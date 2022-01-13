# Version 0.14.1 (Updated 1/13/2022)
# Made by Devons Mo

# Variables
valid_image_types = (".png", ".jpg", ".jpeg", ".tif", ".tiff")
output_folder_name = "/Output_IJOQ/"
data_file_name = "IJOQ.csv"
compressed_image_size = 512  # The average of the height and width of the image will be compressed to this number
channel = 1  # This is the channel of interest. Red = 0, Green = 1, Blue = 2
blur_radius = 5
section_size = 4  # The image will be divided both horizontally and vertically by this number into sections
pixels_sampled = 8  # Each section will sample a total pixel count of this value, squared
normalization_cutoff = 35  # This pixel will be taken as the normalization cutoff value of the section
noise_cutoff = 0.1
lines = 10  # This determines the number of lines drawn during the IJOQ measurement

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
    input()

# Import is successful
else:
    # Opens up tkinter, then immediately hides the main tkinter window
    root = tkinter.Tk()
    root.withdraw()

    print("Please select an image to analyze.\nIf you want to analyze a folder of images, cancel the file selection.")

    # Uses tkinter to browse for a file
    file_path = [filedialog.askopenfilename()]

    # If the file selection is canceled, open up a folder select
    folder_path = ""
    multiple_files = False
    no_input = False
    if file_path == ['']:
        multiple_files = True

        print("The folder selection has been prompted. Please select the folder of images that you want to analyze."
              "\nNote: Any images within a folder containing \"Output\" will be ignored.")

        # Uses tkinter to browse for a folder
        folder_path = filedialog.askdirectory()

        # If no folder was selected, close the program
        if folder_path == "":
            print("No folder was selected. The program will stop.")
            no_input = True
        # If a folder was selected
        else:

            # Walks through everything within the folder (including the folders within the folder)
            # and adds each file that it found into the folder_path list,
            # as long as the file isn't within a folder named "Output"
            file_path = []
            file_list = []
            for (dirpath, dirnames, filenames) in walk(folder_path):
                if "Output" not in dirpath:
                    for file in filenames:
                        file_path.append(dirpath + "/" + file)
                        file_list.append(file)

    # If an input was given, run the program. Else, stop the program
    if not no_input:

        # Import settings
        print("\nPlease select the settings that have been calibrated to your cell type and magnification.\n"
              "Closing this window will prompt the program to use default settings.")

        setting_path = filedialog.askopenfilename()

        if setting_path != "":
            with open(setting_path, mode="r") as settings:
                setting_list = settings.readlines()

                for setting in setting_list:
                    if "compressed_image_size" in setting:
                        compressed_image_size = int(setting[len("compressed_image_size = "):])
                    elif "channel" in setting:
                        channel = int(setting[len("channel = "):])
                    elif "blur_radius" in setting:
                        blur_radius = int(setting[len("blur_radius = "):])
                    elif "section_size" in setting:
                        section_size = int(setting[len("section_size = "):])
                    elif "pixels_sampled" in setting:
                        pixels_sampled = int(setting[len("pixels_sampled = "):])
                    elif "normalization_cutoff" in setting:
                        normalization_cutoff = int(setting[len("normalization_cutoff = "):])
                    elif "noise_cutoff" in setting:
                        noise_cutoff = float(setting[len("noise_cutoff = "):])
                    elif "lines" in setting:
                        lines = int(setting[len("lines = "):])

        print("It'll take just a moment...\n")

        # Determine the save location
        if multiple_files:
            # If multiple files are selected, save to a folder named "Output" within the folder
            save_location = folder_path + output_folder_name

            # If an "Output" folder doesn't exist, create one
            if not path.isdir(save_location):
                mkdir(save_location)
        else:
            # If a single file was selected, save to the same folder as the image
            save_location = "/".join(file_path[0].split("/")[:-1]) + "/"

        # Run the following code for each file that was selected
        IJOQ_list = []
        for file in file_path:

            # Checks to make sure the file is a valid image file
            if not file.lower().endswith(valid_image_types):

                # If only 1 file was selected and the file was invalid, give an explanation and stop the program
                if not multiple_files:
                    print("This program only supports PNG, JPG, and TIF files. "
                          "If you believe this program should support the file you just selected, please reach out.")

                # If more than 1 file was selected and the current file was invalid, make a note and continue program
                else:
                    print("This file was ignored due to having an invalid file type: " + file + "\n")
                    IJOQ_list.append("N/A")

            else:
                # If valid file, open up the file and compress image to
                # so the average of the height and width is equal to the compressed image size
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
                print("Blurred image saved to: " + save_location + image_name + "~1.png")

                image_array = numpy.array(blurred_image.convert("HSV"))

                # Split the picture into sections
                section_width = width / section_size
                section_height = height / section_size
                normalization_cutoff_array = [[0] * section_size for i in range(section_size)]

                # For each section, sample pixels,
                # then find the normalization cutoff value
                for section_x in range(section_size):
                    for section_y in range(section_size):

                        sampled_values = []
                        for x in range(pixels_sampled):
                            for y in range(pixels_sampled):
                                pixel_x = round(section_width * (section_x + ((x + 0.5) / pixels_sampled)))
                                pixel_y = round(section_height * (section_y + ((y + 0.5) / pixels_sampled)))

                                sampled_values.append(image_array[pixel_y][pixel_x][2])

                        sampled_values.sort()
                        normalization_cutoff_array[section_x][section_y] = sampled_values[normalization_cutoff - 1]

                # Parse through the image array and remove all background pixel values (i.e. less than the cutoff point)
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
                print("Normalized image saved to: " + save_location + image_name + "~2.png")

                # Draw horizontal lines
                cell_border_frequency = 0
                for y in range(lines):
                    pixel_y = round((y + 0.5) * height / lines)

                    previous_pixel = image_array[pixel_y][0][2]
                    for x in range(1, width):
                        current_pixel = image_array[pixel_y][x][2]
                        # If the line detects a color change (i.e. black to white or white to black)
                        if not previous_pixel == current_pixel:
                            cell_border_frequency += 0.5 / width

                        # Set current pixel as the previous pixel before moving to the next pixel
                        previous_pixel = current_pixel

                # Repeat the same steps vertical lines
                for x in range(lines):
                    pixel_x = round((x + 0.5) * width / lines)

                    previous_pixel = image_array[0][pixel_x][2]
                    for y in range(1, height):
                        current_pixel = image_array[y][pixel_x][2]
                        if not previous_pixel == current_pixel:
                            cell_border_frequency += 0.5 / height

                        # Set current pixel as the previous pixel before moving to the next pixel
                        previous_pixel = current_pixel

                # Take average of all lines
                cell_border_frequency = cell_border_frequency / (2 * lines)
                print(str(round(cell_border_frequency, 5)) + " cell borders are expected to be crossed per pixel.\n")
                IJOQ_list.append(cell_border_frequency)

        # If multiple files were selected, create a CSV file with the data
        if multiple_files:
            with open(save_location + data_file_name, mode="w", newline="") as data_file:
                data_writer = csv.writer(data_file)
                data_writer.writerow(["File name", "IJOQ"])
                for i in range(len(file_path)):
                    data_writer.writerow([file_list[i], IJOQ_list[i]])

            print("\nData saved to: " + save_location + data_file_name)

    # Keep program open until user gives an input
    input("Press enter to finish")
