from math import floor
import tkinter
from threading import Thread
from PIL import Image, ImageFilter, ImageTk
import numpy

class Calculations:

    def __init__(self, calculation_type, parent):
        """
        Creates the variables necessary for calibration or analysis
        :calculation_type: "calibration" or "analysis"
        """

        self.type = calculation_type

        # TODO: Kind of a cop-out... Rework later to better integrate the GUI and the backend calculations
        self.parent = parent

        # Variables used for both calibration and analysis
        self.current_tab = 0
        self.confirmed_files = []
        self.confirmed_file_names = ()
        self.processed_files = []
        self.confirmed_channel = 0
        self.confirmed_image_compression = 0
        self.confirmed_blur_radius = 0
        self.confirmed_section_number = 0
        self.confirmed_pixel_number = 0
        self.confirmed_normal_threshold = 0
        self.confirmed_noise_filter = 0
        self.confirmed_line_number = 0
        self.current_viewed_picture = 0
        self.input_files = []
        self.minimum_files = 3 if self.type == "calculation" else 1

        # Variables used for only calibration
        if self.type == "calibration":
            self.blurred_images = []
            self.normalization_thresholds = []
            self.brightness_maps = []
            self.noise_filter_threads = []

            # GUI-related settings selection variables (used in calibration
            # TODO: Figure out why I made all of these StringVars instead of IntVar or DoubleVar
            self.cell_number_x = tkinter.StringVar()
            self.cell_number_x.set("0")
            self.cell_number_y = tkinter.StringVar()
            self.cell_number_y.set("0")
            self.channel_options = ("Red", "Green", "Blue", "White")
            self.channel_selection = tkinter.StringVar()
            self.image_compression = tkinter.StringVar()
            self.image_compression.set("512")
            self.blur_radius = tkinter.StringVar()
            self.blur_radius.set("4")
            self.section_number = tkinter.StringVar()
            self.section_number.set("4")
            self.pixel_number = tkinter.StringVar()
            self.pixel_number.set("8")
            self.noise_filter = tkinter.StringVar()
            self.noise_filter.set("0.1")
            self.line_number = tkinter.StringVar()
            self.line_number.set("10")
            self.results_blur_radius = tkinter.StringVar()
            self.results_noise_filter = tkinter.StringVar()

        # Variables used for only analysis
        else:
            self.IJOQ_list = []
            self.has_uploaded_settings = False
            self.channel_selection = 0
            self.image_compression = 0
            self.blur_radius = 0
            self.section_number = 0
            self.pixel_number = 0
            self.normal_threshold = 0
            self.noise_filter = 0
            self.line_number = 0

    def calculate_threshold(self, x, y, section_count, threshold_array, section_width, section_height):
        """
        Calculates the threshold value for a given pixel
        :param x: x-coordinate of the pixel (left to right)
        :param y: y-coordinate of the pixel (top to bottom)
        :param section_count: The number of sections that the image is split into along a single axis
        :param threshold_array: A 2D array containing the calculated thresholds for each bin
        :param section_width: Width (in pixels) of a bin
        :param section_height: Height (in pixels) of a bin
        :return: Brightness (out of 255) of the threshold
        """
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

    def go_to_calibration(self):
        """
        Sets the input variables for the calibration, sets the progress bar, and starts a thread to run the calibration
        :return: None
        """

        # Check for existing noise filter calculation threads. If previous threads exist, prompt them to stop
        if self.noise_filter_threads:
            for thread in self.noise_filter_threads:
                thread.stop = True

            # Wait for threads to stop before continuing
            for thread in self.noise_filter_threads:
                thread.join()

        # Determine settings
        # If using basic settings
        if self.parent.calibration_tab.cal_settings_options_tabs.index("current") == 0:
            average_cell_count = (int(self.cell_number_x.get()) + int(self.cell_number_y.get())) / 2
            if average_cell_count > 50:
                self.confirmed_image_compression = 1024
                self.confirmed_section_number = 6
            else:
                self.confirmed_image_compression = 512
                self.confirmed_section_number = 4

            if self.channel_selection.get() == "Red":
                self.confirmed_channel = 0
            elif self.channel_selection.get() == "Green":
                self.confirmed_channel = 1
            elif self.channel_selection.get() == "Blue":
                self.confirmed_channel = 2
            elif self.channel_selection.get() == "White":
                self.confirmed_channel = 1

            # TODO: Why is blur radius set to negative average cell count?
            self.confirmed_blur_radius = -average_cell_count
            self.confirmed_pixel_number = 8
            self.confirmed_noise_filter = -1
            self.confirmed_line_number = max(10, int(round(average_cell_count, -1)))
        else:  # If using advanced settings
            self.confirmed_image_compression = int(self.image_compression.get())
            if self.channel_selection.get() == "Red":
                self.confirmed_channel = 0
            elif self.channel_selection.get() == "Green":
                self.confirmed_channel = 1
            elif self.channel_selection.get() == "Blue":
                self.confirmed_channel = 2
            elif self.channel_selection.get() == "White":
                self.confirmed_channel = 1
            self.confirmed_blur_radius = int(self.blur_radius.get())
            self.confirmed_section_number = int(self.section_number.get())
            self.confirmed_pixel_number = int(self.pixel_number.get())
            self.confirmed_noise_filter = float(self.noise_filter.get())
            self.confirmed_line_number = int(self.line_number.get())

        # Set progress bar to 0, delete text in textbox, and clear results
        self.blurred_images = []
        self.normalization_thresholds = []
        self.brightness_maps = []
        self.processed_files = []
        progress_bar_maximum = (len(self.confirmed_files) * (13 + (12 * (self.confirmed_section_number ** 2)))) + 6
        self.parent.calibration_tab.calculation_progress_bar.config(maximum=progress_bar_maximum)
        self.parent.calibration_tab.calculation_progress_bar["value"] = 0
        self.parent.calibration_tab.calculation_textbox.delete(1.0, tkinter.END)

        # Move to the calibration screen
        self.parent.calibration_tab.sub_tabs.tab(2, state="normal")
        self.parent.calibration_tab.sub_tabs.select(2)

        # Disable other tabs
        self.parent.calibration_tab.sub_tabs.tab(0, state="disabled")
        self.parent.calibration_tab.sub_tabs.tab(1, state="disabled")
        self.parent.calibration_tab.sub_tabs.tab(3, state="disabled")
        self.parent.calibration_tab.calculation_previous_button["state"] = "disabled"
        self.parent.calibration_tab.calculation_confirm_button["state"] = "disabled"

        calibration_thread = Thread(target=self.run_calibration, daemon=True)
        calibration_thread.start()

    def run_calibration(self):
        """
        Runs the calibration. Should be run as a thread, otherwise the GUI won't update properly
        :return: None
        """

        # Run calibration
        self.parent.calibration_tab.calculation_textbox.insert(tkinter.END, "Determining ideal normalization threshold value...")
        self.parent.calibration_tab.calculation_textbox.see(tkinter.END)

        # Run the following code for each file
        brightness_deviation_list = []
        threshold_list = []
        for file_number in range(len(self.confirmed_files)):
            image_name = self.confirmed_file_names[file_number]
            try:
                image = Image.open(self.confirmed_files[file_number])
                width, height = image.size
                compression_amount = (self.confirmed_image_compression / 2) * (width + height) / (width * height)
                image = image.resize((round(compression_amount * width), round(compression_amount * height)))
                width, height = image.size

                # Take the RGB values from all the pixels in the image as an array
                image_array = numpy.array(image.convert("RGB"))

                # Extract channel
                self.parent.calibration_tab.calculation_textbox.insert(tkinter.END, f"\n\nExtracting channel from {image_name}...")
                self.parent.calibration_tab.calculation_textbox.see(tkinter.END)
                for x in range(width):
                    for y in range(height):
                        image_array[y][x] = [image_array[y][x][self.confirmed_channel]] * 3

                if self.confirmed_blur_radius < 0:
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
                self.parent.calibration_tab.calculation_textbox.insert(tkinter.END, f"\nApplying blur to {image_name}...")
                self.parent.calibration_tab.calculation_textbox.see(tkinter.END)
                image = Image.fromarray(image_array.astype("uint8"))
                blur_radius_values = (0, 1, 2, 3, 4, 5)
                current_blurred_image_list = []
                for blur_radius_value in blur_radius_values:
                    blurred_image = image.filter(ImageFilter.GaussianBlur(radius=blur_radius_value))
                    current_blurred_image_list.append(blurred_image)
                    self.parent.calibration_tab.calculation_progress_bar["value"] += 1
                self.blurred_images.append(current_blurred_image_list)

                # Calculate threshold value for each individual blurred image
                self.parent.calibration_tab.calculation_textbox.insert(tkinter.END, f"\nCalculating threshold values for {image_name}...")
                self.parent.calibration_tab.calculation_textbox.see(tkinter.END)
                current_threshold_list = []
                for blurred_image in current_blurred_image_list:
                    image_array = numpy.array(blurred_image.convert("HSV"))

                    # Split the picture into sections
                    section_width = width / self.confirmed_section_number
                    section_height = height / self.confirmed_section_number

                    white_pixel_counter = 0
                    for section_x in range(self.confirmed_section_number):
                        for section_y in range(self.confirmed_section_number):
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
                                    variance = prob_zero * prob_one * ((mean_zero - mean_one) ** 2)

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
                            self.parent.calibration_tab.calculation_progress_bar["value"] += 1

                    # Determine normalization threshold
                    white_percent = white_pixel_counter / (width * height)

                    threshold = numpy.ceil((1 - white_percent) * (self.confirmed_pixel_number ** 2))
                    current_threshold_list.append(threshold)

                threshold_list.append(current_threshold_list)

            # File could not be opened
            except FileNotFoundError:
                # Print warning, re-enable file selection and settings, then stop function
                self.parent.calibration_tab.calculation_textbox.insert(
                    tkinter.END, f"\n\nWARNING! Unable to find file for {image_name}!")
                self.parent.calibration_tab.calculation_textbox.see(tkinter.END)

                self.parent.calibration_tab.sub_tabs.tab(0, state="normal")
                self.parent.calibration_tab.sub_tabs.tab(1, state="normal")
                self.parent.calibration_tab.calculation_previous_button["state"] = "normal"

                return

        # Take geometric mean of thresholds
        for i in range(6):
            product = 1
            for j in range(len(threshold_list)):
                product *= threshold_list[j][i]

            average_threshold = round(product ** (1 / len(threshold_list)))
            self.normalization_thresholds.append(average_threshold)

            self.parent.calibration_tab.calculation_progress_bar["value"] += 1

        self.parent.calibration_tab.calculation_textbox.insert(tkinter.END, f"\n\nPreparing brightness maps...\n")
        self.parent.calibration_tab.calculation_textbox.see(tkinter.END)
        for i in range(len(self.confirmed_files)):
            image_name = self.confirmed_file_names[i]

            self.parent.calibration_tab.calculation_textbox.insert(tkinter.END, f"\nCalculating brightness map for {image_name}...")
            self.parent.calibration_tab.calculation_textbox.see(tkinter.END)
            current_brightness_map_list = []
            for j in range(len(self.blurred_images[i])):
                width, height = self.blurred_images[i][j].size
                image_array = numpy.array(self.blurred_images[i][j].convert("HSV"))

                # Split the picture into sections
                section_width = width / self.confirmed_section_number
                section_height = height / self.confirmed_section_number
                normalization_threshold_array = numpy.zeros(
                    (self.confirmed_section_number, self.confirmed_section_number))

                # For each section, sample pixels, then find the normalization threshold
                for section_x in range(self.confirmed_section_number):
                    for section_y in range(self.confirmed_section_number):

                        sampled_values = []
                        for x in range(self.confirmed_pixel_number):
                            for y in range(self.confirmed_pixel_number):
                                pixel_x = round(
                                    section_width * (section_x + ((x + 0.5) / self.confirmed_pixel_number)))
                                pixel_y = round(
                                    section_height * (section_y + ((y + 0.5) / self.confirmed_pixel_number)))

                                sampled_values.append(image_array[pixel_y][pixel_x][2])

                        sampled_values.sort()
                        normalization_threshold_array[section_x][section_y] = \
                            sampled_values[self.normalization_thresholds[j] - 1]
                        self.parent.calibration_tab.calculation_progress_bar["value"] += 1

                # Parse through the image array and calculate brightness map
                brightness_map = numpy.zeros((height, width))
                for x in range(width):
                    for y in range(height):
                        brightness_map[y][x] = self.calculate_threshold(
                            x, y,
                            self.confirmed_section_number,
                            normalization_threshold_array,
                            section_width, section_height)
                current_brightness_map_list.append(brightness_map)
                self.parent.calibration_tab.calculation_progress_bar["value"] += 1

            self.brightness_maps.append(current_brightness_map_list)

        # Take average of brightness deviations and set as blur radius
        if self.confirmed_blur_radius < 0:
            average_brightness_deviation = sum(brightness_deviation_list) / len(brightness_deviation_list)
            self.confirmed_blur_radius = \
                max(min(round(25 * average_brightness_deviation / ((-self.confirmed_blur_radius) ** 2.5)), 5), 1)

        # Calculate noise filter

        current_blur_number = self.confirmed_blur_radius
        if self.confirmed_noise_filter == -1:
            brightness_deviation_list = []
            for i in range(len(self.confirmed_files)):

                width, height = self.blurred_images[i][current_blur_number].size
                image_array = numpy.array(self.blurred_images[i][current_blur_number].convert("HSV"))

                # Calculate difference in brightness between local minima/maxima
                # TODO: Dividing local maxima by local minima seems funky and can lead to divide-by-zero errors. Check if this is really the intention
                # Currently doing workaround to set local minimum to 1 if it's 0
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
                            local_minimum = max(int(image_array[y][round(width / 2)][2]), 1)
                        else:
                            local_maximum = image_array[y][round(width / 2)][2]
                    else:
                        if image_array[y][round(width / 2)][2] > 1.05 * local_minimum:
                            increasing = True
                            difference = (local_maximum / local_minimum) - 1
                            brightness_deviation.append(difference)
                            local_maximum = image_array[y][round(width / 2)][2]
                        else:
                            local_minimum = max(int(image_array[y][round(width / 2)][2]), 1)

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
                            local_minimum = max(int(image_array[round(height / 2)][x][2]), 1)
                        else:
                            local_maximum = image_array[round(height / 2)][x][2]
                    else:
                        if image_array[round(height / 2)][x][2] > 1.05 * local_minimum:
                            increasing = True
                            difference = (local_maximum / local_minimum) - 1
                            brightness_deviation.append(difference)
                            local_maximum = image_array[round(height / 2)][x][2]
                        else:
                            local_minimum = max(int(image_array[round(height / 2)][x][2]), 1)

                if brightness_deviation:
                    brightness_deviation.sort()
                    median = brightness_deviation[round(len(brightness_deviation) / 2)]
                    brightness_deviation_list.append(median)
                else:
                    brightness_deviation_list.append(0)

            average_brightness_deviation = sum(brightness_deviation_list) / len(brightness_deviation_list)
            self.confirmed_noise_filter = \
                max(min(round(round((average_brightness_deviation / 10) / 0.05) * 0.05, 2), 0.5), 0)

        self.parent.calibration_tab.calculation_textbox.insert(tkinter.END, f"\n\nPreparing output images...\n")
        self.parent.calibration_tab.calculation_textbox.see(tkinter.END)
        for i in range(len(self.confirmed_files)):
            image_name = self.confirmed_file_names[i]

            self.parent.calibration_tab.calculation_textbox.insert(tkinter.END, f"\nNormalizing {image_name}...")
            self.parent.calibration_tab.calculation_textbox.see(tkinter.END)
            width, height = self.blurred_images[i][current_blur_number].size
            image_array = numpy.array(self.blurred_images[i][current_blur_number].convert("HSV"))

            # Normalize image using calculated brightness map
            normalized_image_array = self.normalize_image(
                image_array,
                self.brightness_maps[i][current_blur_number],
                width, height,
                self.confirmed_noise_filter)

            normalized_image = Image.fromarray(normalized_image_array.astype("uint8"), "HSV").convert("RGB")
            self.processed_files.append(normalized_image)
            self.parent.calibration_tab.calculation_progress_bar["value"] += 1

        self.parent.calibration_tab.calculation_textbox.insert(
            tkinter.END,
            "\n\nCalibration complete! Press the \"Show result\" button to view calibration results.")
        self.parent.calibration_tab.calculation_textbox.see(tkinter.END)

        # Update results tab with new results
        self.confirmed_normal_threshold = self.normalization_thresholds[current_blur_number]
        self.parent.calibration_tab.results_go_to_picture(0)
        self.parent.calibration_tab.cal_results_settings_value_label.config(
            text=f"{self.confirmed_image_compression}\n"
                 f"{self.confirmed_channel}\n"
                 f"{self.confirmed_blur_radius}\n"
                 f"{self.confirmed_section_number}\n"
                 f"{self.confirmed_pixel_number}\n"
                 f"{self.confirmed_normal_threshold}\n"
                 f"{self.confirmed_noise_filter}\n"
                 f"{self.confirmed_line_number}")
        self.results_blur_radius.set(str(self.confirmed_blur_radius))
        self.results_noise_filter.set(str(self.confirmed_noise_filter))

        # Re-enable tabs at the conclusion of calibration, then enable the next and previous buttons
        self.parent.calibration_tab.sub_tabs.tab(0, state="normal")
        self.parent.calibration_tab.sub_tabs.tab(1, state="normal")
        self.parent.calibration_tab.sub_tabs.tab(3, state="normal")
        self.parent.calibration_tab.calculation_previous_button["state"] = "normal"
        self.parent.calibration_tab.calculation_confirm_button["state"] = "normal"

    def normalize_image(self, pixel_array, brightness_map, width, height, noise_threshold):
        """
        Passes an image through a threshold to produce the final processed image
        :param pixel_array: 3D array containing the HSV values of the pixels in a pre-blurred image
        :param brightness_map: 2D array containing all pixel threshold values
        :param width: Width (in pixels) of the image
        :param height: Height (in pixels) of the image
        :param noise_threshold: Arbitrary value added on top of the brightness threshold value to account for noise
        :return: 3D array containing the HSV values of the pixels after thresholding
        """
        for x in range(width):
            for y in range(height):
                pixel_brightness = pixel_array[y][x][2]

                if pixel_brightness > max(brightness_map[y][x] * (1 + noise_threshold), 20):
                    pixel_array[y][x][2] = 255
                else:
                    pixel_array[y][x][2] = 0

        return pixel_array

    def go_to_analysis(self):
        """
        Sets the input variables for the analysis, sets the progress bar, and starts a thread to run the calibration
        :return: None
        """

        # Determine settings
        self.confirmed_image_compression = self.image_compression
        self.confirmed_channel = self.channel_selection
        self.confirmed_blur_radius = self.blur_radius
        self.confirmed_section_number = self.section_number
        self.confirmed_pixel_number = self.pixel_number
        self.confirmed_normal_threshold = self.normal_threshold
        self.confirmed_noise_filter = self.noise_filter
        self.confirmed_line_number = self.line_number

        # Set progress bar to 0, delete text in textbox, and clear results
        self.processed_files = []
        self.IJOQ_list = []
        progress_bar_maximum = len(self.confirmed_files) * (6 + (self.confirmed_section_number ** 2))
        self.parent.analysis_tab.calculation_progress_bar.config(maximum=progress_bar_maximum)
        self.parent.analysis_tab.calculation_progress_bar["value"] = 0
        self.parent.analysis_tab.calculation_textbox.delete(1.0, tkinter.END)

        # Move to the analysis screen
        self.parent.analysis_tab.sub_tabs.tab(2, state="normal")
        self.parent.analysis_tab.sub_tabs.select(2)

        # Disable other tabs
        self.parent.analysis_tab.sub_tabs.tab(0, state="disabled")
        self.parent.analysis_tab.sub_tabs.tab(1, state="disabled")
        self.parent.analysis_tab.sub_tabs.tab(3, state="disabled")
        self.parent.analysis_tab.calculation_previous_button["state"] = "disabled"
        self.parent.analysis_tab.calculation_confirm_button["state"] = "disabled"

        analysis_thread = Thread(target=self.run_analysis, daemon=True)
        analysis_thread.start()

    def run_analysis(self):
        """
        Runs the analysis. Should be run as a thread, otherwise the GUI won't update properly
        :return: None
        """

        # Run analysis
        for file in self.confirmed_files:
            # Determine the image name
            image_name = file.split("/")[-1]

            try:
                self.parent.analysis_tab.calculation_textbox.insert(tkinter.END, f"Analyzing {image_name}...")
                self.parent.analysis_tab.calculation_textbox.see(tkinter.END)

                image = Image.open(file)
                width, height = image.size
                compression_amount = (self.confirmed_image_compression / 2) * (width + height) / (width * height)
                image = image.resize((round(compression_amount * width), round(compression_amount * height)))
                width, height = image.size

                # Take the RGB values from all the pixels in the image as an array
                image_array = numpy.array(image.convert("RGB"))

                # Extract channel
                self.parent.analysis_tab.calculation_textbox.insert(tkinter.END, f"\nExtracting channel from {image_name}...")
                self.parent.analysis_tab.calculation_textbox.see(tkinter.END)
                for x in range(width):
                    for y in range(height):
                        image_array[y][x] = [image_array[y][x][self.confirmed_channel]] * 3

                # Apply blur
                self.parent.analysis_tab.calculation_textbox.insert(tkinter.END, f"\nApplying blur to {image_name}...")
                self.parent.analysis_tab.calculation_textbox.see(tkinter.END)
                image = Image.fromarray(image_array.astype("uint8"))
                blurred_image = image.filter(ImageFilter.GaussianBlur(radius=self.confirmed_blur_radius))
                image_array = numpy.array(blurred_image.convert("HSV"))
                self.parent.analysis_tab.calculation_progress_bar["value"] += 1

                # Split the picture into sections
                self.parent.analysis_tab.calculation_textbox.insert(tkinter.END, f"\nCalculating threshold values for {image_name}...")
                self.parent.analysis_tab.calculation_textbox.see(tkinter.END)
                section_width = width / self.confirmed_section_number
                section_height = height / self.confirmed_section_number
                normalization_threshold_array = numpy.zeros(
                    (self.confirmed_section_number, self.confirmed_section_number))

                # For each section, sample pixels, then find the normalization threshold
                for section_x in range(self.confirmed_section_number):
                    for section_y in range(self.confirmed_section_number):

                        sampled_values = []
                        for x in range(self.confirmed_pixel_number):
                            for y in range(self.confirmed_pixel_number):
                                pixel_x = round(
                                    section_width * (section_x + ((x + 0.5) / self.confirmed_pixel_number)))
                                pixel_y = round(
                                    section_height * (section_y + ((y + 0.5) / self.confirmed_pixel_number)))

                                sampled_values.append(image_array[pixel_y][pixel_x][2])

                        sampled_values.sort()
                        normalization_threshold_array[section_x][section_y] = \
                            sampled_values[self.confirmed_normal_threshold - 1]
                        self.parent.analysis_tab.calculation_progress_bar["value"] += 1

                # Parse through the image array and calculate brightness map
                self.parent.analysis_tab.calculation_textbox.insert(tkinter.END, f"\nCalculating brightness map for {image_name}...")
                self.parent.analysis_tab.calculation_textbox.see(tkinter.END)
                brightness_map = numpy.zeros((height, width))
                for x in range(width):
                    for y in range(height):
                        brightness_map[y][x] = self.calculate_threshold(
                            x, y,
                            self.confirmed_section_number,
                            normalization_threshold_array,
                            section_width, section_height)
                self.parent.analysis_tab.calculation_progress_bar["value"] += 1

                # Normalize image using calculated brightness map
                normalized_image_array = self.normalize_image(
                    image_array,
                    brightness_map,
                    width, height,
                    self.confirmed_noise_filter)
                normalized_image = Image.fromarray(normalized_image_array.astype("uint8"), "HSV").convert("RGB")
                self.processed_files.append(normalized_image)
                self.parent.analysis_tab.calculation_progress_bar["value"] += 1

                # Draw horizontal lines
                self.parent.analysis_tab.calculation_textbox.insert(tkinter.END, f"\nCalculating IJOQ for {image_name}...")
                self.parent.analysis_tab.calculation_textbox.see(tkinter.END)
                cell_border_frequency = 0
                for y in range(self.confirmed_line_number):
                    pixel_y = round((y + 0.5) * height / self.confirmed_line_number)

                    previous_pixel = image_array[pixel_y][0][2]
                    for x in range(1, width):
                        current_pixel = image_array[pixel_y][x][2]
                        # If the line detects a color change (i.e. black to white or white to black)
                        if not previous_pixel == current_pixel:
                            cell_border_frequency += 0.5 / width

                        # Set current pixel as the previous pixel before moving to the next pixel
                        previous_pixel = current_pixel

                # Increment progress bar
                self.parent.analysis_tab.calculation_progress_bar["value"] += 1

                # Repeat the same steps vertical lines
                for x in range(self.confirmed_line_number):
                    pixel_x = round((x + 0.5) * width / self.confirmed_line_number)

                    previous_pixel = image_array[0][pixel_x][2]
                    for y in range(1, height):
                        current_pixel = image_array[y][pixel_x][2]
                        if not previous_pixel == current_pixel:
                            cell_border_frequency += 0.5 / height

                        # Set current pixel as the previous pixel before moving to the next pixel
                        previous_pixel = current_pixel

                # Increment progress bar
                self.parent.analysis_tab.calculation_progress_bar["value"] += 1

                # Take average of all lines
                IJOQ = round(cell_border_frequency / (2 * self.confirmed_line_number), 4)
                self.parent.analysis_tab.calculation_textbox.insert(tkinter.END, f"\n{image_name} has an IJOQ value of {IJOQ}.\n\n")
                self.parent.analysis_tab.calculation_textbox.see(tkinter.END)
                self.IJOQ_list.append(IJOQ)
                self.parent.analysis_tab.calculation_progress_bar["value"] += 1

            # File could not be opened
            except FileNotFoundError:
                # Print warning, re-enable file selection and settings, then stop function
                self.parent.analysis_tab.calculation_textbox.insert(
                    tkinter.END, f"WARNING! Unable to find file for {image_name}!")
                self.parent.analysis_tab.calculation_textbox.see(tkinter.END)

                self.parent.analysis_tab.sub_tabs.tab(0, state="normal")
                self.parent.analysis_tab.sub_tabs.tab(1, state="normal")
                self.parent.analysis_tab.calculation_previous_button["state"] = "normal"

                return

        self.parent.analysis_tab.calculation_textbox.insert(
            tkinter.END,
            "Analysis complete! Press the \"Show result\" button to view analysis results.")
        self.parent.analysis_tab.calculation_textbox.see(tkinter.END)

        # Update results tab with new results
        self.parent.analysis_tab.results_go_to_picture(0)

        # Re-enable tabs at the conclusion of calibration, then enable the next and previous buttons
        self.parent.analysis_tab.sub_tabs.tab(0, state="normal")
        self.parent.analysis_tab.sub_tabs.tab(1, state="normal")
        self.parent.analysis_tab.sub_tabs.tab(3, state="normal")
        self.parent.analysis_tab.calculation_previous_button["state"] = "normal"
        self.parent.analysis_tab.calculation_confirm_button["state"] = "normal"

