# Version 0.3.1 (Updated 1/13/2022)
# Made by Devons Mo

# Variables
valid_image_types = (".png", ".jpg", ".jpeg", ".tif", ".tiff")
output_folder_name = "/Output_Calibration/"
settings_file_name = "settings.txt"

# Tries to import the required modules
# and reports an error if the program is unable to open up the required modules
try:
    from PIL import Image, ImageFilter
    import numpy
    import tkinter
    from tkinter import filedialog
    from os import path, mkdir, walk
    from math import floor
    import csv
except ImportError:
    print("You may be missing a required library! "
          "This program requires Pillow, NumPy, and Tkinter. Make sure to have these modules installed!")

# Import is successful
else:
    # Opens up tkinter, then immediately hides the main tkinter window
    root = tkinter.Tk()
    root.withdraw()

    print("Three negative control images are required for calibration.")

    file_path = []
    while len(file_path) < 3:
        if len(file_path) == 0:
            print("Please select the first:")
        elif len(file_path) == 1:
            print("Please select the second:")
        else:
            print("Please select the third:")

        # Uses tkinter to browse for a file
        selected_image_path = filedialog.askopenfilename()
        if selected_image_path:
            file_path.append(selected_image_path)

    response = []
    response_valid = False
    while not response_valid:
        response.append(input("\nThe image will be compressed to increase speed of analysis.\n"
                              "How much would you like to compress the image?\n"
                              "Smaller number is more compressed.\n"
                              "Average of width and height of compressed image = response\n"
                              "(Default: 512)\n"))
        response.append(input("Which color channel would you like to use?\n"
                              "If your image is grayscale, any option is valid.\n"
                              "Red = 0, Green = 1, Blue = 2\n"
                              "(Default: 1)\n"))
        response.append(input("To help remove granularity of the image, a mild blur will be applied.\n"
                              "What should be the blur radius?\n"
                              "Higher number is more blurred.\n"
                              "Consider turning down this number if the output shows lines that are too thick. "
                              "(i.e. more than 1/2 of a cell's width)\n"
                              "(Default: 5)\n"))
        response.append(input("Often, images will contain brighter and dimmer areas.\n"
                              "To help normalize this deviation, the image will split into "
                              "sections during analysis and analyzed separately.\n"
                              "Into how many sections should the image be split during analysis?\n"
                              "Total number of sections = response^2\n"
                              "(Default: 4)\n"))
        response.append(input("When analyzing each section, pixels will be sampled to determine "
                              "the average brightness of that section.\n"
                              "How many pixels should be sampled?\n"
                              "Total number of pixels sampled = response^2\n"
                              "(Default: 8)\n"))
        response.append(input("In order to reduce the effect of noise on the measurement, a filter will be applied.\n"
                              "What should the filter be?\n"
                              "The response is taken as a percentage (i.e. 0.1 = 10%)\n"
                              "Consider lowering this number if the output is removing too many cell borders. "
                              "Alternately, if you are noticing too much noise remaining, "
                              "consider increasing this number."
                              "(Default: 0.1)\n"))
        response.append(input("During IJOQ analysis, lines will be traced throughout the image.\n"
                              "How many lines should be drawn?\n"
                              "Higher number samples more of the image (beneficial if magnification is low), "
                              "but increases the computational time.\n"
                              "Total number of lines = response x 2\n"
                              "(Default: 10)\n"))

        try:
            compressed_image_size = int(response[0])
            channel = int(response[1])
            blur_radius = int(response[2])
            section_size = int(response[3])
            pixels_sampled = int(response[4])
            noise_cutoff = float(response[5])
            lines = int(response[6])
        except ValueError or TypeError:
            print("Could not interpret response. Please include only numbers.")
        else:
            response_valid = True

    print("\nResponses recorded. Starting calibration...")
    print("This will take a while. Please be patient...\n")

    # Determine save location
    save_location = "/".join(file_path[0].split("/")[:-1]) + output_folder_name

    # If an "Output" folder doesn't exist, create one
    if not path.isdir(save_location):
        mkdir(save_location)

    print("Determining ideal normalization threshold value...")

    # Run the following code for each file that was selected
    threshold_list = []
    stop = False
    for file in file_path:

        # Checks to make sure the file is a valid image file. If invalid, stop the program
        if not file.lower().endswith(valid_image_types):
            print("This program only supports PNG, JPG, and TIF files. "
                  "If you believe this program should support the file you just selected, please reach out.")
            stop = True

            break

        else:
            # If valid file, open up the file and compress image to
            # so the average of the height and width is equal to the compressed image size (default: 512)
            image = Image.open(file)
            width, height = image.size
            compression_amount = (compressed_image_size / 2) * (width + height) / (width * height)
            image = image.resize((round(compression_amount * width), round(compression_amount * height)))
            width, height = image.size

            # Determine the image name
            image_name = ".".join(file.split("/")[-1].split(".")[:-1])

            # Take the RGB values from all the pixels in the image as an array
            image_array = numpy.array(image.convert("RGB"))

            # Extract channel
            for x in range(width):
                for y in range(height):
                    image_array[y][x] = [image_array[y][x][channel]] * 3

            # Apply blur
            image = Image.fromarray(image_array.astype("uint8"))
            blurred_image = image.filter(ImageFilter.GaussianBlur(radius=blur_radius))
            blurred_image.save(save_location + image_name + "~1.png")
            image_array = numpy.array(blurred_image.convert("HSV"))

            # Split the picture into sections (default: 4 x 4)
            section_width = width / section_size
            section_height = height / section_size

            white_pixel_counter = 0
            for section_x in range(section_size):
                for section_y in range(section_size):
                    # Take a histogram of the current section
                    histogram = [0] * 256
                    for x in range(round(section_x * section_width), round((section_x + 1) * section_width)):
                        for y in range(round(section_y * section_height), round((section_y + 1) * section_height)):
                            histogram[image_array[y][x][2]] += 1

                    # Use Otsu's Method to determine threshold for current section
                    maximum_variance_threshold = 0
                    maximum_variance = 0
                    # Try different thresholds until a maximum variance is found
                    for i in range(256):
                        prob_zero = sum(histogram[:i])
                        prob_one = sum(histogram[i:])

                        if prob_zero > 0 and prob_one > 0:  # Must have at least 1 pixel in both classes
                            # Calculate mean zero and mean one
                            mean_zero = 0
                            mean_one = 0
                            for j in range(256):
                                if j < i:
                                    mean_zero += j * histogram[j]
                                else:
                                    mean_one += j * histogram[j]
                            mean_zero /= prob_zero
                            mean_one /= prob_one

                            # Calculate variance
                            variance = prob_zero * prob_one * ((mean_zero - mean_one)**2)

                            if variance >= maximum_variance:
                                maximum_variance_threshold = i
                                maximum_variance = variance

                    if maximum_variance == 0:
                        print("This image cannot be thresholded! Consider using an image with higher contrast")
                        stop = True

                        break

                    # Use the determined threshold to set current section to black and white
                    for x in range(round(section_x * section_width), round((section_x + 1) * section_width)):
                        for y in range(round(section_y * section_height), round((section_y + 1) * section_height)):

                            if image_array[y][x][2] > maximum_variance_threshold:
                                white_pixel_counter += 1

            # Determine normalization threshold
            white_percent = white_pixel_counter / (width * height)

            threshold = numpy.ceil((1-white_percent) * (pixels_sampled**2))
            threshold_list.append(threshold)

    if not stop:
        average_threshold = round(sum(threshold_list) / 3)
        ideal_percent = 1 - (average_threshold / (pixels_sampled**2))

        print("Preparing output images...")

        for file in file_path:
            # If valid file, open up the file and compress image to
            # so the average of the height and width is equal to the compressed image size (default: 512)
            image = Image.open(file)
            width, height = image.size
            compression_amount = (compressed_image_size / 2) * (width + height) / (width * height)
            image = image.resize((round(compression_amount * width), round(compression_amount * height)))
            width, height = image.size

            # Determine the image name
            image_name = ".".join(file.split("/")[-1].split(".")[:-1])

            # Take the RGB values from all the pixels in the image as an array
            image_array = numpy.array(image.convert("RGB"))

            # Extract channel
            for x in range(width):
                for y in range(height):
                    image_array[y][x] = [image_array[y][x][channel]] * 3

            # Apply blur
            image = Image.fromarray(image_array.astype("uint8"))
            blurred_image = image.filter(ImageFilter.GaussianBlur(radius=blur_radius))
            blurred_image.save(save_location + image_name + "~1.png")
            image_array = numpy.array(blurred_image.convert("HSV"))

            # Split the picture into sections (default: 4 x 4)
            section_width = width / section_size
            section_height = height / section_size
            normalization_cutoff_array = [[0] * section_size for i in range(section_size)]

            # For each section, sample pixels (default: 8 x 8),
            # then find the normalization cutoff value (default: 53rd pixel)
            for section_x in range(section_size):
                for section_y in range(section_size):

                    sampled_values = []
                    for x in range(pixels_sampled):
                        for y in range(pixels_sampled):
                            pixel_x = round(section_width * (section_x + ((x + 0.5) / pixels_sampled)))
                            pixel_y = round(section_height * (section_y + ((y + 0.5) / pixels_sampled)))

                            sampled_values.append(image_array[pixel_y][pixel_x][2])

                    sampled_values.sort()
                    normalization_cutoff_array[section_x][section_y] = sampled_values[average_threshold - 1]

            # Parse through the image array and remove all background pixel values (i.e. less than the cutoff point)
            # Then, calculate noise
            histogram = [0] * 256
            for y in range(height):
                for x in range(width):

                    # Calculate a pixel's upper left section, as well as its relative position to the next section
                    x_percent = round(((x - section_width / 2) % section_width) / section_width, 2)
                    y_percent = round(((y - section_height / 2) % section_height) / section_height, 2)
                    left_section = floor((x / section_width) - 0.5)
                    top_section = floor((y / section_height) - 0.5)

                    # If pixel is not near a border, find the normalization cutoff values of the 4 closest sections
                    if 0 <= left_section <= 2 and 0 <= top_section <= 2:
                        top_left_cutoff = normalization_cutoff_array[left_section][top_section]
                        top_right_cutoff = normalization_cutoff_array[left_section + 1][top_section]
                        bottom_left_cutoff = normalization_cutoff_array[left_section][top_section + 1]
                        bottom_right_cutoff = normalization_cutoff_array[left_section + 1][top_section + 1]
                    # If pixel is less than half a grid away from the border, copy the normalization cutoff value
                    else:
                        top_left_value = (left_section, top_section)
                        top_right_value = (left_section + 1, top_section)
                        bottom_left_value = (left_section, top_section + 1)
                        bottom_right_value = (left_section + 1, top_section + 1)

                        # Pixel is on left border
                        if left_section < 0:
                            top_left_value = top_right_value
                            bottom_left_value = bottom_right_value
                        # Pixel is on right border
                        elif left_section >= section_size - 1:
                            top_right_value = top_left_value
                            bottom_right_value = bottom_left_value

                        # Pixel is on top border
                        if top_section < 0:
                            top_left_value = bottom_left_value
                            top_right_value = bottom_right_value
                        # Pixel is on bottom border
                        elif top_section >= section_size - 1:
                            bottom_left_value = top_left_value
                            bottom_right_value = top_right_value

                        top_left_cutoff = \
                            normalization_cutoff_array[top_left_value[0]][top_left_value[1]]
                        top_right_cutoff = \
                            normalization_cutoff_array[top_right_value[0]][top_right_value[1]]
                        bottom_left_cutoff = \
                            normalization_cutoff_array[bottom_left_value[0]][bottom_left_value[1]]
                        bottom_right_cutoff = \
                            normalization_cutoff_array[bottom_right_value[0]][bottom_right_value[1]]

                    # Calculate the weighted average of the normalization cutoff value
                    cutoff_top = (1 - x_percent) * top_left_cutoff + x_percent * top_right_cutoff
                    cutoff_bottom = (1 - x_percent) * bottom_left_cutoff + x_percent * bottom_right_cutoff

                    cutoff_final = round((1 - y_percent) * cutoff_top + y_percent * cutoff_bottom)

                    # Remove pixel if lower than cutoff
                    pixel_brightness = image_array[y][x][2]

                    if pixel_brightness > max(cutoff_final * (1 + noise_cutoff), 20):
                        image_array[y][x][2] = 255
                    else:
                        image_array[y][x][2] = 0

            # Save normalized image
            normalized_image = Image.fromarray(image_array.astype("uint8"), "HSV").convert("RGB")
            normalized_image.save(save_location + image_name + "~2.png")

        print("\nOutputs saved to: " + save_location + "\n")

        print("Ideal normalization threshold value: ", average_threshold)

        response = input("\nWould you like to save these settings? (Yes/No)\n")

        while True:
            if response.lower() == "yes":
                with open(save_location + settings_file_name, mode="w") as settings_file:
                    settings_file.write("compressed_image_size = " + str(compressed_image_size) + "\n")
                    settings_file.write("channel = " + str(channel) + "\n")
                    settings_file.write("blur_radius = " + str(blur_radius) + "\n")
                    settings_file.write("section_size = " + str(section_size) + "\n")
                    settings_file.write("pixels_sampled = " + str(pixels_sampled) + "\n")
                    settings_file.write("normalization_cutoff = " + str(average_threshold) + "\n")
                    settings_file.write("noise_cutoff = " + str(noise_cutoff) + "\n")
                    settings_file.write("lines = " + str(lines))

                print("Settings saved to: ", save_location + settings_file_name)

                break
            elif response.lower() == "no":
                print("Settings will not be saved.")
                break
            else:
                response = input("Could not interpret response. Would you like to save these settings? (Yes/No)")


# Keep program open until user gives an input
input("Press enter to finish")
