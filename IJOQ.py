# Devons Mo and Shane Nicole Homez 1/11/2023
# Global variables
valid_image_types = (".png", ".jpg", ".jpeg", ".tif", ".tiff")
current_version = "v1.2.8"

# Tries to import the required modules
# and reports an error if the program is unable to open up the required modules
try:
    import csv
    from math import floor
    import numpy
    from os import path, mkdir, walk
    from PIL import Image, ImageFilter, ImageTk
    from threading import Thread
    import tkinter
    from tkinter import filedialog, ttk, messagebox
except ImportError:
    print("You may be missing a required library! "
          "Be sure to run the IJOQ Setup before running this program!")
    input()

# Import is successful
else:

    class CalNoiseCalculationThread(Thread):
        def __init__(self):
            Thread.__init__(self)
            self.stop = False
            self.current_file = 0
            self.update_order = []

        def run(self):
            global cal_blurred_images, cal_brightness_maps, cal_processed_files

            # Save current image number
            self.current_file = cal_current_viewed_picture
            blur_number = cal_confirmed_blur_radius

            # Determine update order (current image first, then nearby images, etc.)
            above_images_count = len(cal_processed_files) - self.current_file - 1
            below_images_count = self.current_file

            for i in range(1, max(above_images_count, below_images_count) + 1):
                if i <= below_images_count:
                    self.update_order.append(self.current_file - i)
                if i <= above_images_count:
                    self.update_order.append(self.current_file + i)

            # Calculate current image first
            blurred_image = cal_blurred_images[self.current_file][blur_number]
            brightness_map = cal_brightness_maps[self.current_file][blur_number]
            width, height = blurred_image.size

            image_array = numpy.array(blurred_image.convert("HSV"))
            normalized_image_array = normalize_image(
                image_array,
                brightness_map,
                width, height,
                cal_confirmed_noise_filter)
            normalized_image = Image.fromarray(normalized_image_array.astype("uint8"), "HSV").convert("RGB")
            cal_processed_files[self.current_file] = normalized_image

            draw_results_image(self.current_file, "cal")

            # Re-enable slider and spinbox
            cal_results_settings_blur_slider["state"] = "normal"
            cal_results_settings_blur_spinbox["state"] = "normal"
            cal_results_settings_noise_slider["state"] = "normal"
            cal_results_settings_noise_spinbox["state"] = "normal"

            # Calculate remaining images in the background
            for i in self.update_order:
                if self.stop:
                    break
                elif i is not self.current_file:
                    blur_number = cal_confirmed_blur_radius
                    blurred_image = cal_blurred_images[i][blur_number]
                    brightness_map = cal_brightness_maps[i][blur_number]
                    width, height = blurred_image.size

                    image_array = numpy.array(blurred_image.convert("HSV"))
                    normalized_image_array = normalize_image(
                        image_array,
                        brightness_map,
                        width, height,
                        cal_confirmed_noise_filter)
                    normalized_image = Image.fromarray(normalized_image_array.astype("uint8"), "HSV").convert("RGB")
                    cal_processed_files[i] = normalized_image

                    # Update image if current image is the currently-viewed image (if user changes picture mid-thread)
                    if i == cal_current_viewed_picture:
                        draw_results_image(i, "cal")

    # Update current tab when a tab change is detected
    def update_current_tab(tab):
        # If calibration
        if tab == "cal":
            global cal_current_tab

            # If there are unconfirmed files in the input, send message that calibration cannot be performed
            if cal_current_tab == 0 and cal_input_files != cal_confirmed_files:
                cal_settings_confirm_button["state"] = "disabled"
                messagebox.showinfo(
                    "Unconfirmed file selection",
                    "Unconfirmed file selection detected!\n\nYou will not be able "
                    "to run a calibration unless the file selection is confirmed.")

            cal_current_tab = calibration_side_tabs.index("current")
        # If analysis
        elif tab == "anl":
            global anl_current_tab

            # If there are unconfirmed files in the input, send message that analysis cannot be performed
            if anl_current_tab == 0 and anl_input_files != anl_confirmed_files:
                anl_settings_confirm_button["state"] = "disabled"
                messagebox.showinfo(
                    "Unconfirmed file selection",
                    "Unconfirmed file selection detected!\n\nYou will not be able "
                    "to run an analysis unless the file selection is confirmed.")

            anl_current_tab = analysis_side_tabs.index("current")

    # Go to previous page
    def go_to_previous_page(tab):
        if tab == "cal":
            global cal_current_tab

            calibration_side_tabs.select(cal_current_tab - 1)
        elif tab == "anl":
            global anl_current_tab

            analysis_side_tabs.select(anl_current_tab - 1)

    # Prompts a file selection and adds the file to the listbox
    # and the internal calibration or analysis file selection list
    def add_file(tab):
        file_path = filedialog.askopenfilename()
        if file_path:
            if file_path.lower().endswith(valid_image_types):
                if "Output" not in file_path:
                    # Check calibration file count
                    if len(cal_input_files) < 99 and tab == "cal":
                        file_name = file_path.split("/")[-1]
                        cal_input_files.append(file_path)
                        cal_file_list_box.insert(tkinter.END, file_name)
                    # Check analysis file count
                    elif len(anl_input_files) < 99 and tab == "anl":
                        file_name = file_path.split("/")[-1]
                        anl_input_files.append(file_path)
                        anl_file_list_box.insert(tkinter.END, file_name)
                    else:
                        messagebox.showinfo(
                            "File limit reached",
                            "You have reached the image file limit!\n\n"
                            "The program accepts a maximum of 99 images.")
                else:
                    messagebox.showinfo(
                        "Output file detected",
                        "A possible output file detected!\n\nThis program automatically ignores any "
                        "images saved in a folder containing \"Output\" in its name.")
            else:
                messagebox.showinfo(
                    "Incompatible file type selected",
                    "Incompatible file type selected!\n\nThis program can only accept PNG, JPG, and TIF files.")

        # Enable the confirm files button if there are at least 3 selections for calibration
        # and at least 1 selection for analysis
        if len(cal_input_files) >= 3 and tab == "cal":
            cal_file_select_button["state"] = "normal"
        elif len(anl_input_files) >= 1 and tab == "anl":
            anl_file_select_button["state"] = "normal"

    # Prompts a folder selection and adds all files to the listbox
    # and the internal calibration or analysis file selection list
    def add_folder(tab):
        folder_path = filedialog.askdirectory()
        if "Output" in folder_path:
            messagebox.showinfo(
                "Output folder selected",
                "A possible output folder was selected!\n\nThis program automatically ignores any "
                "images saved in a folder containing \"Output\" in its name.")
        else:
            file_limit_reached = False
            for (dirpath, dirnames, filenames) in walk(folder_path):
                if "Output" not in dirpath:
                    for file in filenames:
                        if file.lower().endswith(valid_image_types):
                            # Check calibration file count
                            if len(cal_input_files) < 99 and tab == "cal":
                                cal_input_files.append(dirpath + "/" + file)
                                cal_file_list_box.insert(tkinter.END, file)
                            # Check analysis file count
                            elif len(anl_input_files) < 99 and tab == "anl":
                                anl_input_files.append(dirpath + "/" + file)
                                anl_file_list_box.insert(tkinter.END, file)
                            else:
                                messagebox.showinfo(
                                    "File limit reached",
                                    "You have reached the image file limit!\n\n"
                                    "The program accepts a maximum of 99 images.")
                                file_limit_reached = True
                                break
                        if file_limit_reached:
                            break
                if file_limit_reached:
                    break

        # Enable the confirm files button if there are at least 3 selections for calibration
        # and at least 1 selection for analysis
        if len(cal_input_files) >= 3 and tab == "cal":
            cal_file_select_button["state"] = "normal"
        elif len(anl_input_files) >= 1 and tab == "anl":
            anl_file_select_button["state"] = "normal"

    # Retrieves highlighted selection from the listbox and removes from the internal file selection list
    # as well as the listbox
    def del_file(tab):
        if tab == "cal":
            # Delete from the largest index first to maintain the index order
            for i in sorted(cal_file_list_box.curselection(), reverse=True):
                del cal_input_files[i]
                cal_file_list_box.delete(i)

            # Disable the confirm files button if there are less than 3 selections
            if len(cal_input_files) < 3:
                cal_file_select_button["state"] = "disabled"
        elif tab == "anl":
            # Delete from the largest index first to maintain the index order
            for i in sorted(anl_file_list_box.curselection(), reverse=True):
                del anl_input_files[i]
                anl_file_list_box.delete(i)

            # Disable the confirm files button if there are less than 1 selection
            if len(anl_input_files) < 1:
                anl_file_select_button["state"] = "disabled"

    def clear_file(tab):
        if tab == "cal":
            cal_input_files.clear()
            cal_file_list_box.delete(0, tkinter.END)

            # Disable the confirm files button
            cal_file_select_button["state"] = "disabled"
        elif tab == "anl":
            anl_input_files.clear()
            anl_file_list_box.delete(0, tkinter.END)

            # Disable the confirm files button
            anl_file_select_button["state"] = "disabled"

    def confirm_files(tab):
        if tab == "cal":
            global cal_confirmed_files, cal_confirmed_file_names

            # Enable next page, then move to next page
            calibration_side_tabs.tab(1, state="normal")
            calibration_side_tabs.select(1)

            # Copy input files into confirmed files
            cal_confirmed_files = cal_input_files.copy()
            cal_confirmed_file_names = cal_file_list_box.get(0, cal_file_list_box.size() - 1)

            # Enable the button to start calibration
            cal_settings_confirm_button["state"] = "normal"
        elif tab == "anl":
            global anl_confirmed_files, anl_confirmed_file_names

            # Enable next page, then move to next page
            analysis_side_tabs.tab(1, state="normal")
            analysis_side_tabs.select(1)

            # Copy input files into confirmed files
            anl_confirmed_files = anl_input_files.copy()
            anl_confirmed_file_names = anl_file_list_box.get(0, anl_file_list_box.size() - 1)

            # Enable the button to start analysis if settings has already been uploaded
            if anl_has_uploaded_settings:
                anl_settings_confirm_button["state"] = "normal"

    # Validates input for spinboxes (for ints)
    def validate_input_int(new_input):
        return new_input.isdecimal() or new_input == ""

    # Validates input for spinboxes (for floats)
    def validate_input_float(new_input):
        has_period = False
        is_first_char = True
        for char in new_input:
            if not char.isdecimal():
                # If character is a period (and it is the only period), then it is acceptable
                if char == "." and not has_period:
                    has_period = True
                # If character is a minus, and it is the first character in the input, then it is acceptable
                elif char == "-" and is_first_char:
                    pass
                else:
                    return False

            is_first_char = False
        return True

    # Prevents invalid inputs
    def sanitize_input(variable, is_even, var_type, var_min, var_max):
        variable_value = variable.get()
        if var_type == "int":
            # Remove leading zeroes
            sanitized_input = ""
            has_number = False
            for char in variable_value:
                if not has_number:
                    if char != "0":
                        has_number = True
                        sanitized_input += char
                else:
                    sanitized_input += char

            # Exception is if 0 is the only digit
            if sanitized_input == "":
                sanitized_input = "0"

            # If is_even is true, then round up if number is odd
            if is_even and int(sanitized_input) % 2 != 0:
                sanitized_input = str(int(sanitized_input) + 1)

            # Ensure input is within bounds
            if int(sanitized_input) < var_min:
                sanitized_input = str(var_min)
            elif int(sanitized_input) > var_max:
                sanitized_input = str(var_max)

            variable.set(sanitized_input)
        elif var_type == "float":
            # Remove leading zeroes
            sanitized_input = ""
            has_period = False
            for char in variable_value:
                if not has_period:
                    if char == ".":
                        has_period = True
                        sanitized_input += "0."
                    elif char != "0":
                        sanitized_input += char
                else:
                    sanitized_input += char

            # Exception is if 0 or - is the only digit
            if sanitized_input == "" or sanitized_input == "-":
                sanitized_input = "0"

            # Ensure input is within bounds
            if float(variable_value) < var_min:
                sanitized_input = str(var_min)
            elif float(variable_value) > var_max:
                sanitized_input = str(var_max)

            # Round input to nearest 0.005
            sanitized_input = str(round(round(float(sanitized_input) / 0.005) * 0.005, 3))

            variable.set(sanitized_input)

    def cal_go_to_calibration():
        global cal_confirmed_image_compression, cal_confirmed_channel, cal_confirmed_blur_radius, \
            cal_confirmed_section_number, cal_confirmed_pixel_number, cal_confirmed_noise_filter, \
            cal_confirmed_line_number, cal_blurred_images, cal_normalization_thresholds, \
            cal_brightness_maps, cal_processed_files

        # Check for existing noise filter calculation threads. If previous threads exist, prompt them to stop
        if cal_noise_filter_threads:
            for thread in cal_noise_filter_threads:
                thread.stop = True

            # Wait for threads to stop before continuing
            for thread in cal_noise_filter_threads:
                thread.join()

        # Determine settings
        # If using basic settings
        if cal_settings_options_tabs.index("current") == 0:
            average_cell_count = (int(cal_cell_number_x.get()) + int(cal_cell_number_y.get())) / 2
            if average_cell_count > 50:
                cal_confirmed_image_compression = 1024
                cal_confirmed_section_number = 6
            else:
                cal_confirmed_image_compression = 512
                cal_confirmed_section_number = 4

            if cal_channel_selection.get() == "Red":
                cal_confirmed_channel = 0
            elif cal_channel_selection.get() == "Green":
                cal_confirmed_channel = 1
            elif cal_channel_selection.get() == "Blue":
                cal_confirmed_channel = 2
            elif cal_channel_selection.get() == "White":
                cal_confirmed_channel = 1

            cal_confirmed_blur_radius = -average_cell_count
            cal_confirmed_pixel_number = 8
            cal_confirmed_noise_filter = -1
            cal_confirmed_line_number = max(10, int(round(average_cell_count, -1)))
        else:  # If using advanced settings
            cal_confirmed_image_compression = int(cal_image_compression.get())
            if cal_channel_selection.get() == "Red":
                cal_confirmed_channel = 0
            elif cal_channel_selection.get() == "Green":
                cal_confirmed_channel = 1
            elif cal_channel_selection.get() == "Blue":
                cal_confirmed_channel = 2
            elif cal_channel_selection.get() == "White":
                cal_confirmed_channel = 1
            cal_confirmed_blur_radius = int(cal_blur_radius.get())
            cal_confirmed_section_number = int(cal_section_number.get())
            cal_confirmed_pixel_number = int(cal_pixel_number.get())
            cal_confirmed_noise_filter = float(cal_noise_filter.get())
            cal_confirmed_line_number = int(cal_line_number.get())

        # Set progress bar to 0, delete text in textbox, and clear results
        cal_blurred_images = []
        cal_normalization_thresholds = []
        cal_brightness_maps = []
        cal_processed_files = []
        progress_bar_maximum = (len(cal_confirmed_files) * (13 + (12 * (cal_confirmed_section_number**2)))) + 6
        cal_calibration_progress_bar.config(maximum=progress_bar_maximum)
        cal_calibration_progress_bar["value"] = 0
        cal_calibration_textbox.delete(1.0, tkinter.END)

        # Move to the calibration screen
        calibration_side_tabs.tab(2, state="normal")
        calibration_side_tabs.select(2)

        # Disable other tabs
        calibration_side_tabs.tab(0, state="disabled")
        calibration_side_tabs.tab(1, state="disabled")
        calibration_side_tabs.tab(3, state="disabled")
        cal_calibration_previous_button["state"] = "disabled"
        cal_calibration_confirm_button["state"] = "disabled"

        calibration_thread = Thread(target=cal_run_calibration, daemon=True)
        calibration_thread.start()

    # Calculate threshold value for a given pixel
    def calculate_threshold(x, y, section_count, threshold_array, section_width, section_height):
        # Calculate a pixel's upper left section, as well as its relative position to the next section
        x_percent = round(((x - section_width / 2) % section_width) / section_width, 2)
        y_percent = round(((y - section_height / 2) % section_height) / section_height, 2)
        left_section = floor((x / section_width) - 0.5)
        top_section = floor((y / section_height) - 0.5)

        # If pixel is not near a border, find the normalization thresholds of the 4 closest sections
        if 0 <= left_section <= (section_count - 2) and 0 <= top_section <= (section_count - 2):
            top_left_threshold = threshold_array[left_section][top_section]
            top_right_threshold = threshold_array[left_section + 1][top_section]
            bottom_left_threshold = threshold_array[left_section][top_section + 1]
            bottom_right_threshold = threshold_array[left_section + 1][top_section + 1]
        # If pixel is less than half a grid away from the border, copy teh normalization threshold value
        else:
            top_left_value = (left_section, top_section)
            top_right_value = (left_section + 1, top_section)
            bottom_left_value = (left_section, top_section + 1)
            bottom_right_value = (left_section + 1, top_section + 1)

            # Pixel is on the left border
            if left_section < 0:
                top_left_value = top_right_value
                bottom_left_value = bottom_right_value
            # Pixel is on the right border
            elif left_section >= section_count - 1:
                top_right_value = top_left_value
                bottom_right_value = bottom_left_value

            # Pixel is on top border
            if top_section < 0:
                top_left_value = bottom_left_value
                top_right_value = bottom_right_value
            # Pixel is on bottom border
            elif top_section >= section_count - 1:
                bottom_left_value = top_left_value
                bottom_right_value = top_right_value

            top_left_threshold = threshold_array[top_left_value[0]][top_left_value[1]]
            top_right_threshold = threshold_array[top_right_value[0]][top_right_value[1]]
            bottom_left_threshold = threshold_array[bottom_left_value[0]][bottom_left_value[1]]
            bottom_right_threshold = threshold_array[bottom_right_value[0]][bottom_right_value[1]]

        # Calculate the weighted average of the normalization cutoff value
        threshold_top = ((1 - x_percent) * top_left_threshold) + (x_percent * top_right_threshold)
        threshold_bottom = ((1 - x_percent) * bottom_left_threshold) + (x_percent * bottom_right_threshold)

        threshold_final = round(((1 - y_percent) * threshold_top) + (y_percent * threshold_bottom))

        return threshold_final

    # Returns the processed image
    def normalize_image(pixel_array, brightness_map, width, height, noise_threshold):
        for x in range(width):
            for y in range(height):
                pixel_brightness = pixel_array[y][x][2]

                if pixel_brightness > max(brightness_map[y][x] * (1 + noise_threshold), 20):
                    pixel_array[y][x][2] = 255
                else:
                    pixel_array[y][x][2] = 0

        return pixel_array

    # Run calibration
    def cal_run_calibration():
        global cal_confirmed_image_compression, cal_confirmed_channel, cal_confirmed_blur_radius, \
            cal_confirmed_section_number, cal_confirmed_pixel_number, cal_confirmed_noise_filter, \
            cal_brightness_maps, cal_processed_files, cal_confirmed_normal_threshold

        # Run calibration
        cal_calibration_textbox.insert(tkinter.END, "Determining ideal normalization threshold value...")
        cal_calibration_textbox.see(tkinter.END)

        # Run the following code for each file
        brightness_deviation_list = []
        threshold_list = []
        for file_number in range(len(cal_confirmed_files)):
            image_name = cal_confirmed_file_names[file_number]
            try:
                image = Image.open(cal_confirmed_files[file_number])
                width, height = image.size
                compression_amount = (cal_confirmed_image_compression / 2) * (width + height) / (width * height)
                image = image.resize((round(compression_amount * width), round(compression_amount * height)))
                width, height = image.size

                # Take the RGB values from all the pixels in the image as an array
                image_array = numpy.array(image.convert("RGB"))

                # Extract channel
                cal_calibration_textbox.insert(tkinter.END, f"\n\nExtracting channel from {image_name}...")
                cal_calibration_textbox.see(tkinter.END)
                for x in range(width):
                    for y in range(height):
                        image_array[y][x] = [image_array[y][x][cal_confirmed_channel]] * 3

                if cal_confirmed_blur_radius < 0:
                    # Calculate deviation in brightness of neighboring pixels
                    brightness_deviation = []
                    for y in range(1, height):
                        brightness_deviation.append(int(image_array[y][round(width / 2)][2]) -
                                                    int(image_array[y - 1][round(width / 2)][2]))
                    for x in range(1, width):
                        brightness_deviation.append(int(image_array[round(height / 2)][x][2]) -
                                                    int(image_array[round(height / 2)][x - 1][2]))

                    brightness_deviation.sort()
                    IQR = brightness_deviation[round(3 * len(brightness_deviation) / 4)] - \
                        brightness_deviation[round(len(brightness_deviation) / 4)]
                    brightness_deviation_list.append(IQR)

                # Apply blur
                cal_calibration_textbox.insert(tkinter.END, f"\nApplying blur to {image_name}...")
                cal_calibration_textbox.see(tkinter.END)
                image = Image.fromarray(image_array.astype("uint8"))
                blur_radius_values = (0, 1, 2, 3, 4, 5)
                current_blurred_image_list = []
                for blur_radius_value in blur_radius_values:
                    blurred_image = image.filter(ImageFilter.GaussianBlur(radius=blur_radius_value))
                    current_blurred_image_list.append(blurred_image)
                    cal_calibration_progress_bar["value"] += 1
                cal_blurred_images.append(current_blurred_image_list)

                # Calculate threshold value for each individual blurred image
                cal_calibration_textbox.insert(tkinter.END, f"\nCalculating threshold values for {image_name}...")
                cal_calibration_textbox.see(tkinter.END)
                current_threshold_list = []
                for blurred_image in current_blurred_image_list:
                    image_array = numpy.array(blurred_image.convert("HSV"))

                    # Split the picture into sections
                    section_width = width / cal_confirmed_section_number
                    section_height = height / cal_confirmed_section_number

                    white_pixel_counter = 0
                    for section_x in range(cal_confirmed_section_number):
                        for section_y in range(cal_confirmed_section_number):
                            # Take a histogram of the current section
                            histogram = [0] * 256
                            for x in range(round(section_x * section_width),
                                           round((section_x + 1) * section_width)):
                                for y in range(round(section_y * section_height),
                                               round((section_y + 1) * section_height)):
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

                            # Use the determined threshold to set current section to black and white
                            for x in range(round(section_x * section_width),
                                           round((section_x + 1) * section_width)):
                                for y in range(round(section_y * section_height),
                                               round((section_y + 1) * section_height)):
                                    if image_array[y][x][2] > maximum_variance_threshold:
                                        white_pixel_counter += 1

                            # Increment progress bar
                            cal_calibration_progress_bar["value"] += 1

                    # Determine normalization threshold
                    white_percent = white_pixel_counter / (width * height)

                    threshold = numpy.ceil((1 - white_percent) * (cal_confirmed_pixel_number**2))
                    current_threshold_list.append(threshold)

                threshold_list.append(current_threshold_list)

            # File could not be opened
            except FileNotFoundError:
                # Print warning, re-enable file selection and settings, then stop function
                cal_calibration_textbox.insert(
                    tkinter.END, f"\n\nWARNING! Unable to find file for {image_name}!")
                cal_calibration_textbox.see(tkinter.END)

                calibration_side_tabs.tab(0, state="normal")
                calibration_side_tabs.tab(1, state="normal")
                cal_calibration_previous_button["state"] = "normal"

                return

        # Take geometric mean of thresholds
        for i in range(6):
            product = 1
            for j in range(len(threshold_list)):
                product *= threshold_list[j][i]

            average_threshold = round(product**(1/len(threshold_list)))
            cal_normalization_thresholds.append(average_threshold)

            cal_calibration_progress_bar["value"] += 1

        cal_calibration_textbox.insert(tkinter.END, f"\n\nPreparing brightness maps...\n")
        cal_calibration_textbox.see(tkinter.END)
        for i in range(len(cal_confirmed_files)):
            image_name = cal_confirmed_file_names[i]

            cal_calibration_textbox.insert(tkinter.END, f"\nCalculating brightness map for {image_name}...")
            cal_calibration_textbox.see(tkinter.END)
            current_brightness_map_list = []
            for j in range(len(cal_blurred_images[i])):
                width, height = cal_blurred_images[i][j].size
                image_array = numpy.array(cal_blurred_images[i][j].convert("HSV"))

                # Split the picture into sections
                section_width = width / cal_confirmed_section_number
                section_height = height / cal_confirmed_section_number
                normalization_threshold_array = numpy.zeros(
                    (cal_confirmed_section_number, cal_confirmed_section_number))

                # For each section, sample pixels, then find the normalization threshold
                for section_x in range(cal_confirmed_section_number):
                    for section_y in range(cal_confirmed_section_number):

                        sampled_values = []
                        for x in range(cal_confirmed_pixel_number):
                            for y in range(cal_confirmed_pixel_number):
                                pixel_x = round(section_width * (section_x + ((x + 0.5) / cal_confirmed_pixel_number)))
                                pixel_y = round(section_height * (section_y + ((y + 0.5) / cal_confirmed_pixel_number)))

                                sampled_values.append(image_array[pixel_y][pixel_x][2])

                        sampled_values.sort()
                        normalization_threshold_array[section_x][section_y] = \
                            sampled_values[cal_normalization_thresholds[j] - 1]
                        cal_calibration_progress_bar["value"] += 1

                # Parse through the image array and calculate brightness map
                brightness_map = numpy.zeros((height, width))
                for x in range(width):
                    for y in range(height):
                        brightness_map[y][x] = calculate_threshold(
                            x, y,
                            cal_confirmed_section_number,
                            normalization_threshold_array,
                            section_width, section_height)
                current_brightness_map_list.append(brightness_map)
                cal_calibration_progress_bar["value"] += 1

            cal_brightness_maps.append(current_brightness_map_list)

        # Take average of brightness deviations and set as blur radius
        if cal_confirmed_blur_radius < 0:
            average_brightness_deviation = sum(brightness_deviation_list) / len(brightness_deviation_list)
            cal_confirmed_blur_radius = \
                max(min(round(25 * average_brightness_deviation / ((-cal_confirmed_blur_radius) ** 2.5)), 5), 1)

        # Calculate noise filter
        current_blur_number = cal_confirmed_blur_radius
        if cal_confirmed_noise_filter == -1:
            brightness_deviation_list = []
            for i in range(len(cal_confirmed_files)):

                width, height = cal_blurred_images[i][current_blur_number].size
                image_array = numpy.array(cal_blurred_images[i][current_blur_number].convert("HSV"))

                # Calculate difference in brightness between local minima/maxima
                brightness_deviation = []
                local_minimum = -1
                local_maximum = 0
                increasing = True
                for y in range(1, height):
                    if increasing:
                        if image_array[y][round(width / 2)][2] < 0.95 * local_maximum:
                            increasing = False
                            if local_minimum != -1:
                                difference = (local_maximum / local_minimum) - 1
                                brightness_deviation.append(difference)
                            local_minimum = image_array[y][round(width / 2)][2]
                        else:
                            local_maximum = image_array[y][round(width / 2)][2]
                    else:
                        if image_array[y][round(width / 2)][2] > 1.05 * local_minimum:
                            increasing = True
                            difference = (local_maximum / local_minimum) - 1
                            brightness_deviation.append(difference)
                            local_maximum = image_array[y][round(width / 2)][2]
                        else:
                            local_minimum = image_array[y][round(width / 2)][2]

                local_minimum = -1
                local_maximum = 0
                increasing = True
                for x in range(1, width):
                    if increasing:
                        if image_array[round(height / 2)][x][2] < 0.95 * local_maximum:
                            increasing = False
                            if local_minimum != -1:
                                difference = (local_maximum / local_minimum) - 1
                                brightness_deviation.append(difference)
                            local_minimum = image_array[round(height / 2)][x][2]
                        else:
                            local_maximum = image_array[round(height / 2)][x][2]
                    else:
                        if image_array[round(height / 2)][x][2] > 1.05 * local_minimum:
                            increasing = True
                            difference = (local_maximum / local_minimum) - 1
                            brightness_deviation.append(difference)
                            local_maximum = image_array[round(height / 2)][x][2]
                        else:
                            local_minimum = image_array[round(height / 2)][x][2]

                if brightness_deviation:
                    brightness_deviation.sort()
                    median = brightness_deviation[round(len(brightness_deviation) / 2)]
                    brightness_deviation_list.append(median)
                else:
                    brightness_deviation_list.append(0)

            average_brightness_deviation = sum(brightness_deviation_list) / len(brightness_deviation_list)
            cal_confirmed_noise_filter = \
                max(min(round(round((average_brightness_deviation / 10) / 0.05) * 0.05, 2), 0.5), 0)

        cal_calibration_textbox.insert(tkinter.END, f"\n\nPreparing output images...\n")
        cal_calibration_textbox.see(tkinter.END)
        for i in range(len(cal_confirmed_files)):
            image_name = cal_confirmed_file_names[i]

            cal_calibration_textbox.insert(tkinter.END, f"\nNormalizing {image_name}...")
            cal_calibration_textbox.see(tkinter.END)
            width, height = cal_blurred_images[i][current_blur_number].size
            image_array = numpy.array(cal_blurred_images[i][current_blur_number].convert("HSV"))

            # Normalize image using calculated brightness map
            normalized_image_array = normalize_image(
                image_array,
                cal_brightness_maps[i][current_blur_number],
                width, height,
                cal_confirmed_noise_filter)

            normalized_image = Image.fromarray(normalized_image_array.astype("uint8"), "HSV").convert("RGB")
            cal_processed_files.append(normalized_image)
            cal_calibration_progress_bar["value"] += 1

        cal_calibration_textbox.insert(
            tkinter.END,
            "\n\nCalibration complete! Press the \"Show result\" button to view calibration results.")
        cal_calibration_textbox.see(tkinter.END)

        # Update results tab with new results
        cal_confirmed_normal_threshold = cal_normalization_thresholds[current_blur_number]
        results_go_to_picture(0, "cal")
        cal_results_settings_value_label.config(
            text=f"{cal_confirmed_image_compression}\n"
                 f"{cal_confirmed_channel}\n"
                 f"{cal_confirmed_blur_radius}\n"
                 f"{cal_confirmed_section_number}\n"
                 f"{cal_confirmed_pixel_number}\n"
                 f"{cal_confirmed_normal_threshold}\n"
                 f"{cal_confirmed_noise_filter}\n"
                 f"{cal_confirmed_line_number}")
        cal_results_blur_radius.set(str(cal_confirmed_blur_radius))
        cal_results_noise_filter.set(str(cal_confirmed_noise_filter))

        # Re-enable tabs at the conclusion of calibration, then enable the next and previous buttons
        calibration_side_tabs.tab(0, state="normal")
        calibration_side_tabs.tab(1, state="normal")
        calibration_side_tabs.tab(3, state="normal")
        cal_calibration_previous_button["state"] = "normal"
        cal_calibration_confirm_button["state"] = "normal"

    # Updates the results picture, label, and arrows for navigating the results pictures
    def results_go_to_picture(image_number, tab):
        if tab == "cal":
            global cal_current_viewed_picture

            # Disable left arrow if at first image, and disable right arrow if at last image
            if image_number == 0:
                cal_results_picture_left_arrow_button["state"] = "disabled"
                cal_results_picture_right_arrow_button["state"] = "normal"
            elif image_number == len(cal_confirmed_files) - 1:
                cal_results_picture_left_arrow_button["state"] = "normal"
                cal_results_picture_right_arrow_button["state"] = "disabled"
            else:
                cal_results_picture_left_arrow_button["state"] = "normal"
                cal_results_picture_right_arrow_button["state"] = "normal"

            # Update text label
            cal_results_picture_label.configure(text=cal_confirmed_file_names[image_number])

            # Update image
            draw_results_image(image_number, tab)

            # Update current viewed image variable
            cal_current_viewed_picture = image_number
        elif tab == "anl":
            global anl_current_viewed_picture

            # Disable left arrow if at first image, and disable right arrow if at last image
            if image_number == 0:
                anl_results_picture_left_arrow_button["state"] = "disabled"
                anl_results_picture_right_arrow_button["state"] = "normal"
            elif image_number == len(anl_confirmed_files) - 1:
                anl_results_picture_left_arrow_button["state"] = "normal"
                anl_results_picture_right_arrow_button["state"] = "disabled"
            else:
                anl_results_picture_left_arrow_button["state"] = "normal"
                anl_results_picture_right_arrow_button["state"] = "normal"

            # Update text label
            anl_results_picture_label.configure(text=anl_confirmed_file_names[image_number])

            # Update image
            draw_results_image(image_number, tab)

            # Update current viewed image variable
            anl_current_viewed_picture = image_number

    # Resizes an image to fit into a rectangle
    def resize_image(image, width, height):
        image_width, image_height = image.size
        # Determine whether label is longer or taller than image by comparing aspect ratios
        # Label is longer than the image
        if (width / height) >= (image_width / image_height):
            # Scale by height
            scale_width = round(image_width * (height - 20) / image_height)
            image = image.resize((scale_width, height - 20))
        # Label is taller than the image
        else:
            # Scale by width
            scale_height = round(image_height * width / image_width)
            image = image.resize((width, scale_height))

        return image

    # Takes an image file, resizes it, then draws the image onto the results label
    def draw_results_image(image_number, tab):
        if tab == "cal":
            image = cal_processed_files[image_number]
            label = cal_results_picture_label
        elif tab == "anl":
            image = anl_processed_files[image_number]
            label = anl_results_picture_label

        # Resize image according to label's width and height
        label_width = label.winfo_width()
        label_height = label.winfo_height()
        displayed_image = image.copy()
        displayed_image = resize_image(displayed_image, label_width, label_height - 20)

        # Convert to tkinter image and display
        tk_displayed_image = ImageTk.PhotoImage(displayed_image)
        label.configure(image=tk_displayed_image)
        label.image = tk_displayed_image  # Prevent garbage collection

    def cal_update_results(new_blur, new_noise_filter):
        global cal_confirmed_blur_radius, cal_confirmed_normal_threshold, cal_confirmed_noise_filter

        blur_number = new_blur

        # Update internal blur radius and noise filter values
        cal_confirmed_blur_radius = new_blur
        cal_confirmed_normal_threshold = cal_normalization_thresholds[blur_number]
        cal_confirmed_noise_filter = new_noise_filter

        # Check for existing threads. If previous threads exist, prompt them to stop
        if cal_noise_filter_threads:
            for thread in cal_noise_filter_threads:
                thread.stop = True

        # Redraw images using new thread
        noise_filter_thread = CalNoiseCalculationThread()
        cal_noise_filter_threads.append(noise_filter_thread)
        noise_filter_thread.start()

        # Disable the slider and spinbox widgets
        cal_results_settings_blur_slider["state"] = "disabled"
        cal_results_settings_blur_spinbox["state"] = "disabled"
        cal_results_settings_noise_slider["state"] = "disabled"
        cal_results_settings_noise_spinbox["state"] = "disabled"

        # Update the label text
        settings_values = cal_results_settings_value_label.cget("text").split("\n")
        settings_values[2] = str(cal_confirmed_blur_radius)
        settings_values[5] = str(cal_confirmed_normal_threshold)
        settings_values[6] = str(cal_confirmed_noise_filter)
        cal_results_settings_value_label["text"] = "\n".join(settings_values)

    def cal_results_blur_spinbox_update(_):
        sanitize_input(cal_results_blur_radius, False, "int", 0, 5)
        cal_update_results(int(cal_results_blur_radius.get()), cal_confirmed_noise_filter)

    def cal_results_noise_spinbox_update(_):
        sanitize_input(cal_results_noise_filter, False, "float", -0.5, 0.5)
        cal_update_results(cal_confirmed_blur_radius, float(cal_results_noise_filter.get()))

    def cal_save_settings():
        folder_path = filedialog.askdirectory()

        # If user did not press cancel
        if folder_path:

            # If save folder exists, add a number until an available save folder is found
            save_path = folder_path + "/Settings_Output/"
            if path.isdir(save_path):
                folder_number = 2
                while path.isdir(save_path[:-1] + " (" + str(folder_number) + ")/"):
                    folder_number += 1
                save_path = save_path[:-1] + " (" + str(folder_number) + ")/"
            mkdir(save_path)

            with open(save_path + "Settings " + current_version + ".txt", mode="w") as settings_file:
                settings_file.write(
                    f"compressed_image_size = {cal_confirmed_image_compression}\n"
                    f"channel = {cal_confirmed_channel}\n"
                    f"blur_radius = {cal_confirmed_blur_radius}\n"
                    f"section_size = {cal_confirmed_section_number}\n"
                    f"pixels_sampled = {cal_confirmed_pixel_number}\n"
                    f"normalization_cutoff = {cal_confirmed_normal_threshold}\n"
                    f"noise_cutoff = {cal_confirmed_noise_filter}\n"
                    f"lines = {cal_confirmed_line_number}")

            for i in range(len(cal_processed_files)):
                image_name = ".".join(cal_confirmed_file_names[i].split(".")[:-1])
                image = cal_processed_files[i]
                image.save(save_path + image_name + "_processed.png")

            messagebox.showinfo(
                "Settings saved successfully",
                "The settings have been saved successfully to:\n\n" +
                save_path)

    def anl_add_settings():
        global anl_image_compression, anl_channel_selection, anl_blur_radius, anl_section_number, anl_pixel_number, \
            anl_normal_threshold, anl_noise_filter, anl_line_number, anl_has_uploaded_settings

        file_path = filedialog.askopenfilename()
        if file_path:
            if file_path.lower().endswith(".txt"):
                with open(file_path, mode="r") as settings:
                    setting_list = settings.readlines()

                    for setting in setting_list:
                        if "compressed_image_size" in setting:
                            anl_image_compression = int(setting[len("compressed_image_size = "):])
                        elif "channel" in setting:
                            anl_channel_selection = int(setting[len("channel = "):])
                        elif "blur_radius" in setting:
                            anl_blur_radius = int(setting[len("blur_radius = "):])
                        elif "section_size" in setting:
                            anl_section_number = int(setting[len("section_size = "):])
                        elif "pixels_sampled" in setting:
                            anl_pixel_number = int(setting[len("pixels_sampled = "):])
                        elif "normalization_cutoff" in setting:
                            anl_normal_threshold = int(setting[len("normalization_cutoff = "):])
                        elif "noise_cutoff" in setting:
                            anl_noise_filter = float(setting[len("noise_cutoff = "):])
                        elif "lines" in setting:
                            anl_line_number = int(setting[len("lines = "):])

                    # Update label values in settings page
                    anl_settings_value_label.config(
                        text=f"{anl_image_compression}\n"
                             f"{anl_channel_selection}\n"
                             f"{anl_blur_radius}\n"
                             f"{anl_section_number}\n"
                             f"{anl_pixel_number}\n"
                             f"{anl_normal_threshold}\n"
                             f"{anl_noise_filter}\n"
                             f"{anl_line_number}")

                    # Enable analysis button if files are confirmed
                    if anl_input_files == anl_confirmed_files:
                        anl_settings_confirm_button["state"] = "normal"

                    anl_has_uploaded_settings = True

            else:
                messagebox.showinfo(
                    "Incompatible file type selected",
                    "Incompatible file type selected!\n\nThis program can only accept TXT files.")

    def anl_go_to_analysis():
        global anl_confirmed_image_compression, anl_confirmed_channel, anl_confirmed_blur_radius, \
            anl_confirmed_section_number, anl_confirmed_pixel_number, anl_confirmed_normal_threshold, \
            anl_confirmed_noise_filter, anl_confirmed_line_number, anl_processed_files, anl_IJOQ_list

        # Determine settings
        anl_confirmed_image_compression = anl_image_compression
        anl_confirmed_channel = anl_channel_selection
        anl_confirmed_blur_radius = anl_blur_radius
        anl_confirmed_section_number = anl_section_number
        anl_confirmed_pixel_number = anl_pixel_number
        anl_confirmed_normal_threshold = anl_normal_threshold
        anl_confirmed_noise_filter = anl_noise_filter
        anl_confirmed_line_number = anl_line_number

        # Set progress bar to 0, delete text in textbox, and clear results
        anl_processed_files = []
        anl_IJOQ_list = []
        progress_bar_maximum = len(anl_confirmed_files) * (6 + (anl_confirmed_section_number ** 2))
        anl_analysis_progress_bar.config(maximum=progress_bar_maximum)
        anl_analysis_progress_bar["value"] = 0
        anl_analysis_textbox.delete(1.0, tkinter.END)

        # Move to the analysis screen
        analysis_side_tabs.tab(2, state="normal")
        analysis_side_tabs.select(2)

        # Disable other tabs
        analysis_side_tabs.tab(0, state="disabled")
        analysis_side_tabs.tab(1, state="disabled")
        analysis_side_tabs.tab(3, state="disabled")
        anl_analysis_previous_button["state"] = "disabled"
        anl_analysis_confirm_button["state"] = "disabled"

        analysis_thread = Thread(target=anl_run_analysis, daemon=True)
        analysis_thread.start()

    # Run analysis
    def anl_run_analysis():
        global anl_confirmed_image_compression, anl_confirmed_channel, anl_confirmed_blur_radius, \
            anl_confirmed_section_number, anl_confirmed_pixel_number, anl_confirmed_normal_threshold, \
            anl_confirmed_noise_filter, anl_IJOQ_list, anl_processed_files

        # Run analysis
        for file in anl_confirmed_files:
            # Determine the image name
            image_name = file.split("/")[-1]

            try:
                anl_analysis_textbox.insert(tkinter.END, f"Analyzing {image_name}...")
                anl_analysis_textbox.see(tkinter.END)

                image = Image.open(file)
                width, height = image.size
                compression_amount = (anl_confirmed_image_compression / 2) * (width + height) / (width * height)
                image = image.resize((round(compression_amount * width), round(compression_amount * height)))
                width, height = image.size

                # Take the RGB values from all the pixels in the image as an array
                image_array = numpy.array(image.convert("RGB"))

                # Extract channel
                anl_analysis_textbox.insert(tkinter.END, f"\nExtracting channel from {image_name}...")
                anl_analysis_textbox.see(tkinter.END)
                for x in range(width):
                    for y in range(height):
                        image_array[y][x] = [image_array[y][x][anl_confirmed_channel]] * 3

                # Apply blur
                anl_analysis_textbox.insert(tkinter.END, f"\nApplying blur to {image_name}...")
                anl_analysis_textbox.see(tkinter.END)
                image = Image.fromarray(image_array.astype("uint8"))
                blurred_image = image.filter(ImageFilter.GaussianBlur(radius=anl_confirmed_blur_radius))
                image_array = numpy.array(blurred_image.convert("HSV"))
                anl_analysis_progress_bar["value"] += 1

                # Split the picture into sections
                anl_analysis_textbox.insert(tkinter.END, f"\nCalculating threshold values for {image_name}...")
                anl_analysis_textbox.see(tkinter.END)
                section_width = width / anl_confirmed_section_number
                section_height = height / anl_confirmed_section_number
                normalization_threshold_array = numpy.zeros(
                    (anl_confirmed_section_number, anl_confirmed_section_number))

                # For each section, sample pixels, then find the normalization threshold
                for section_x in range(anl_confirmed_section_number):
                    for section_y in range(anl_confirmed_section_number):

                        sampled_values = []
                        for x in range(anl_confirmed_pixel_number):
                            for y in range(anl_confirmed_pixel_number):
                                pixel_x = round(
                                    section_width * (section_x + ((x + 0.5) / anl_confirmed_pixel_number)))
                                pixel_y = round(
                                    section_height * (section_y + ((y + 0.5) / anl_confirmed_pixel_number)))

                                sampled_values.append(image_array[pixel_y][pixel_x][2])

                        sampled_values.sort()
                        normalization_threshold_array[section_x][section_y] = \
                            sampled_values[anl_confirmed_normal_threshold - 1]
                        anl_analysis_progress_bar["value"] += 1

                # Parse through the image array and calculate brightness map
                anl_analysis_textbox.insert(tkinter.END, f"\nCalculating brightness map for {image_name}...")
                anl_analysis_textbox.see(tkinter.END)
                brightness_map = numpy.zeros((height, width))
                for x in range(width):
                    for y in range(height):
                        brightness_map[y][x] = calculate_threshold(
                            x, y,
                            anl_confirmed_section_number,
                            normalization_threshold_array,
                            section_width, section_height)
                anl_analysis_progress_bar["value"] += 1

                # Normalize image using calculated brightness map
                normalized_image_array = normalize_image(
                    image_array,
                    brightness_map,
                    width, height,
                    anl_confirmed_noise_filter)
                normalized_image = Image.fromarray(normalized_image_array.astype("uint8"), "HSV").convert("RGB")
                anl_processed_files.append(normalized_image)
                anl_analysis_progress_bar["value"] += 1

                # Draw horizontal lines
                anl_analysis_textbox.insert(tkinter.END, f"\nCalculating IJOQ for {image_name}...")
                anl_analysis_textbox.see(tkinter.END)
                cell_border_frequency = 0
                for y in range(anl_confirmed_line_number):
                    pixel_y = round((y + 0.5) * height / anl_confirmed_line_number)

                    previous_pixel = image_array[pixel_y][0][2]
                    for x in range(1, width):
                        current_pixel = image_array[pixel_y][x][2]
                        # If the line detects a color change (i.e. black to white or white to black)
                        if not previous_pixel == current_pixel:
                            cell_border_frequency += 0.5 / width

                        # Set current pixel as the previous pixel before moving to the next pixel
                        previous_pixel = current_pixel

                # Increment progress bar
                anl_analysis_progress_bar["value"] += 1

                # Repeat the same steps vertical lines
                for x in range(anl_confirmed_line_number):
                    pixel_x = round((x + 0.5) * width / anl_confirmed_line_number)

                    previous_pixel = image_array[0][pixel_x][2]
                    for y in range(1, height):
                        current_pixel = image_array[y][pixel_x][2]
                        if not previous_pixel == current_pixel:
                            cell_border_frequency += 0.5 / height

                        # Set current pixel as the previous pixel before moving to the next pixel
                        previous_pixel = current_pixel

                # Increment progress bar
                anl_analysis_progress_bar["value"] += 1

                # Take average of all lines
                IJOQ = round(cell_border_frequency / (2 * anl_confirmed_line_number), 4)
                anl_analysis_textbox.insert(tkinter.END, f"\n{image_name} has an IJOQ value of {IJOQ}.\n\n")
                anl_analysis_textbox.see(tkinter.END)
                anl_IJOQ_list.append(IJOQ)
                anl_analysis_progress_bar["value"] += 1

            # File could not be opened
            except FileNotFoundError:
                # Print warning, re-enable file selection and settings, then stop function
                anl_analysis_textbox.insert(
                    tkinter.END, f"WARNING! Unable to find file for {image_name}!")
                anl_analysis_textbox.see(tkinter.END)

                analysis_side_tabs.tab(0, state="normal")
                analysis_side_tabs.tab(1, state="normal")
                anl_analysis_previous_button["state"] = "normal"

                return

        anl_analysis_textbox.insert(
            tkinter.END,
            "Analysis complete! Press the \"Show result\" button to view analysis results.")
        anl_analysis_textbox.see(tkinter.END)

        # Update results tab with new results
        results_go_to_picture(0, "anl")

        # Re-enable tabs at the conclusion of calibration, then enable the next and previous buttons
        analysis_side_tabs.tab(0, state="normal")
        analysis_side_tabs.tab(1, state="normal")
        analysis_side_tabs.tab(3, state="normal")
        anl_analysis_previous_button["state"] = "normal"
        anl_analysis_confirm_button["state"] = "normal"

    # Save results after IJOQ analysis
    def anl_save_results():
        folder_path = filedialog.askdirectory()

        # If user did not press cancel
        if folder_path:

            # If save folder exists, add a number until an available save folder is found
            save_path = folder_path + "/Analysis_Output/"
            if path.isdir(save_path):
                folder_number = 2
                while path.isdir(save_path[:-1] + " (" + str(folder_number) + ")/"):
                    folder_number += 1
                save_path = save_path[:-1] + " (" + str(folder_number) + ")/"
            mkdir(save_path)

            with open(save_path + "IJOQ Results " + current_version + ".csv", mode="w", newline="") as results_file:
                data_writer = csv.writer(results_file)
                data_writer.writerow(["File name", "IJOQ"])
                for i in range(len(anl_confirmed_files)):
                    data_writer.writerow([anl_confirmed_file_names[i], anl_IJOQ_list[i]])

            for i in range(len(anl_processed_files)):
                image_name = ".".join(anl_confirmed_file_names[i].split(".")[:-1])
                image = anl_processed_files[i]
                image.save(save_path + image_name + "_processed.png")

            messagebox.showinfo(
                "Results saved successfully",
                "The analysis results have been saved successfully to:\n\n" +
                save_path)


    # Opens up tkinter, set up window
    root = tkinter.Tk()
    root.geometry("750x500")
    root.minsize(750, 500)
    root.title("IJOQ " + current_version)

    # Styles
    centered_tab_style = ttk.Style()
    centered_tab_style.configure("centered.TNotebook", tabposition="n")

    # Input validation
    vcmd_int = (root.register(validate_input_int), "%P")
    vcmd_float = (root.register(validate_input_float), "%P")

    # Add upper tabs
    upper_tabs = ttk.Notebook(root, style="centered.TNotebook")
    upper_tabs.pack(fill="both", expand=True)

    calibration_frame = ttk.Frame(upper_tabs)
    analysis_frame = ttk.Frame(upper_tabs)
    calibration_frame.pack(fill="both", expand=True)
    analysis_frame.pack(fill="both", expand=True)

    upper_tabs.add(calibration_frame, text=f'{"Calibrate IJOQ":^80s}')
    upper_tabs.add(analysis_frame, text=f'{"IJOQ analysis":^80s}')

    # ==CALIBRATION==
    # Add calibration tabs
    calibration_side_tabs = ttk.Notebook(calibration_frame)
    calibration_side_tabs.pack(fill="both", expand=True)

    cal_select_frame = ttk.Frame(calibration_side_tabs)
    cal_settings_frame = ttk.Frame(calibration_side_tabs)
    cal_calibration_frame = ttk.Frame(calibration_side_tabs)
    cal_results_frame = ttk.Frame(calibration_side_tabs)
    cal_select_frame.pack(fill="both", expand=True)
    cal_settings_frame.pack(fill="both", expand=True)
    cal_calibration_frame.pack(fill="both", expand=True)
    cal_results_frame.pack(fill="both", expand=True)

    calibration_side_tabs.add(cal_select_frame, text=f'{"1. Select images":^25s}')
    calibration_side_tabs.add(cal_settings_frame, text=f'{"2. Select settings":^25s}')
    calibration_side_tabs.add(cal_calibration_frame, text=f'{"3. Calibration":^25s}')
    calibration_side_tabs.add(cal_results_frame, text=f'{"4. View Results":^25s}')
    calibration_side_tabs.tab(1, state="disabled")
    calibration_side_tabs.tab(2, state="disabled")
    calibration_side_tabs.tab(3, state="disabled")

    calibration_side_tabs.bind(
        "<<NotebookTabChanged>>",
        lambda e: update_current_tab("cal"))

    # Calibration variables
    # Global calibration variables
    cal_current_tab = 0
    cal_confirmed_files = []
    cal_confirmed_file_names = ()
    cal_blurred_images = []
    cal_normalization_thresholds = []
    cal_brightness_maps = []
    cal_processed_files = []
    cal_confirmed_channel = 0
    cal_confirmed_image_compression = 0
    cal_confirmed_blur_radius = 0
    cal_confirmed_section_number = 0
    cal_confirmed_pixel_number = 0
    cal_confirmed_normal_threshold = 0
    cal_confirmed_noise_filter = 0
    cal_confirmed_line_number = 0
    cal_current_viewed_picture = 0
    cal_noise_filter_threads = []

    # File selection variables
    cal_input_files = []

    # Settings selection variables
    cal_cell_number_x = tkinter.StringVar()
    cal_cell_number_x.set("0")
    cal_cell_number_y = tkinter.StringVar()
    cal_cell_number_y.set("0")
    cal_channel_options = ("Red", "Green", "Blue", "White")
    cal_channel_selection = tkinter.StringVar()
    cal_image_compression = tkinter.StringVar()
    cal_image_compression.set("512")
    cal_blur_radius = tkinter.StringVar()
    cal_blur_radius.set("4")
    cal_section_number = tkinter.StringVar()
    cal_section_number.set("4")
    cal_pixel_number = tkinter.StringVar()
    cal_pixel_number.set("8")
    cal_noise_filter = tkinter.StringVar()
    cal_noise_filter.set("0.1")
    cal_line_number = tkinter.StringVar()
    cal_line_number.set("10")
    cal_results_blur_radius = tkinter.StringVar()
    cal_results_noise_filter = tkinter.StringVar()

    # ==CALIBRATION:SELECT IMAGE PAGE==
    # Add calibration frames
    # Frame for calibration file entry
    cal_select_frame.columnconfigure(0, weight=1)
    cal_select_frame.columnconfigure(1, weight=0)
    cal_select_frame.rowconfigure(0, weight=0)
    cal_select_frame.rowconfigure(1, weight=1)
    cal_select_frame.rowconfigure(2, weight=0)

    # Add description label to the top
    cal_file_description_label = ttk.Label(
        master=cal_select_frame,
        text="Calibration is required to determine proper settings for IJOQ analysis. "
             "Once calibrated, recalibrating is not required until the experimental protocol is changed.\n\n"
             "To begin, please select at least 3 negative control images.\n"
             "All files located in folders that have \"Output\" in their names will be automatically excluded.")
    cal_file_description_label.bind(
        "<Configure>",
        lambda e, label=cal_file_description_label: label.config(wraplength=label.winfo_width()))
    cal_file_description_label.grid(padx=10, pady=10, row=0, column=0, columnspan=2, sticky="nsew")

    # Add center frames
    cal_file_list_frame = ttk.Frame(cal_select_frame)
    cal_file_options_frame = ttk.Frame(cal_select_frame)
    cal_file_list_frame.grid(padx=10, row=1, column=0, sticky="nsew")
    cal_file_options_frame.grid(row=1, column=1, sticky="nsew")

    # Add file list
    cal_file_list_frame.columnconfigure(0, weight=1)
    cal_file_list_frame.columnconfigure(1, weight=0)
    cal_file_list_frame.rowconfigure(0, weight=0)
    cal_file_list_frame.rowconfigure(1, weight=1)

    cal_file_list_label = ttk.Label(master=cal_file_list_frame, text="Selected files:")
    cal_file_list_box = tkinter.Listbox(master=cal_file_list_frame)
    cal_file_list_scrollbar = ttk.Scrollbar(master=cal_file_list_frame, orient="vertical")
    cal_file_list_box.config(yscrollcommand=cal_file_list_scrollbar.set)
    cal_file_list_scrollbar.config(command=cal_file_list_box.yview)
    cal_file_list_label.grid(row=0, column=0, sticky="nsew")
    cal_file_list_box.grid(row=1, column=0, sticky="nsew")
    cal_file_list_scrollbar.grid(row=1, column=1, sticky="ns")

    # Add file options
    cal_file_add_button = ttk.Button(
        master=cal_file_options_frame, text="Add file",
        command=lambda: add_file("cal"))
    cal_folder_add_button = ttk.Button(
        master=cal_file_options_frame, text="Add folder",
        command=lambda: add_folder("cal"))
    cal_file_delete_button = ttk.Button(
        master=cal_file_options_frame, text="Delete selection",
        command=lambda: del_file("cal"))
    cal_file_clear_button = ttk.Button(
        master=cal_file_options_frame, text="Clear all",
        command=lambda: clear_file("cal"))
    cal_file_add_button.pack(padx=10, pady=2, fill="both")
    cal_folder_add_button.pack(padx=10, pady=2, fill="both")
    cal_file_delete_button.pack(padx=10, pady=2, fill="both")
    cal_file_clear_button.pack(padx=10, pady=2, fill="both")

    # Add lower button
    cal_file_select_button = ttk.Button(
        master=cal_select_frame,
        text="Confirm selection",
        width=20,
        state="disabled",
        command=lambda: confirm_files("cal"))
    cal_file_select_button.grid(padx=10, pady=10, row=2, column=1, sticky="se")

    # ==CALIBRATION:SETTINGS PAGE==
    # Frame for determining the settings
    cal_settings_frame.columnconfigure(0, weight=1)
    cal_settings_frame.columnconfigure(1, weight=1)
    cal_settings_frame.rowconfigure(0, weight=1)
    cal_settings_frame.rowconfigure(1, weight=0)

    # Add Basic and Advanced settings tab
    cal_settings_options_tabs = ttk.Notebook(cal_settings_frame, style="centered.TNotebook")
    cal_settings_options_tabs.grid(padx=10, pady=10, row=0, columnspan=2, sticky="nsew")

    cal_settings_basic_frame = ttk.Frame(cal_settings_options_tabs)
    cal_settings_advanced_frame = ttk.Frame(cal_settings_options_tabs)

    cal_settings_options_tabs.add(cal_settings_basic_frame, text=f'{"Basic":^80s}')
    cal_settings_options_tabs.add(cal_settings_advanced_frame, text=f'{"Advanced":^80s}')

    # Basic Frame
    cal_settings_basic_frame.columnconfigure(0, weight=4)
    cal_settings_basic_frame.columnconfigure(1, weight=1)
    cal_settings_basic_frame.rowconfigure(0, weight=0)
    cal_settings_basic_frame.rowconfigure(1, weight=0)
    cal_settings_basic_frame.rowconfigure(2, weight=0)
    cal_settings_basic_frame.rowconfigure(3, weight=0)

    # Basic Setting Labels
    cal_settings_description_label = ttk.Label(
        master=cal_settings_basic_frame,
        text="Use the basic settings if you want the program to estimate the settings for you. "
             "Use the advanced settings if you would like to change the calibration manually.")
    cal_settings_description_label.bind(
        "<Configure>",
        lambda e, label=cal_settings_description_label: label.config(wraplength=label.winfo_width()))
    cal_settings_description_label.grid(padx=10, pady=15, row=0, column=0, columnspan=2, sticky="nsew")
    cal_settings_cell_number_x_label = ttk.Label(
        master=cal_settings_basic_frame,
        text="Estimate the number of cells along the image width:")
    cal_settings_cell_number_y_label = ttk.Label(
        master=cal_settings_basic_frame,
        text="Estimate the number of cells along the image height:")
    cal_settings_channel_label = ttk.Label(
        master=cal_settings_basic_frame,
        text="Select the channel that you want to calibrate to:")

    # Basic Setting Spinbox
    cal_settings_cell_number_x_spinbox = ttk.Spinbox(
        cal_settings_basic_frame, from_=0, to=99,
        wrap=True, textvariable=cal_cell_number_x, width=5,
        validate="key", validatecommand=vcmd_int)
    cal_settings_cell_number_x_spinbox.bind(
        "<FocusOut>",
        lambda e: sanitize_input(cal_cell_number_x, False, "int", 0, 99))
    cal_settings_cell_number_x_spinbox.bind(
        "<Return>",
        lambda e: root.focus())
    cal_settings_cell_number_y_spinbox = ttk.Spinbox(
        cal_settings_basic_frame, from_=0, to=99,
        wrap=True, textvariable=cal_cell_number_y, width=5,
        validate="key", validatecommand=vcmd_int)
    cal_settings_cell_number_y_spinbox.bind(
        "<FocusOut>",
        lambda e: sanitize_input(cal_cell_number_y, False, "int", 0, 99))
    cal_settings_cell_number_y_spinbox.bind(
        "<Return>",
        lambda e: root.focus())

    # Basic Setting Dropdown
    cal_settings_channel_dropdown = ttk.OptionMenu(
        cal_settings_basic_frame, cal_channel_selection,
        cal_channel_options[0], *cal_channel_options)
    cal_settings_channel_dropdown.configure(width=5)

    # Grid the Basic Setting Components
    cal_settings_cell_number_x_label.grid(padx=10, pady=10, row=1, column=0, sticky="ew")
    cal_settings_cell_number_y_label.grid(padx=10, pady=10, row=2, column=0, sticky="ew")
    cal_settings_channel_label.grid(padx=10, pady=10, row=3, column=0, sticky="ew")
    cal_settings_cell_number_x_spinbox.grid(padx=10, pady=10, row=1, column=1, sticky="w")
    cal_settings_cell_number_y_spinbox.grid(padx=10, pady=10, row=2, column=1, sticky="w")
    cal_settings_channel_dropdown.grid(padx=10, pady=10, row=3, column=1, sticky="w")

    # Advanced Frame
    cal_settings_advanced_frame.columnconfigure(0, weight=4)
    cal_settings_advanced_frame.columnconfigure(1, weight=1)
    cal_settings_advanced_frame.rowconfigure(0, weight=0)
    cal_settings_advanced_frame.rowconfigure(1, weight=0)
    cal_settings_advanced_frame.rowconfigure(2, weight=0)
    cal_settings_advanced_frame.rowconfigure(3, weight=0)
    cal_settings_advanced_frame.rowconfigure(4, weight=0)
    cal_settings_advanced_frame.rowconfigure(5, weight=0)
    cal_settings_advanced_frame.rowconfigure(6, weight=0)

    # Advanced Settings Label
    cal_settings_image_compression_label = ttk.Label(
        master=cal_settings_advanced_frame, text="Image compression")
    cal_settings_advanced_channel_label = ttk.Label(
        master=cal_settings_advanced_frame, text="Color channel")
    cal_settings_blur_radius_label = ttk.Label(
        master=cal_settings_advanced_frame, text="Blur radius")
    cal_settings_section_number_label = ttk.Label(
        master=cal_settings_advanced_frame, text="Number of sections to be split")
    cal_settings_pixel_number_label = ttk.Label(
        master=cal_settings_advanced_frame, text="Number of pixels to be sampled")
    cal_settings_noise_filter_label = ttk.Label(
        master=cal_settings_advanced_frame, text="Percentage of noise filter")
    cal_settings_line_number_label = ttk.Label(
        master=cal_settings_advanced_frame, text="Number of lines drawn")

    # Advanced Settings Spinbox
    cal_settings_image_compression_spinbox = ttk.Spinbox(
        cal_settings_advanced_frame, from_=0, to=1024,
        wrap=True, textvariable=cal_image_compression, width=6,
        validate="key", validatecommand=vcmd_int)
    cal_settings_image_compression_spinbox.bind(
        "<FocusOut>",
        lambda e: sanitize_input(cal_image_compression, False, "int", 128, 1024))
    cal_settings_image_compression_spinbox.bind(
        "<Return>",
        lambda e: root.focus())
    cal_settings_blur_radius_spinbox = ttk.Spinbox(
        cal_settings_advanced_frame, from_=0, to=5,
        wrap=True, textvariable=cal_blur_radius, width=6,
        validate="key", validatecommand=vcmd_int)
    cal_settings_blur_radius_spinbox.bind(
        "<FocusOut>",
        lambda e: sanitize_input(cal_blur_radius, False, "int", 0, 5))
    cal_settings_blur_radius_spinbox.bind(
        "<Return>",
        lambda e: root.focus())
    cal_settings_section_number_spinbox = ttk.Spinbox(
        cal_settings_advanced_frame, from_=0, to=10,
        wrap=True, textvariable=cal_section_number, width=6,
        validate="key", validatecommand=vcmd_int)
    cal_settings_section_number_spinbox.bind(
        "<FocusOut>",
        lambda e: sanitize_input(cal_section_number, False, "int", 0, 10))
    cal_settings_section_number_spinbox.bind(
        "<Return>",
        lambda e: root.focus())
    cal_settings_pixel_number_spinbox = ttk.Spinbox(
        cal_settings_advanced_frame, from_=0, to=99,
        wrap=True, textvariable=cal_pixel_number, width=6,
        validate="key", validatecommand=vcmd_int)
    cal_settings_pixel_number_spinbox.bind(
        "<FocusOut>",
        lambda e: sanitize_input(cal_pixel_number, False, "int", 0, 99))
    cal_settings_pixel_number_spinbox.bind(
        "<Return>",
        lambda e: root.focus())
    cal_settings_noise_filter_spinbox = ttk.Spinbox(
        cal_settings_advanced_frame, from_=-0.5, to=0.5, increment=0.005,
        wrap=True, textvariable=cal_noise_filter, width=6,
        validate="key", validatecommand=vcmd_float)
    cal_settings_noise_filter_spinbox.bind(
        "<FocusOut>",
        lambda e: sanitize_input(cal_noise_filter, False, "float", -0.5, 0.5))
    cal_settings_noise_filter_spinbox.bind(
        "<Return>",
        lambda e: root.focus())
    cal_settings_line_number_spinbox = ttk.Spinbox(
        cal_settings_advanced_frame, from_=0, to=99,
        wrap=True, textvariable=cal_line_number, width=6,
        validate="key", validatecommand=vcmd_int)
    cal_settings_line_number_spinbox.bind(
        "<FocusOut>",
        lambda e: sanitize_input(cal_line_number, False, "int", 0, 99))
    cal_settings_line_number_spinbox.bind(
        "<Return>",
        lambda e: root.focus())

    # Advanced Settings Dropdown
    cal_settings_advanced_channel_dropdown = ttk.OptionMenu(
        cal_settings_advanced_frame, cal_channel_selection,
        cal_channel_options[0], *cal_channel_options)
    cal_settings_advanced_channel_dropdown.configure(width=8)

    # Grid the Advanced Setting Components
    cal_settings_image_compression_label.grid(padx=10, pady=6, row=0, column=0, sticky="ew")
    cal_settings_advanced_channel_label.grid(padx=10, pady=6, row=1, column=0, sticky="ew")
    cal_settings_blur_radius_label.grid(padx=10, pady=6, row=2, column=0, sticky="ew")
    cal_settings_section_number_label.grid(padx=10, pady=6, row=3, column=0, sticky="ew")
    cal_settings_pixel_number_label.grid(padx=10, pady=6, row=4, column=0, sticky="ew")
    cal_settings_noise_filter_label.grid(padx=10, pady=6, row=5, column=0, sticky="ew")
    cal_settings_line_number_label.grid(padx=10, pady=6, row=6, column=0, sticky="ew")
    cal_settings_image_compression_spinbox.grid(padx=10, pady=6, row=0, column=1, sticky="w")
    cal_settings_advanced_channel_dropdown.grid(padx=10, pady=6, row=1, column=1, sticky="w")
    cal_settings_blur_radius_spinbox.grid(padx=10, pady=6, row=2, column=1, sticky="w")
    cal_settings_section_number_spinbox.grid(padx=10, pady=6, row=3, column=1, sticky="w")
    cal_settings_pixel_number_spinbox.grid(padx=10, pady=6, row=4, column=1, sticky="w")
    cal_settings_noise_filter_spinbox.grid(padx=10, pady=6, row=5, column=1, sticky="w")
    cal_settings_line_number_spinbox.grid(padx=10, pady=6, row=6, column=1, sticky="w")

    # Add previous and confirm button
    cal_settings_previous_button = ttk.Button(
        master=cal_settings_frame,
        text="Previous",
        width=20,
        command=lambda: go_to_previous_page("cal"))
    cal_settings_confirm_button = ttk.Button(
        master=cal_settings_frame,
        text="Run calibration",
        width=20,
        state="disabled",
        command=cal_go_to_calibration)
    cal_settings_previous_button.grid(padx=10, pady=10, row=1, column=0, sticky="sw")
    cal_settings_confirm_button.grid(padx=10, pady=10, row=1, column=1, sticky="se")

    # ==CALIBRATION:CALIBRATION PAGE==
    cal_calibration_frame.columnconfigure(0, weight=1)
    cal_calibration_frame.columnconfigure(1, weight=1)
    cal_calibration_frame.rowconfigure(0, weight=0)
    cal_calibration_frame.rowconfigure(1, weight=1)
    cal_calibration_frame.rowconfigure(2, weight=0)

    # Add a progress bar
    cal_calibration_progress_bar = ttk.Progressbar(
        master=cal_calibration_frame,
        orient="horizontal",
        mode='determinate')
    cal_calibration_progress_bar.grid(padx=10, pady=10, row=0, column=0, columnspan=2, sticky="ew")

    # Add a frame for text box and scrollbar
    cal_calibration_text_frame = ttk.Frame(cal_calibration_frame)
    cal_calibration_text_frame.grid(padx=10, pady=0, row=1, column=0, columnspan=2, sticky="nsew")

    cal_calibration_text_frame.columnconfigure(0, weight=1)
    cal_calibration_text_frame.columnconfigure(1, weight=0)
    cal_calibration_text_frame.rowconfigure(0, weight=1)

    # Add scroll bar for text box
    cal_calibration_textbox = tkinter.Text(cal_calibration_text_frame)
    cal_calibration_textbox.bind(
        "<Key>",
        lambda e: "break")
    cal_calibration_text_scrollbar = ttk.Scrollbar(master=cal_calibration_text_frame, orient="vertical")
    cal_calibration_textbox.config(yscrollcommand=cal_calibration_text_scrollbar.set)
    cal_calibration_text_scrollbar.config(command=cal_calibration_textbox.yview)
    cal_calibration_textbox.grid(row=0, column=0, sticky="nsew")
    cal_calibration_text_scrollbar.grid(row=0, column=1, sticky="ns")

    # Add previous and confirm button
    cal_calibration_previous_button = ttk.Button(
        master=cal_calibration_frame,
        text="Previous",
        width=20,
        state="disabled",
        command=lambda: go_to_previous_page("cal"))
    cal_calibration_confirm_button = ttk.Button(
        master=cal_calibration_frame,
        text="Show result",
        width=20,
        state="disabled",
        command=lambda: calibration_side_tabs.select(3))
    cal_calibration_previous_button.grid(padx=10, pady=10, row=2, column=0, sticky="sw")
    cal_calibration_confirm_button.grid(padx=10, pady=10, row=2, column=1, sticky="se")

    # ==CALIBRATION:RESULTS PAGE==
    cal_results_frame.columnconfigure(0, weight=1)
    cal_results_frame.columnconfigure(1, weight=0)
    cal_results_frame.rowconfigure(0, weight=0)
    cal_results_frame.rowconfigure(1, weight=1)
    cal_results_frame.rowconfigure(2, weight=0)

    # Add description label
    cal_results_description_label = ttk.Label(
        master=cal_results_frame,
        text="If the basic settings were selected, "
             "the calibration settings were estimated to the best of the program's abilities. "
             "Please review the processed images and ensure that the calibration is "
             "adequately thresholding the images.\n\n"
             "You may edit the blur radius and the noise threshold at the bottom right "
             "to make adjustments to the calibration settings before saving. "
             "It may take a moment for the image to update after adjusting the blur radius or noise threshold.")
    cal_results_description_label.bind(
        "<Configure>",
        lambda e, label=cal_results_description_label: label.config(wraplength=label.winfo_width()))
    cal_results_description_label.grid(padx=10, pady=5, row=0, column=0, columnspan=2, sticky="new")

    # Frame for picture
    cal_results_picture_frame = ttk.Frame(cal_results_frame)
    cal_results_picture_frame.grid(padx=5, pady=5, row=1, column=0, sticky="nsew")
    cal_results_picture_frame.columnconfigure(0, weight=1)
    cal_results_picture_frame.columnconfigure(1, weight=3)
    cal_results_picture_frame.columnconfigure(2, weight=1)
    cal_results_picture_frame.rowconfigure(0, weight=1)

    # Arrows for picture
    cal_results_picture_left_arrow_button = ttk.Button(
        master=cal_results_picture_frame,
        text="←",
        width=3,
        command=lambda: results_go_to_picture(cal_current_viewed_picture - 1, "cal")
        )
    cal_results_picture_right_arrow_button = ttk.Button(
        master=cal_results_picture_frame,
        text="→",
        width=3,
        command=lambda: results_go_to_picture(cal_current_viewed_picture + 1, "cal")
        )
    cal_results_picture_left_arrow_button.grid(row=0, column=0, sticky="e")
    cal_results_picture_right_arrow_button.grid(row=0, column=2, sticky="w")

    # Textbox for Picture
    cal_results_picture_label = ttk.Label(cal_results_picture_frame, compound=tkinter.TOP, anchor=tkinter.CENTER)
    cal_results_picture_label.grid(row=0, column=1, sticky="nsew")
    cal_results_picture_label.bind(
        "<Configure>",
        lambda e: draw_results_image(cal_current_viewed_picture, "cal"))

    # Frame for settings
    cal_results_settings_frame = ttk.Frame(cal_results_frame)
    cal_results_settings_frame.grid(padx=10, pady=5, row=1, column=1, sticky="nsew")
    cal_results_settings_frame.rowconfigure(0, weight=0)
    cal_results_settings_frame.rowconfigure(1, weight=1)
    cal_results_settings_frame.rowconfigure(2, weight=0)
    cal_results_settings_frame.rowconfigure(3, weight=0)
    cal_results_settings_frame.rowconfigure(4, weight=0)
    cal_results_settings_frame.rowconfigure(5, weight=0)

    # Parameter label for the settings
    cal_results_settings_label = ttk.Label(
        master=cal_results_settings_frame,
        text="Parameters:")
    cal_results_settings_label.grid(row=0, column=0, sticky="nsew")
    cal_results_settings_parameter_labels = ttk.Label(
        master=cal_results_settings_frame,
        text="Image compression: \n"
        "Color channel: \n"
        "Blur radius: \n"
        "Number of sections: \n"
        "Number of pixels: \n"
        "Normalization threshold: \n"
        "Noise filter: \n"
        "Number of lines: \n",
        anchor=tkinter.NW,
        justify=tkinter.LEFT)
    cal_results_settings_parameter_labels.grid(row=1, column=0, sticky="nsew")

    # Parameter value label for the settings
    cal_results_settings_value_label = ttk.Label(
        master=cal_results_settings_frame,
        anchor=tkinter.NW, width=20,
        justify=tkinter.LEFT)
    cal_results_settings_value_label.grid(row=1, column=1, columnspan=2, sticky="nsew")

    # Label for the blur radius
    cal_results_settings_blur_label = ttk.Label(
        master=cal_results_settings_frame,
        text="Blur radius:")
    cal_results_settings_blur_label.grid(row=2, column=0, sticky="nsew")

    # Slider for the blur radius
    cal_results_settings_blur_slider = ttk.Scale(
        master=cal_results_settings_frame,
        from_=0, to=5,
        variable=cal_results_blur_radius,
        length=200,
        command=lambda e: cal_results_blur_radius.set(
            str(int(round(float(cal_results_blur_radius.get()))))))
    cal_results_settings_blur_slider.bind(
        "<ButtonRelease-1>",
        lambda e: cal_update_results(int(cal_results_blur_radius.get()), cal_confirmed_noise_filter))
    cal_results_settings_blur_slider.grid(padx=2, row=3, column=0, columnspan=2, sticky="ew")

    # Spinbox for the blur radius
    cal_results_settings_blur_spinbox = ttk.Spinbox(
        cal_results_settings_frame, from_=0, to=5,
        wrap=True, textvariable=cal_results_blur_radius, width=6,
        command=lambda: cal_update_results(int(cal_results_blur_radius.get()), cal_confirmed_noise_filter),
        validate="key", validatecommand=vcmd_int)
    cal_results_settings_blur_spinbox.bind(
        "<FocusOut>",
        cal_results_blur_spinbox_update)
    cal_results_settings_blur_spinbox.bind(
        "<Return>",
        lambda e: root.focus())
    cal_results_settings_blur_spinbox.grid(padx=2, row=3, column=2, sticky="e")

    # Label for the noise threshold
    cal_results_settings_noise_label = ttk.Label(
        master=cal_results_settings_frame,
        text="Noise Threshold:")
    cal_results_settings_noise_label.grid(row=4, column=0, sticky="nsew")

    # Slider for the noise threshold
    cal_results_settings_noise_slider = ttk.Scale(
        master=cal_results_settings_frame,
        from_=-0.5, to=0.5,
        variable=cal_results_noise_filter,
        length=200,
        command=lambda e: cal_results_noise_filter.set(
            str(round(round(float(cal_results_noise_filter.get())/0.005) * 0.005, 3))))
    cal_results_settings_noise_slider.bind(
        "<ButtonRelease-1>",
        lambda e: cal_update_results(cal_confirmed_blur_radius, float(cal_results_noise_filter.get())))
    cal_results_settings_noise_slider.grid(padx=2, row=5, column=0, columnspan=2, sticky="ew")

    # Spinbox for the noise threshold
    cal_results_settings_noise_spinbox = ttk.Spinbox(
        cal_results_settings_frame, from_=-0.5, to=0.5, increment=0.005,
        wrap=True, textvariable=cal_results_noise_filter, width=6,
        command=lambda: cal_update_results(cal_confirmed_blur_radius, float(cal_results_noise_filter.get())),
        validate="key", validatecommand=vcmd_float)
    cal_results_settings_noise_spinbox.bind(
        "<FocusOut>",
        cal_results_noise_spinbox_update)
    cal_results_settings_noise_spinbox.bind(
        "<Return>",
        lambda e: root.focus())
    cal_results_settings_noise_spinbox.grid(padx=2, row=5, column=2, sticky="e")

    # Add previous and confirm button
    cal_results_previous_button = ttk.Button(
        master=cal_results_frame,
        text="Previous",
        width=20,
        command=lambda: go_to_previous_page("cal"))
    cal_results_save_button = ttk.Button(
        master=cal_results_frame,
        text="Save settings",
        width=20,
        command=cal_save_settings)
    cal_results_previous_button.grid(padx=10, pady=10, row=2, column=0, sticky="sw")
    cal_results_save_button.grid(padx=10, pady=10, row=2, column=1, sticky="se")

    # ==ANALYSIS==
    # Add analysis tabs
    analysis_side_tabs = ttk.Notebook(analysis_frame)
    analysis_side_tabs.pack(fill="both", expand=True)

    anl_select_frame = ttk.Frame(analysis_side_tabs)
    anl_settings_frame = ttk.Frame(analysis_side_tabs)
    anl_analysis_frame = ttk.Frame(analysis_side_tabs)
    anl_results_frame = ttk.Frame(analysis_side_tabs)
    anl_select_frame.pack(fill="both", expand=True)
    anl_settings_frame.pack(fill="both", expand=True)
    anl_analysis_frame.pack(fill="both", expand=True)
    anl_results_frame.pack(fill="both", expand=True)

    analysis_side_tabs.add(anl_select_frame, text=f'{"1. Select images":^25s}')
    analysis_side_tabs.add(anl_settings_frame, text=f'{"2. Select settings":^25s}')
    analysis_side_tabs.add(anl_analysis_frame, text=f'{"3. Analysis":^25s}')
    analysis_side_tabs.add(anl_results_frame, text=f'{"4. View Results":^25s}')
    analysis_side_tabs.tab(1, state="disabled")
    analysis_side_tabs.tab(2, state="disabled")
    analysis_side_tabs.tab(3, state="disabled")

    analysis_side_tabs.bind(
        "<<NotebookTabChanged>>",
        lambda e: update_current_tab("anl"))

    # Analysis variables
    # Global analysis variables
    anl_current_tab = 0
    anl_confirmed_files = []
    anl_confirmed_file_names = ()
    anl_processed_files = []
    anl_IJOQ_list = []
    anl_confirmed_channel = 0
    anl_confirmed_image_compression = 0
    anl_confirmed_blur_radius = 0
    anl_confirmed_section_number = 0
    anl_confirmed_pixel_number = 0
    anl_confirmed_normal_threshold = 0
    anl_confirmed_noise_filter = 0
    anl_confirmed_line_number = 0
    anl_current_viewed_picture = 0
    anl_has_uploaded_settings = False

    # File selection variables
    anl_input_files = []

    # Settings selection variables
    anl_channel_selection = 0
    anl_image_compression = 0
    anl_blur_radius = 0
    anl_section_number = 0
    anl_pixel_number = 0
    anl_normal_threshold = 0
    anl_noise_filter = 0
    anl_line_number = 0

    # ==ANALYSIS:SELECT IMAGE PAGE==
    # Add analysis frames
    # Frame for analysis file entry
    anl_select_frame.columnconfigure(0, weight=1)
    anl_select_frame.columnconfigure(1, weight=0)
    anl_select_frame.rowconfigure(0, weight=0)
    anl_select_frame.rowconfigure(1, weight=1)
    anl_select_frame.rowconfigure(2, weight=0)

    # Add description label to the top
    anl_file_description_label = ttk.Label(
        master=anl_select_frame,
        text="Calibration should be performed before IJOQ analysis.\n\n"
             "To begin IJOQ analysis, please select the images to be analyzed.\n"
             "All files located in folders that have \"Output\" in their names will be automatically excluded.")
    anl_file_description_label.bind(
        "<Configure>",
        lambda e, label=anl_file_description_label: label.config(wraplength=label.winfo_width()))
    anl_file_description_label.grid(padx=10, pady=10, row=0, column=0, columnspan=2, sticky="nsew")

    # Add center frames
    anl_file_list_frame = ttk.Frame(anl_select_frame)
    anl_file_options_frame = ttk.Frame(anl_select_frame)
    anl_file_list_frame.grid(padx=10, row=1, column=0, sticky="nsew")
    anl_file_options_frame.grid(row=1, column=1, sticky="nsew")

    # Add file list
    anl_file_list_frame.columnconfigure(0, weight=1)
    anl_file_list_frame.columnconfigure(1, weight=0)
    anl_file_list_frame.rowconfigure(0, weight=0)
    anl_file_list_frame.rowconfigure(1, weight=1)

    anl_file_list_label = ttk.Label(master=anl_file_list_frame, text="Selected files:")
    anl_file_list_box = tkinter.Listbox(master=anl_file_list_frame)
    anl_file_list_scrollbar = ttk.Scrollbar(master=anl_file_list_frame, orient="vertical")
    anl_file_list_box.config(yscrollcommand=anl_file_list_scrollbar.set)
    anl_file_list_scrollbar.config(command=anl_file_list_box.yview)
    anl_file_list_label.grid(row=0, column=0, sticky="nsew")
    anl_file_list_box.grid(row=1, column=0, sticky="nsew")
    anl_file_list_scrollbar.grid(row=1, column=1, sticky="ns")

    # Add file options
    anl_file_add_button = ttk.Button(
        master=anl_file_options_frame, text="Add file",
        command=lambda: add_file("anl"))
    anl_folder_add_button = ttk.Button(
        master=anl_file_options_frame, text="Add folder",
        command=lambda: add_folder("anl"))
    anl_file_delete_button = ttk.Button(
        master=anl_file_options_frame, text="Delete selection",
        command=lambda: del_file("anl"))
    anl_file_clear_button = ttk.Button(
        master=anl_file_options_frame, text="Clear all",
        command=lambda: clear_file("anl"))
    anl_file_add_button.pack(padx=10, pady=2, fill="both")
    anl_folder_add_button.pack(padx=10, pady=2, fill="both")
    anl_file_delete_button.pack(padx=10, pady=2, fill="both")
    anl_file_clear_button.pack(padx=10, pady=2, fill="both")

    # Add lower button
    anl_file_select_button = ttk.Button(
        master=anl_select_frame,
        text="Confirm selection",
        width=20,
        state="disabled",
        command=lambda: confirm_files("anl"))
    anl_file_select_button.grid(padx=10, pady=10, row=2, column=1, sticky="se")

    # ==ANALYSIS:SETTINGS PAGE==
    anl_settings_frame.columnconfigure(0, weight=0)
    anl_settings_frame.columnconfigure(1, weight=1)
    anl_settings_frame.columnconfigure(2, weight=0)
    anl_settings_frame.rowconfigure(0, weight=1)
    anl_settings_frame.rowconfigure(1, weight=0)
    anl_settings_frame.rowconfigure(2, weight=2)
    anl_settings_frame.rowconfigure(3, weight=0)

    # Description for the settings
    anl_settings_description_label = ttk.Label(
        master=anl_settings_frame,
        text="Please upload the settings file obtained from calibration.",
        anchor=tkinter.NW)
    anl_settings_description_label.grid(padx=10, pady=10, row=0, column=0, columnspan=3, sticky="nsew")

    # Parameter label for the settings
    anl_settings_label = ttk.Label(
        master=anl_settings_frame,
        text="Parameters:")
    anl_settings_label.grid(padx=10, row=1, column=0, sticky="nsew")
    anl_settings_parameter_labels = ttk.Label(
        master=anl_settings_frame,
        text="Image compression: \n"
             "Color channel: \n"
             "Blur radius: \n"
             "Number of sections: \n"
             "Number of pixels: \n"
             "Normalization threshold: \n"
             "Noise filter: \n"
             "Number of lines: \n",
        anchor=tkinter.NW,
        justify=tkinter.LEFT)
    anl_settings_parameter_labels.grid(padx=10, pady=2, row=2, column=0, sticky="nsew")

    # Parameter value label for the settings
    anl_settings_value_label = ttk.Label(
        master=anl_settings_frame,
        anchor=tkinter.NW, width=20,
        justify=tkinter.LEFT)
    anl_settings_value_label.grid(pady=2, row=2, column=1, sticky="nsew")

    # Add settings file button
    anl_add_settings_button = ttk.Button(
        master=anl_settings_frame, text="Upload settings",
        command=anl_add_settings)
    anl_add_settings_button.grid(padx=10, row=1, rowspan=2, column=2, sticky="new")

    # Add previous and confirm button
    anl_settings_previous_button = ttk.Button(
        master=anl_settings_frame,
        text="Previous",
        width=20,
        command=lambda: go_to_previous_page("anl"))
    anl_settings_confirm_button = ttk.Button(
        master=anl_settings_frame,
        text="Run analysis",
        width=20,
        state="disabled",
        command=anl_go_to_analysis)
    anl_settings_previous_button.grid(padx=10, pady=10, row=3, column=0, sticky="sw")
    anl_settings_confirm_button.grid(padx=10, pady=10, row=3, column=2, sticky="se")

    # ==ANALYSIS:ANALYSIS PAGE==
    anl_analysis_frame.columnconfigure(0, weight=1)
    anl_analysis_frame.columnconfigure(1, weight=1)
    anl_analysis_frame.rowconfigure(0, weight=0)
    anl_analysis_frame.rowconfigure(1, weight=1)
    anl_analysis_frame.rowconfigure(2, weight=0)

    # Add a progress bar
    anl_analysis_progress_bar = ttk.Progressbar(
        master=anl_analysis_frame,
        orient="horizontal",
        mode='determinate')
    anl_analysis_progress_bar.grid(padx=10, pady=10, row=0, column=0, columnspan=2, sticky="ew")

    # Add a frame for text box and scrollbar
    anl_analysis_text_frame = ttk.Frame(anl_analysis_frame)
    anl_analysis_text_frame.grid(padx=10, pady=0, row=1, column=0, columnspan=2, sticky="nsew")

    anl_analysis_text_frame.columnconfigure(0, weight=1)
    anl_analysis_text_frame.columnconfigure(1, weight=0)
    anl_analysis_text_frame.rowconfigure(0, weight=1)

    # Add scroll bar for text box
    anl_analysis_textbox = tkinter.Text(anl_analysis_text_frame)
    anl_analysis_textbox.bind(
        "<Key>",
        lambda e: "break")
    anl_analysis_text_scrollbar = ttk.Scrollbar(master=anl_analysis_text_frame, orient="vertical")
    anl_analysis_textbox.config(yscrollcommand=anl_analysis_text_scrollbar.set)
    anl_analysis_text_scrollbar.config(command=anl_analysis_textbox.yview)
    anl_analysis_textbox.grid(row=0, column=0, sticky="nsew")
    anl_analysis_text_scrollbar.grid(row=0, column=1, sticky="ns")

    # Add previous and confirm button
    anl_analysis_previous_button = ttk.Button(
        master=anl_analysis_frame,
        text="Previous",
        width=20,
        state="disabled",
        command=lambda: go_to_previous_page("anl"))
    anl_analysis_confirm_button = ttk.Button(
        master=anl_analysis_frame,
        text="Show result",
        width=20,
        state="disabled",
        command=lambda: analysis_side_tabs.select(3))
    anl_analysis_previous_button.grid(padx=10, pady=10, row=2, column=0, sticky="sw")
    anl_analysis_confirm_button.grid(padx=10, pady=10, row=2, column=1, sticky="se")

    # ==ANALYSIS:RESULTS PAGE==
    anl_results_frame.columnconfigure(0, weight=1)
    anl_results_frame.columnconfigure(1, weight=0)
    anl_results_frame.rowconfigure(0, weight=0)
    anl_results_frame.rowconfigure(1, weight=1)
    anl_results_frame.rowconfigure(2, weight=0)

    # Add description label
    anl_results_description_label = ttk.Label(
        master=anl_results_frame,
        text="Please review the processed images and ensure that the program is "
             "adequately thresholding the images before saving the results.")
    anl_results_description_label.bind(
        "<Configure>",
        lambda e, label=anl_results_description_label: label.config(wraplength=label.winfo_width()))
    anl_results_description_label.grid(padx=10, pady=10, row=0, column=0, sticky="new")

    # Frame for picture
    anl_results_picture_frame = ttk.Frame(anl_results_frame)
    anl_results_picture_frame.grid(padx=10, pady=5, row=1, column=0, columnspan=2, sticky="nsew")
    anl_results_picture_frame.columnconfigure(0, weight=1)
    anl_results_picture_frame.columnconfigure(1, weight=3)
    anl_results_picture_frame.columnconfigure(2, weight=1)
    anl_results_picture_frame.rowconfigure(0, weight=1)

    # Arrows for picture
    anl_results_picture_left_arrow_button = ttk.Button(
        master=anl_results_picture_frame,
        text="←",
        width=3,
        command=lambda: results_go_to_picture(anl_current_viewed_picture - 1, "anl")
    )
    anl_results_picture_right_arrow_button = ttk.Button(
        master=anl_results_picture_frame,
        text="→",
        width=3,
        command=lambda: results_go_to_picture(anl_current_viewed_picture + 1, "anl")
    )
    anl_results_picture_left_arrow_button.grid(row=0, column=0, sticky="e")
    anl_results_picture_right_arrow_button.grid(row=0, column=2, sticky="w")

    # Textbox for Picture
    anl_results_picture_label = ttk.Label(anl_results_picture_frame, compound=tkinter.TOP, anchor=tkinter.CENTER)
    anl_results_picture_label.grid(row=0, column=1, sticky="nsew")
    anl_results_picture_label.bind(
        "<Configure>",
        lambda e: draw_results_image(anl_current_viewed_picture, "anl"))

    # Add previous and confirm button
    anl_results_previous_button = ttk.Button(
        master=anl_results_frame,
        text="Previous",
        width=20,
        command=lambda: go_to_previous_page("anl"))
    anl_results_save_button = ttk.Button(
        master=anl_results_frame,
        text="Save results",
        width=20,
        command=anl_save_results)
    anl_results_previous_button.grid(padx=10, pady=10, row=2, column=0, sticky="sw")
    anl_results_save_button.grid(padx=10, pady=10, row=2, column=1, sticky="se")


    root.mainloop()