class NoiseCalculationThread(Thread):
    """
    Starts a thread for updating the calibration results when the blur/noise options are changed
    """

    def __init__(self, parent, calibration):
        Thread.__init__(self)
        self.parent = parent
        self.calibration = calibration
        self.stop = False
        self.current_file = 0 # TODO: Set as self.parent.cal_current_viewed_picture?
        self.update_order = []

    def run(self):
        """
        Updates the images in the cal_processed_files list according to the current blur/noise settings
        :return: None
        """

        # Save current image number
        self.current_file = self.calibration.current_viewed_picture
        blur_number = self.calibration.confirmed_blur_radius

        # Determine update order (current image first, then nearby images, etc.)
        above_images_count = len(self.calibration.processed_files) - self.current_file - 1
        below_images_count = self.current_file

        for i in range(1, max(above_images_count, below_images_count) + 1):
            if i <= below_images_count:
                self.update_order.append(self.current_file - i)
            if i <= above_images_count:
                self.update_order.append(self.current_file + i)

        # Calculate current image first
        blurred_image = self.calibration.blurred_images[self.current_file][blur_number]
        brightness_map = self.calibration.brightness_maps[self.current_file][blur_number]
        width, height = blurred_image.size

        image_array = numpy.array(blurred_image.convert("HSV"))
        normalized_image_array = self.calibration.normalize_image(
            image_array,
            brightness_map,
            width, height,
            self.calibration.confirmed_noise_filter)
        normalized_image = Image.fromarray(normalized_image_array.astype("uint8"), "HSV").convert("RGB")
        self.calibration.processed_files[self.current_file] = normalized_image

        self.parent.draw_results_image(self.current_file)

        # Re-enable slider and spinbox
        self.parent.cal_results_settings_blur_slider["state"] = "normal"
        self.parent.cal_results_settings_blur_spinbox["state"] = "normal"
        self.parent.cal_results_settings_noise_slider["state"] = "normal"
        self.parent.cal_results_settings_noise_spinbox["state"] = "normal"

        # Calculate remaining images in the background
        for i in self.update_order:
            if self.stop:
                break
            elif i is not self.current_file:
                blur_number = self.calibration.confirmed_blur_radius
                blurred_image = self.calibration.blurred_images[i][blur_number]
                brightness_map = self.calibration.brightness_maps[i][blur_number]
                width, height = blurred_image.size

                image_array = numpy.array(blurred_image.convert("HSV"))
                normalized_image_array = self.calibration.normalize_image(
                    image_array,
                    brightness_map,
                    width, height,
                    self.calibration.confirmed_noise_filter)
                normalized_image = Image.fromarray(normalized_image_array.astype("uint8"), "HSV").convert("RGB")
                self.calibration.processed_files[i] = normalized_image

                # Update image if current image is the currently-viewed image (if user changes picture mid-thread)
                if i == self.calibration.current_viewed_picture:
                    self.parent.draw_results_image(i)
