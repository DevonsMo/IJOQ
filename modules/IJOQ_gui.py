import csv
from math import floor
from os import path, mkdir, walk
import tkinter
from tkinter import filedialog, ttk, messagebox
from threading import Thread
from PIL import Image, ImageFilter, ImageTk
import numpy

class GuiWindow:

    class CalNoiseCalculationThread(Thread):
        """
        Starts a thread for updating the calibration results when the blur/noise options are changed
        """

        def __init__(self, parent):
            Thread.__init__(self)
            self.parent = parent
            self.stop = False
            self.current_file = 0 # TODO: Set as self.parent.cal_current_viewed_picture?
            self.update_order = []

        def run(self):
            """
            Updates the images in the cal_processed_files list according to the current blur/noise settings
            :return: None
            """

            # Save current image number
            self.current_file = self.parent.cal_current_viewed_picture
            blur_number = self.parent.cal_confirmed_blur_radius

            # Determine update order (current image first, then nearby images, etc.)
            above_images_count = len(self.parent.cal_processed_files) - self.current_file - 1
            below_images_count = self.current_file

            for i in range(1, max(above_images_count, below_images_count) + 1):
                if i <= below_images_count:
                    self.update_order.append(self.current_file - i)
                if i <= above_images_count:
                    self.update_order.append(self.current_file + i)

            # Calculate current image first
            blurred_image = self.parent.cal_blurred_images[self.current_file][blur_number]
            brightness_map = self.parent.cal_brightness_maps[self.current_file][blur_number]
            width, height = blurred_image.size

            image_array = numpy.array(blurred_image.convert("HSV"))
            normalized_image_array = self.parent.normalize_image(
                image_array,
                brightness_map,
                width, height,
                self.parent.cal_confirmed_noise_filter)
            normalized_image = Image.fromarray(normalized_image_array.astype("uint8"), "HSV").convert("RGB")
            self.parent.cal_processed_files[self.current_file] = normalized_image

            self.parent.draw_results_image(self.current_file, "cal")

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
                    blur_number = self.parent.cal_confirmed_blur_radius
                    blurred_image = self.parent.cal_blurred_images[i][blur_number]
                    brightness_map = self.parent.cal_brightness_maps[i][blur_number]
                    width, height = blurred_image.size

                    image_array = numpy.array(blurred_image.convert("HSV"))
                    normalized_image_array = self.parent.normalize_image(
                        image_array,
                        brightness_map,
                        width, height,
                        self.parent.cal_confirmed_noise_filter)
                    normalized_image = Image.fromarray(normalized_image_array.astype("uint8"), "HSV").convert("RGB")
                    self.parent.cal_processed_files[i] = normalized_image

                    # Update image if current image is the currently-viewed image (if user changes picture mid-thread)
                    if i == self.parent.cal_current_viewed_picture:
                        self.parent.draw_results_image(i, "cal")


    def __init__(self, x, y, min_x, min_y, title, icon_name, image_formats, version, directory):
        """
        Starts the tkinter GUI and saves as root
        :param x: Initial width of window
        :param y: Initial height of window
        :param min_x: Minimum allowed width of window
        :param min_y: Minimum allowed height of window
        :param title: Title of the window
        :param icon_name: File name of the icon
        :param image_formats: List of file formats that can be accepted
        :param version: String containing the current version of the program
        :param directory: String containing the working directory of the main program
        :return: None
        """

        # Global variables
        # Calibration variables
        self.cal_current_tab = 0
        self.cal_confirmed_files = []
        self.cal_confirmed_file_names = ()
        self.cal_blurred_images = []
        self.cal_normalization_thresholds = []
        self.cal_brightness_maps = []
        self.cal_processed_files = []
        self.cal_confirmed_channel = 0
        self.cal_confirmed_image_compression = 0
        self.cal_confirmed_blur_radius = 0
        self.cal_confirmed_section_number = 0
        self.cal_confirmed_pixel_number = 0
        self.cal_confirmed_normal_threshold = 0
        self.cal_confirmed_noise_filter = 0
        self.cal_confirmed_line_number = 0
        self.cal_current_viewed_picture = 0
        self.cal_noise_filter_threads = []

        # Calibration file selection variables
        self.cal_input_files = []

        # Analysis variables
        self.anl_current_tab = 0
        self.anl_confirmed_files = []
        self.anl_confirmed_file_names = ()
        self.anl_processed_files = []
        self.anl_IJOQ_list = []
        self.anl_confirmed_channel = 0
        self.anl_confirmed_image_compression = 0
        self.anl_confirmed_blur_radius = 0
        self.anl_confirmed_section_number = 0
        self.anl_confirmed_pixel_number = 0
        self.anl_confirmed_normal_threshold = 0
        self.anl_confirmed_noise_filter = 0
        self.anl_confirmed_line_number = 0
        self.anl_current_viewed_picture = 0
        self.anl_has_uploaded_settings = False

        # Analysis file selection variables
        self.anl_input_files = []

        # Settings selection variables
        self.anl_channel_selection = 0
        self.anl_image_compression = 0
        self.anl_blur_radius = 0
        self.anl_section_number = 0
        self.anl_pixel_number = 0
        self.anl_normal_threshold = 0
        self.anl_noise_filter = 0
        self.anl_line_number = 0

        # Set window variables
        self.root = tkinter.Tk()
        self.root.geometry(f"{x}x{y}")
        self.root.minsize(min_x, min_y)
        self.root.title(title)
        icon = tkinter.PhotoImage(file=f"{directory}/{icon_name}")
        self.root.iconphoto(False, icon)

        self.valid_image_types = image_formats
        self.current_version = version

        # Set styles
        centered_tab_style = ttk.Style()
        centered_tab_style.configure("centered.TNotebook", tabposition="n")

        # Input validation
        vcmd_int = (self.root.register(self.validate_input_int), "%P")
        vcmd_float = (self.root.register(self.validate_input_float), "%P")

        # GUI-related settings selection variables (used in calibration
        # TODO: Figure out why I made all of these StringVars instead of IntVar or DoubleVar
        self.cal_cell_number_x = tkinter.StringVar()
        self.cal_cell_number_x.set("0")
        self.cal_cell_number_y = tkinter.StringVar()
        self.cal_cell_number_y.set("0")
        self.cal_channel_options = ("Red", "Green", "Blue", "White")
        self.cal_channel_selection = tkinter.StringVar()
        self.cal_image_compression = tkinter.StringVar()
        self.cal_image_compression.set("512")
        self.cal_blur_radius = tkinter.StringVar()
        self.cal_blur_radius.set("4")
        self.cal_section_number = tkinter.StringVar()
        self.cal_section_number.set("4")
        self.cal_pixel_number = tkinter.StringVar()
        self.cal_pixel_number.set("8")
        self.cal_noise_filter = tkinter.StringVar()
        self.cal_noise_filter.set("0.1")
        self.cal_line_number = tkinter.StringVar()
        self.cal_line_number.set("10")
        self.cal_results_blur_radius = tkinter.StringVar()
        self.cal_results_noise_filter = tkinter.StringVar()

        # Add upper tabs
        upper_tabs = ttk.Notebook(self.root, style="centered.TNotebook")
        upper_tabs.pack(fill="both", expand=True)

        calibration_frame = ttk.Frame(upper_tabs)
        analysis_frame = ttk.Frame(upper_tabs)
        calibration_frame.pack(fill="both", expand=True)
        analysis_frame.pack(fill="both", expand=True)

        upper_tabs.add(calibration_frame, text=f'{"Calibrate IJOQ":^80s}')
        upper_tabs.add(analysis_frame, text=f'{"IJOQ analysis":^80s}')

        # ==CALIBRATION==
        # Add calibration tabs
        self.calibration_side_tabs = ttk.Notebook(calibration_frame)
        self.calibration_side_tabs.pack(fill="both", expand=True)

        cal_select_frame = ttk.Frame(self.calibration_side_tabs)
        cal_settings_frame = ttk.Frame(self.calibration_side_tabs)
        cal_calibration_frame = ttk.Frame(self.calibration_side_tabs)
        cal_results_frame = ttk.Frame(self.calibration_side_tabs)
        cal_select_frame.pack(fill="both", expand=True)
        cal_settings_frame.pack(fill="both", expand=True)
        cal_calibration_frame.pack(fill="both", expand=True)
        cal_results_frame.pack(fill="both", expand=True)

        self.calibration_side_tabs.add(cal_select_frame, text=f'{"1. Select images":^25s}')
        self.calibration_side_tabs.add(cal_settings_frame, text=f'{"2. Select settings":^25s}')
        self.calibration_side_tabs.add(cal_calibration_frame, text=f'{"3. Calibration":^25s}')
        self.calibration_side_tabs.add(cal_results_frame, text=f'{"4. View Results":^25s}')
        self.calibration_side_tabs.tab(1, state="disabled")
        self.calibration_side_tabs.tab(2, state="disabled")
        self.calibration_side_tabs.tab(3, state="disabled")

        self.calibration_side_tabs.bind(
            "<<NotebookTabChanged>>",
            lambda e: self.update_current_tab("cal"))

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
        self.cal_file_list_box = tkinter.Listbox(master=cal_file_list_frame)
        cal_file_list_scrollbar = ttk.Scrollbar(master=cal_file_list_frame, orient="vertical")
        self.cal_file_list_box.config(yscrollcommand=cal_file_list_scrollbar.set)
        cal_file_list_scrollbar.config(command=self.cal_file_list_box.yview)
        cal_file_list_label.grid(row=0, column=0, sticky="nsew")
        self.cal_file_list_box.grid(row=1, column=0, sticky="nsew")
        cal_file_list_scrollbar.grid(row=1, column=1, sticky="ns")

        # Add file options
        cal_file_add_button = ttk.Button(
            master=cal_file_options_frame, text="Add file",
            command=lambda: self.add_file("cal"))
        cal_folder_add_button = ttk.Button(
            master=cal_file_options_frame, text="Add folder",
            command=lambda: self.add_folder("cal"))
        cal_file_delete_button = ttk.Button(
            master=cal_file_options_frame, text="Delete selection",
            command=lambda: self.del_file("cal"))
        cal_file_clear_button = ttk.Button(
            master=cal_file_options_frame, text="Clear all",
            command=lambda: self.clear_file("cal"))
        cal_file_add_button.pack(padx=10, pady=2, fill="both")
        cal_folder_add_button.pack(padx=10, pady=2, fill="both")
        cal_file_delete_button.pack(padx=10, pady=2, fill="both")
        cal_file_clear_button.pack(padx=10, pady=2, fill="both")

        # Add lower button
        self.cal_file_select_button = ttk.Button(
            master=cal_select_frame,
            text="Confirm selection",
            width=20,
            state="disabled",
            command=lambda: self.confirm_files("cal"))
        self.cal_file_select_button.grid(padx=10, pady=10, row=2, column=1, sticky="se")

        # ==CALIBRATION:SETTINGS PAGE==
        # Frame for determining the settings
        cal_settings_frame.columnconfigure(0, weight=1)
        cal_settings_frame.columnconfigure(1, weight=1)
        cal_settings_frame.rowconfigure(0, weight=1)
        cal_settings_frame.rowconfigure(1, weight=0)

        # Add Basic and Advanced settings tab
        self.cal_settings_options_tabs = ttk.Notebook(cal_settings_frame, style="centered.TNotebook")
        self.cal_settings_options_tabs.grid(padx=10, pady=10, row=0, columnspan=2, sticky="nsew")

        cal_settings_basic_frame = ttk.Frame(self.cal_settings_options_tabs)
        cal_settings_advanced_frame = ttk.Frame(self.cal_settings_options_tabs)

        self.cal_settings_options_tabs.add(cal_settings_basic_frame, text=f'{"Basic":^80s}')
        self.cal_settings_options_tabs.add(cal_settings_advanced_frame, text=f'{"Advanced":^80s}')

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
            wrap=True, textvariable=self.cal_cell_number_x, width=5,
            validate="key", validatecommand=vcmd_int)
        cal_settings_cell_number_x_spinbox.bind(
            "<FocusOut>",
            lambda e: self.sanitize_input(self.cal_cell_number_x, False, "int", 0, 99))
        cal_settings_cell_number_x_spinbox.bind(
            "<Return>",
            lambda e: self.root.focus())
        cal_settings_cell_number_y_spinbox = ttk.Spinbox(
            cal_settings_basic_frame, from_=0, to=99,
            wrap=True, textvariable=self.cal_cell_number_y, width=5,
            validate="key", validatecommand=vcmd_int)
        cal_settings_cell_number_y_spinbox.bind(
            "<FocusOut>",
            lambda e: self.sanitize_input(self.cal_cell_number_y, False, "int", 0, 99))
        cal_settings_cell_number_y_spinbox.bind(
            "<Return>",
            lambda e: self.root.focus())

        # Basic Setting Dropdown
        cal_settings_channel_dropdown = ttk.OptionMenu(
            cal_settings_basic_frame, self.cal_channel_selection,
            self.cal_channel_options[0], *self.cal_channel_options)
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
            wrap=True, textvariable=self.cal_image_compression, width=6,
            validate="key", validatecommand=vcmd_int)
        cal_settings_image_compression_spinbox.bind(
            "<FocusOut>",
            lambda e: self.sanitize_input(self.cal_image_compression, False, "int", 128, 1024))
        cal_settings_image_compression_spinbox.bind(
            "<Return>",
            lambda e: self.root.focus())
        cal_settings_blur_radius_spinbox = ttk.Spinbox(
            cal_settings_advanced_frame, from_=0, to=5,
            wrap=True, textvariable=self.cal_blur_radius, width=6,
            validate="key", validatecommand=vcmd_int)
        cal_settings_blur_radius_spinbox.bind(
            "<FocusOut>",
            lambda e: self.sanitize_input(self.cal_blur_radius, False, "int", 0, 5))
        cal_settings_blur_radius_spinbox.bind(
            "<Return>",
            lambda e: self.root.focus())
        cal_settings_section_number_spinbox = ttk.Spinbox(
            cal_settings_advanced_frame, from_=0, to=50,
            wrap=True, textvariable=self.cal_section_number, width=6,
            validate="key", validatecommand=vcmd_int)
        cal_settings_section_number_spinbox.bind(
            "<FocusOut>",
            lambda e: self.sanitize_input(self.cal_section_number, False, "int", 0, 10))
        cal_settings_section_number_spinbox.bind(
            "<Return>",
            lambda e: self.root.focus())
        cal_settings_pixel_number_spinbox = ttk.Spinbox(
            cal_settings_advanced_frame, from_=0, to=99,
            wrap=True, textvariable=self.cal_pixel_number, width=6,
            validate="key", validatecommand=vcmd_int)
        cal_settings_pixel_number_spinbox.bind(
            "<FocusOut>",
            lambda e: self.sanitize_input(self.cal_pixel_number, False, "int", 0, 99))
        cal_settings_pixel_number_spinbox.bind(
            "<Return>",
            lambda e: self.root.focus())
        cal_settings_noise_filter_spinbox = ttk.Spinbox(
            cal_settings_advanced_frame, from_=-0.5, to=0.5, increment=0.005,
            wrap=True, textvariable=self.cal_noise_filter, width=6,
            validate="key", validatecommand=vcmd_float)
        cal_settings_noise_filter_spinbox.bind(
            "<FocusOut>",
            lambda e: self.sanitize_input(self.cal_noise_filter, False, "float", -0.5, 0.5))
        cal_settings_noise_filter_spinbox.bind(
            "<Return>",
            lambda e: self.root.focus())
        cal_settings_line_number_spinbox = ttk.Spinbox(
            cal_settings_advanced_frame, from_=0, to=99,
            wrap=True, textvariable=self.cal_line_number, width=6,
            validate="key", validatecommand=vcmd_int)
        cal_settings_line_number_spinbox.bind(
            "<FocusOut>",
            lambda e: self.sanitize_input(self.cal_line_number, False, "int", 0, 99))
        cal_settings_line_number_spinbox.bind(
            "<Return>",
            lambda e: self.root.focus())

        # Advanced Settings Dropdown
        cal_settings_advanced_channel_dropdown = ttk.OptionMenu(
            cal_settings_advanced_frame, self.cal_channel_selection,
            self.cal_channel_options[0], *self.cal_channel_options)
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
            command=lambda: self.go_to_previous_page("cal"))
        self.cal_settings_confirm_button = ttk.Button(
            master=cal_settings_frame,
            text="Run calibration",
            width=20,
            state="disabled",
            command=self.cal_go_to_calibration)
        cal_settings_previous_button.grid(padx=10, pady=10, row=1, column=0, sticky="sw")
        self.cal_settings_confirm_button.grid(padx=10, pady=10, row=1, column=1, sticky="se")

        # ==CALIBRATION:CALIBRATION PAGE==
        cal_calibration_frame.columnconfigure(0, weight=1)
        cal_calibration_frame.columnconfigure(1, weight=1)
        cal_calibration_frame.rowconfigure(0, weight=0)
        cal_calibration_frame.rowconfigure(1, weight=1)
        cal_calibration_frame.rowconfigure(2, weight=0)

        # Add a progress bar
        self.cal_calibration_progress_bar = ttk.Progressbar(
            master=cal_calibration_frame,
            orient="horizontal",
            mode='determinate')
        self.cal_calibration_progress_bar.grid(padx=10, pady=10, row=0, column=0, columnspan=2, sticky="ew")

        # Add a frame for text box and scrollbar
        cal_calibration_text_frame = ttk.Frame(cal_calibration_frame)
        cal_calibration_text_frame.grid(padx=10, pady=0, row=1, column=0, columnspan=2, sticky="nsew")

        cal_calibration_text_frame.columnconfigure(0, weight=1)
        cal_calibration_text_frame.columnconfigure(1, weight=0)
        cal_calibration_text_frame.rowconfigure(0, weight=1)

        # Add scroll bar for text box
        self.cal_calibration_textbox = tkinter.Text(cal_calibration_text_frame)
        self.cal_calibration_textbox.bind(
            "<Key>",
            lambda e: "break")
        cal_calibration_text_scrollbar = ttk.Scrollbar(master=cal_calibration_text_frame, orient="vertical")
        self.cal_calibration_textbox.config(yscrollcommand=cal_calibration_text_scrollbar.set)
        cal_calibration_text_scrollbar.config(command=self.cal_calibration_textbox.yview)
        self.cal_calibration_textbox.grid(row=0, column=0, sticky="nsew")
        cal_calibration_text_scrollbar.grid(row=0, column=1, sticky="ns")

        # Add previous and confirm button
        self.cal_calibration_previous_button = ttk.Button(
            master=cal_calibration_frame,
            text="Previous",
            width=20,
            state="disabled",
            command=lambda: self.go_to_previous_page("cal"))
        self.cal_calibration_confirm_button = ttk.Button(
            master=cal_calibration_frame,
            text="Show result",
            width=20,
            state="disabled",
            command=lambda: self.calibration_side_tabs.select(3))
        self.cal_calibration_previous_button.grid(padx=10, pady=10, row=2, column=0, sticky="sw")
        self.cal_calibration_confirm_button.grid(padx=10, pady=10, row=2, column=1, sticky="se")

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
                 "Please review the processed images and ensure that the identified "
                 "junctions are smooth and the noise filter is as high as possible without removing junctions. \n\n"
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
        self.cal_results_picture_left_arrow_button = ttk.Button(
            master=cal_results_picture_frame,
            text="←",
            width=3,
            command=lambda: self.results_go_to_picture(self.cal_current_viewed_picture - 1, "cal")
        )
        self.cal_results_picture_right_arrow_button = ttk.Button(
            master=cal_results_picture_frame,
            text="→",
            width=3,
            command=lambda: self.results_go_to_picture(self.cal_current_viewed_picture + 1, "cal")
        )
        self.cal_results_picture_left_arrow_button.grid(row=0, column=0, sticky="e")
        self.cal_results_picture_right_arrow_button.grid(row=0, column=2, sticky="w")

        # Textbox for Picture
        self.cal_results_picture_label = ttk.Label(cal_results_picture_frame, compound=tkinter.TOP, anchor=tkinter.CENTER)
        self.cal_results_picture_label.grid(row=0, column=1, sticky="nsew")
        self.cal_results_picture_label.bind(
            "<Configure>",
            lambda e: self.draw_results_image(self.cal_current_viewed_picture, "cal"))

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
        self.cal_results_settings_value_label = ttk.Label(
            master=cal_results_settings_frame,
            anchor=tkinter.NW, width=20,
            justify=tkinter.LEFT)
        self.cal_results_settings_value_label.grid(row=1, column=1, columnspan=2, sticky="nsew")

        # Label for the blur radius
        cal_results_settings_blur_label = ttk.Label(
            master=cal_results_settings_frame,
            text="Blur radius:")
        cal_results_settings_blur_label.grid(row=2, column=0, sticky="nsew")

        # Slider for the blur radius
        self.cal_results_settings_blur_slider = ttk.Scale(
            master=cal_results_settings_frame,
            from_=0, to=5,
            variable=self.cal_results_blur_radius,
            length=200,
            command=lambda e: self.cal_results_blur_radius.set(
                str(int(round(float(self.cal_results_blur_radius.get()))))))
        self.cal_results_settings_blur_slider.bind(
            "<ButtonRelease-1>",
            lambda e: self.cal_update_results(int(self.cal_results_blur_radius.get()), self.cal_confirmed_noise_filter))
        self.cal_results_settings_blur_slider.grid(padx=2, row=3, column=0, columnspan=2, sticky="ew")

        # Spinbox for the blur radius
        self.cal_results_settings_blur_spinbox = ttk.Spinbox(
            cal_results_settings_frame, from_=0, to=5,
            wrap=True, textvariable=self.cal_results_blur_radius, width=6,
            command=lambda: self.cal_update_results(int(self.cal_results_blur_radius.get()), self.cal_confirmed_noise_filter),
            validate="key", validatecommand=vcmd_int)
        self.cal_results_settings_blur_spinbox.bind(
            "<FocusOut>",
            self.cal_results_blur_spinbox_update)
        self.cal_results_settings_blur_spinbox.bind(
            "<Return>",
            lambda e: self.root.focus())
        self.cal_results_settings_blur_spinbox.grid(padx=2, row=3, column=2, sticky="e")

        # Label for the noise threshold
        cal_results_settings_noise_label = ttk.Label(
            master=cal_results_settings_frame,
            text="Noise Threshold:")
        cal_results_settings_noise_label.grid(row=4, column=0, sticky="nsew")

        # Slider for the noise threshold
        self.cal_results_settings_noise_slider = ttk.Scale(
            master=cal_results_settings_frame,
            from_=-0.5, to=0.5,
            variable=self.cal_results_noise_filter,
            length=200,
            command=lambda e: self.cal_results_noise_filter.set(
                str(round(round(float(self.cal_results_noise_filter.get()) / 0.005) * 0.005, 3))))
        self.cal_results_settings_noise_slider.bind(
            "<ButtonRelease-1>",
            lambda e: self.cal_update_results(self.cal_confirmed_blur_radius, float(self.cal_results_noise_filter.get())))
        self.cal_results_settings_noise_slider.grid(padx=2, row=5, column=0, columnspan=2, sticky="ew")

        # Spinbox for the noise threshold
        self.cal_results_settings_noise_spinbox = ttk.Spinbox(
            cal_results_settings_frame, from_=-0.5, to=0.5, increment=0.005,
            wrap=True, textvariable=self.cal_results_noise_filter, width=6,
            command=lambda: self.cal_update_results(self.cal_confirmed_blur_radius, float(self.cal_results_noise_filter.get())),
            validate="key", validatecommand=vcmd_float)
        self.cal_results_settings_noise_spinbox.bind(
            "<FocusOut>",
            self.cal_results_noise_spinbox_update)
        self.cal_results_settings_noise_spinbox.bind(
            "<Return>",
            lambda e: self.root.focus())
        self.cal_results_settings_noise_spinbox.grid(padx=2, row=5, column=2, sticky="e")

        # Add previous and confirm button
        cal_results_previous_button = ttk.Button(
            master=cal_results_frame,
            text="Previous",
            width=20,
            command=lambda: self.go_to_previous_page("cal"))
        cal_results_save_button = ttk.Button(
            master=cal_results_frame,
            text="Save settings",
            width=20,
            command=self.cal_save_settings)
        cal_results_previous_button.grid(padx=10, pady=10, row=2, column=0, sticky="sw")
        cal_results_save_button.grid(padx=10, pady=10, row=2, column=1, sticky="se")

        # ==ANALYSIS==
        # Add analysis tabs
        self.analysis_side_tabs = ttk.Notebook(analysis_frame)
        self.analysis_side_tabs.pack(fill="both", expand=True)

        anl_select_frame = ttk.Frame(self.analysis_side_tabs)
        anl_settings_frame = ttk.Frame(self.analysis_side_tabs)
        anl_analysis_frame = ttk.Frame(self.analysis_side_tabs)
        anl_results_frame = ttk.Frame(self.analysis_side_tabs)
        anl_select_frame.pack(fill="both", expand=True)
        anl_settings_frame.pack(fill="both", expand=True)
        anl_analysis_frame.pack(fill="both", expand=True)
        anl_results_frame.pack(fill="both", expand=True)

        self.analysis_side_tabs.add(anl_select_frame, text=f'{"1. Select images":^25s}')
        self.analysis_side_tabs.add(anl_settings_frame, text=f'{"2. Select settings":^25s}')
        self.analysis_side_tabs.add(anl_analysis_frame, text=f'{"3. Analysis":^25s}')
        self.analysis_side_tabs.add(anl_results_frame, text=f'{"4. View Results":^25s}')
        self.analysis_side_tabs.tab(1, state="disabled")
        self.analysis_side_tabs.tab(2, state="disabled")
        self.analysis_side_tabs.tab(3, state="disabled")

        self.analysis_side_tabs.bind(
            "<<NotebookTabChanged>>",
            lambda e: self.update_current_tab("anl"))

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
        self.anl_file_list_box = tkinter.Listbox(master=anl_file_list_frame)
        anl_file_list_scrollbar = ttk.Scrollbar(master=anl_file_list_frame, orient="vertical")
        self.anl_file_list_box.config(yscrollcommand=anl_file_list_scrollbar.set)
        anl_file_list_scrollbar.config(command=self.anl_file_list_box.yview)
        anl_file_list_label.grid(row=0, column=0, sticky="nsew")
        self.anl_file_list_box.grid(row=1, column=0, sticky="nsew")
        anl_file_list_scrollbar.grid(row=1, column=1, sticky="ns")

        # Add file options
        anl_file_add_button = ttk.Button(
            master=anl_file_options_frame, text="Add file",
            command=lambda: self.add_file("anl"))
        anl_folder_add_button = ttk.Button(
            master=anl_file_options_frame, text="Add folder",
            command=lambda: self.add_folder("anl"))
        anl_file_delete_button = ttk.Button(
            master=anl_file_options_frame, text="Delete selection",
            command=lambda: self.del_file("anl"))
        anl_file_clear_button = ttk.Button(
            master=anl_file_options_frame, text="Clear all",
            command=lambda: self.clear_file("anl"))
        anl_file_add_button.pack(padx=10, pady=2, fill="both")
        anl_folder_add_button.pack(padx=10, pady=2, fill="both")
        anl_file_delete_button.pack(padx=10, pady=2, fill="both")
        anl_file_clear_button.pack(padx=10, pady=2, fill="both")

        # Add lower button
        self.anl_file_select_button = ttk.Button(
            master=anl_select_frame,
            text="Confirm selection",
            width=20,
            state="disabled",
            command=lambda: self.confirm_files("anl"))
        self.anl_file_select_button.grid(padx=10, pady=10, row=2, column=1, sticky="se")

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
        self.anl_settings_value_label = ttk.Label(
            master=anl_settings_frame,
            anchor=tkinter.NW, width=20,
            justify=tkinter.LEFT)
        self.anl_settings_value_label.grid(pady=2, row=2, column=1, sticky="nsew")

        # Add settings file button
        anl_add_settings_button = ttk.Button(
            master=anl_settings_frame, text="Upload settings",
            command=self.anl_add_settings)
        anl_add_settings_button.grid(padx=10, row=1, rowspan=2, column=2, sticky="new")

        # Add previous and confirm button
        anl_settings_previous_button = ttk.Button(
            master=anl_settings_frame,
            text="Previous",
            width=20,
            command=lambda: self.go_to_previous_page("anl"))
        self.anl_settings_confirm_button = ttk.Button(
            master=anl_settings_frame,
            text="Run analysis",
            width=20,
            state="disabled",
            command=self.anl_go_to_analysis)
        anl_settings_previous_button.grid(padx=10, pady=10, row=3, column=0, sticky="sw")
        self.anl_settings_confirm_button.grid(padx=10, pady=10, row=3, column=2, sticky="se")

        # ==ANALYSIS:ANALYSIS PAGE==
        anl_analysis_frame.columnconfigure(0, weight=1)
        anl_analysis_frame.columnconfigure(1, weight=1)
        anl_analysis_frame.rowconfigure(0, weight=0)
        anl_analysis_frame.rowconfigure(1, weight=1)
        anl_analysis_frame.rowconfigure(2, weight=0)

        # Add a progress bar
        self.anl_analysis_progress_bar = ttk.Progressbar(
            master=anl_analysis_frame,
            orient="horizontal",
            mode='determinate')
        self.anl_analysis_progress_bar.grid(padx=10, pady=10, row=0, column=0, columnspan=2, sticky="ew")

        # Add a frame for text box and scrollbar
        anl_analysis_text_frame = ttk.Frame(anl_analysis_frame)
        anl_analysis_text_frame.grid(padx=10, pady=0, row=1, column=0, columnspan=2, sticky="nsew")

        anl_analysis_text_frame.columnconfigure(0, weight=1)
        anl_analysis_text_frame.columnconfigure(1, weight=0)
        anl_analysis_text_frame.rowconfigure(0, weight=1)

        # Add scroll bar for text box
        self.anl_analysis_textbox = tkinter.Text(anl_analysis_text_frame)
        self.anl_analysis_textbox.bind(
            "<Key>",
            lambda e: "break")
        anl_analysis_text_scrollbar = ttk.Scrollbar(master=anl_analysis_text_frame, orient="vertical")
        self.anl_analysis_textbox.config(yscrollcommand=anl_analysis_text_scrollbar.set)
        anl_analysis_text_scrollbar.config(command=self.anl_analysis_textbox.yview)
        self.anl_analysis_textbox.grid(row=0, column=0, sticky="nsew")
        anl_analysis_text_scrollbar.grid(row=0, column=1, sticky="ns")

        # Add previous and confirm button
        self.anl_analysis_previous_button = ttk.Button(
            master=anl_analysis_frame,
            text="Previous",
            width=20,
            state="disabled",
            command=lambda: self.go_to_previous_page("anl"))
        self.anl_analysis_confirm_button = ttk.Button(
            master=anl_analysis_frame,
            text="Show result",
            width=20,
            state="disabled",
            command=lambda: self.analysis_side_tabs.select(3))
        self.anl_analysis_previous_button.grid(padx=10, pady=10, row=2, column=0, sticky="sw")
        self.anl_analysis_confirm_button.grid(padx=10, pady=10, row=2, column=1, sticky="se")

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
        self.anl_results_picture_left_arrow_button = ttk.Button(
            master=anl_results_picture_frame,
            text="←",
            width=3,
            command=lambda: self.results_go_to_picture(self.anl_current_viewed_picture - 1, "anl")
        )
        self.anl_results_picture_right_arrow_button = ttk.Button(
            master=anl_results_picture_frame,
            text="→",
            width=3,
            command=lambda: self.results_go_to_picture(self.anl_current_viewed_picture + 1, "anl")
        )
        self.anl_results_picture_left_arrow_button.grid(row=0, column=0, sticky="e")
        self.anl_results_picture_right_arrow_button.grid(row=0, column=2, sticky="w")

        # Textbox for Picture
        self.anl_results_picture_label = ttk.Label(anl_results_picture_frame, compound=tkinter.TOP, anchor=tkinter.CENTER)
        self.anl_results_picture_label.grid(row=0, column=1, sticky="nsew")
        self.anl_results_picture_label.bind(
            "<Configure>",
            lambda e: self.draw_results_image(self.anl_current_viewed_picture, "anl"))

        # Add previous and confirm button
        anl_results_previous_button = ttk.Button(
            master=anl_results_frame,
            text="Previous",
            width=20,
            command=lambda: self.go_to_previous_page("anl"))
        anl_results_save_button = ttk.Button(
            master=anl_results_frame,
            text="Save results",
            width=20,
            command=self.anl_save_results)
        anl_results_previous_button.grid(padx=10, pady=10, row=2, column=0, sticky="sw")
        anl_results_save_button.grid(padx=10, pady=10, row=2, column=1, sticky="se")

    def validate_input_int(self, new_input):
        """
        Used to validate inputs for spinboxes that are meant to be integers only
        :param new_input: Input to be validated
        :return: True if input is an integer, False if not
        """
        return new_input.isdecimal() or new_input == ""

    def validate_input_float(self, new_input):
        """
        Used to validate inputs for spinboxes that are meant to be floats only
        :param new_input: Input to be validated
        :return: True if input is a float, False if not
        """
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

    def sanitize_input(self, variable, is_even, var_type, var_min, var_max):
        """
        Prevents invalid inputs by rounding/deleting parts of the input until it fits to the expected variable type
        :param variable: Variable to be sanitized
        :param is_even: True/False. The variable must be even. Must be used with the "int" var_type
        :param var_type: "int" or "float". The variable must be an integer or float
        :param var_min: The minimum allowable value of the variable
        :param var_max: The maximum allowable value of the variable
        :return: None
        """
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

    def add_file(self, tab):
        """
        Opens a file selection window and adds the selected file to a listbox,
        then adds the file to the internal calibration/analysis file selection list.
        Can only pick 1 file at a time.
        :param tab: "cal" (calibration) or "anl" (analysis)
        :return: None
        """
        file_path = filedialog.askopenfilename()
        if file_path:
            if file_path.lower().endswith(self.valid_image_types):
                if "Output" not in file_path:
                    # Check calibration file count
                    if len(self.cal_input_files) < 99 and tab == "cal":
                        file_name = file_path.split("/")[-1]
                        self.cal_input_files.append(file_path)
                        self.cal_file_list_box.insert(tkinter.END, file_name)
                    # Check analysis file count
                    elif len(self.anl_input_files) < 99 and tab == "anl":
                        file_name = file_path.split("/")[-1]
                        self.anl_input_files.append(file_path)
                        self.anl_file_list_box.insert(tkinter.END, file_name)
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
        if len(self.cal_input_files) >= 3 and tab == "cal":
            self.cal_file_select_button["state"] = "normal"
        elif len(self.anl_input_files) >= 1 and tab == "anl":
            self.anl_file_select_button["state"] = "normal"

    def add_folder(self, tab):
        """
        Opens a folder selection window and adds all files within the folder to a listbox,
        then adds the files to the internal calibration/analysis file selection list.
        Can only pick 1 file at a time.
        :param tab: "cal" (calibration) or "anl" (analysis)
        :return: None
        """
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
                        if file.lower().endswith(self.valid_image_types):
                            # Check calibration file count
                            if len(self.cal_input_files) < 99 and tab == "cal":
                                self.cal_input_files.append(dirpath + "/" + file)
                                self.cal_file_list_box.insert(tkinter.END, file)
                            # Check analysis file count
                            elif len(self.anl_input_files) < 99 and tab == "anl":
                                self.anl_input_files.append(dirpath + "/" + file)
                                self.anl_file_list_box.insert(tkinter.END, file)
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
        if len(self.cal_input_files) >= 3 and tab == "cal":
            self.cal_file_select_button["state"] = "normal"
        elif len(self.anl_input_files) >= 1 and tab == "anl":
            self.anl_file_select_button["state"] = "normal"

    def del_file(self, tab):
        """
        Deletes the selected option from the listbox and removes the file from
        the internal calibration/analysis file selection list.
        :param tab: "cal" (calibration) or "anl" (analysis)
        :return: None
        """
        if tab == "cal":
            # Delete from the largest index first to maintain the index order
            for i in sorted(self.cal_file_list_box.curselection(), reverse=True):
                del self.cal_input_files[i]
                self.cal_file_list_box.delete(i)

            # Disable the confirm files button if there are less than 3 selections
            if len(self.cal_input_files) < 3:
                self.cal_file_select_button["state"] = "disabled"
        elif tab == "anl":
            # Delete from the largest index first to maintain the index order
            for i in sorted(self.anl_file_list_box.curselection(), reverse=True):
                del self.anl_input_files[i]
                self.anl_file_list_box.delete(i)

            # Disable the confirm files button if there are less than 1 selection
            if len(self.anl_input_files) < 1:
                self.anl_file_select_button["state"] = "disabled"

    def clear_file(self, tab):
        """
        Deletes all files from the listbox and removes the files from
        the internal calibration/analysis file selection list.
        :param tab: "cal" (calibration) or "anl" (analysis)
        :return: None
        """
        if tab == "cal":
            self.cal_input_files.clear()
            self.cal_file_list_box.delete(0, tkinter.END)

            # Disable the confirm files button
            self.cal_file_select_button["state"] = "disabled"
        elif tab == "anl":
            self.anl_input_files.clear()
            self.anl_file_list_box.delete(0, tkinter.END)

            # Disable the confirm files button
            self.anl_file_select_button["state"] = "disabled"

    def confirm_files(self, tab):
        """
        Confirm file selection. Copies the list of files to a confirmed_files list,
        then enables the calibration/analysis button (files must be confirmed in order to run calibration/analysis)
        :param tab: "cal" (calibration) or "anl" (analysis)
        :return: None
        """
        if tab == "cal":

            # Enable next page, then move to next page
            self.calibration_side_tabs.tab(1, state="normal")
            self.calibration_side_tabs.select(1)

            # Copy input files into confirmed files
            self.cal_confirmed_files = self.cal_input_files.copy()
            self.cal_confirmed_file_names = self.cal_file_list_box.get(0, self.cal_file_list_box.size() - 1)

            # Enable the button to start calibration
            self.cal_settings_confirm_button["state"] = "normal"
        elif tab == "anl":

            # Enable next page, then move to next page
            self.analysis_side_tabs.tab(1, state="normal")
            self.analysis_side_tabs.select(1)

            # Copy input files into confirmed files
            self.anl_confirmed_files = self.anl_input_files.copy()
            self.anl_confirmed_file_names = self.anl_file_list_box.get(0, self.anl_file_list_box.size() - 1)

            # Enable the button to start analysis if settings has already been uploaded
            if self.anl_has_uploaded_settings:
                self.anl_settings_confirm_button["state"] = "normal"

    def update_current_tab(self, tab):
        """
        Updates the current tab when a tab change is detected
        :param tab: "cal" (calibration) or "anl" (analysis)
        :return: None
        """
        # If calibration
        if tab == "cal":

            # If there are unconfirmed files in the input, send message that calibration cannot be performed
            if self.cal_current_tab == 0 and self.cal_input_files != self.cal_confirmed_files:
                self.cal_settings_confirm_button["state"] = "disabled"
                messagebox.showinfo(
                    "Unconfirmed file selection",
                    "Unconfirmed file selection detected!\n\nYou will not be able "
                    "to run a calibration unless the file selection is confirmed.")

            self.cal_current_tab = self.calibration_side_tabs.index("current")
        # If analysis
        elif tab == "anl":

            # If there are unconfirmed files in the input, send message that analysis cannot be performed
            if self.anl_current_tab == 0 and self.anl_input_files != self.anl_confirmed_files:
                self.anl_settings_confirm_button["state"] = "disabled"
                messagebox.showinfo(
                    "Unconfirmed file selection",
                    "Unconfirmed file selection detected!\n\nYou will not be able "
                    "to run an analysis unless the file selection is confirmed.")

            self.anl_current_tab = self.analysis_side_tabs.index("current")

    def go_to_previous_page(self, tab):
        """
        Goes to the previous page in the calibration or analysis process
        :param tab: "cal" (calibration) or "anl" (analysis)
        :return: None
        """
        if tab == "cal":

            self.calibration_side_tabs.select(self.cal_current_tab - 1)
        elif tab == "anl":

            self.analysis_side_tabs.select(self.anl_current_tab - 1)

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

    def cal_go_to_calibration(self):
        """
        Sets the input variables for the calibration, sets the progress bar, and starts a thread to run the calibration
        :return: None
        """

        # Check for existing noise filter calculation threads. If previous threads exist, prompt them to stop
        if self.cal_noise_filter_threads:
            for thread in self.cal_noise_filter_threads:
                thread.stop = True

            # Wait for threads to stop before continuing
            for thread in self.cal_noise_filter_threads:
                thread.join()

        # Determine settings
        # If using basic settings
        if self.cal_settings_options_tabs.index("current") == 0:
            average_cell_count = (int(self.cal_cell_number_x.get()) + int(self.cal_cell_number_y.get())) / 2
            if average_cell_count > 50:
                self.cal_confirmed_image_compression = 1024
                self.cal_confirmed_section_number = 6
            else:
                self.cal_confirmed_image_compression = 512
                self.cal_confirmed_section_number = 4

            if self.cal_channel_selection.get() == "Red":
                self.cal_confirmed_channel = 0
            elif self.cal_channel_selection.get() == "Green":
                self.cal_confirmed_channel = 1
            elif self.cal_channel_selection.get() == "Blue":
                self.cal_confirmed_channel = 2
            elif self.cal_channel_selection.get() == "White":
                self.cal_confirmed_channel = 1

            # TODO: Why is blur radius set to negative average cell count?
            self.cal_confirmed_blur_radius = -average_cell_count
            self.cal_confirmed_pixel_number = 8
            self.cal_confirmed_noise_filter = -1
            self.cal_confirmed_line_number = max(10, int(round(average_cell_count, -1)))
        else:  # If using advanced settings
            self.cal_confirmed_image_compression = int(self.cal_image_compression.get())
            if self.cal_channel_selection.get() == "Red":
                self.cal_confirmed_channel = 0
            elif self.cal_channel_selection.get() == "Green":
                self.cal_confirmed_channel = 1
            elif self.cal_channel_selection.get() == "Blue":
                self.cal_confirmed_channel = 2
            elif self.cal_channel_selection.get() == "White":
                self.cal_confirmed_channel = 1
            self.cal_confirmed_blur_radius = int(self.cal_blur_radius.get())
            self.cal_confirmed_section_number = int(self.cal_section_number.get())
            self.cal_confirmed_pixel_number = int(self.cal_pixel_number.get())
            self.cal_confirmed_noise_filter = float(self.cal_noise_filter.get())
            self.cal_confirmed_line_number = int(self.cal_line_number.get())

        # Set progress bar to 0, delete text in textbox, and clear results
        self.cal_blurred_images = []
        self.cal_normalization_thresholds = []
        self.cal_brightness_maps = []
        self.cal_processed_files = []
        progress_bar_maximum = (len(self.cal_confirmed_files) * (13 + (12 * (self.cal_confirmed_section_number ** 2)))) + 6
        self.cal_calibration_progress_bar.config(maximum=progress_bar_maximum)
        self.cal_calibration_progress_bar["value"] = 0
        self.cal_calibration_textbox.delete(1.0, tkinter.END)

        # Move to the calibration screen
        self.calibration_side_tabs.tab(2, state="normal")
        self.calibration_side_tabs.select(2)

        # Disable other tabs
        self.calibration_side_tabs.tab(0, state="disabled")
        self.calibration_side_tabs.tab(1, state="disabled")
        self.calibration_side_tabs.tab(3, state="disabled")
        self.cal_calibration_previous_button["state"] = "disabled"
        self.cal_calibration_confirm_button["state"] = "disabled"

        calibration_thread = Thread(target=self.cal_run_calibration, daemon=True)
        calibration_thread.start()

    def cal_run_calibration(self):
        """
        Runs the calibration. Should be run as a thread, otherwise the GUI won't update properly
        :return: None
        """

        # Run calibration
        self.cal_calibration_textbox.insert(tkinter.END, "Determining ideal normalization threshold value...")
        self.cal_calibration_textbox.see(tkinter.END)

        # Run the following code for each file
        brightness_deviation_list = []
        threshold_list = []
        for file_number in range(len(self.cal_confirmed_files)):
            image_name = self.cal_confirmed_file_names[file_number]
            try:
                image = Image.open(self.cal_confirmed_files[file_number])
                width, height = image.size
                compression_amount = (self.cal_confirmed_image_compression / 2) * (width + height) / (width * height)
                image = image.resize((round(compression_amount * width), round(compression_amount * height)))
                width, height = image.size

                # Take the RGB values from all the pixels in the image as an array
                image_array = numpy.array(image.convert("RGB"))

                # Extract channel
                self.cal_calibration_textbox.insert(tkinter.END, f"\n\nExtracting channel from {image_name}...")
                self.cal_calibration_textbox.see(tkinter.END)
                for x in range(width):
                    for y in range(height):
                        image_array[y][x] = [image_array[y][x][self.cal_confirmed_channel]] * 3

                if self.cal_confirmed_blur_radius < 0:
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
                self.cal_calibration_textbox.insert(tkinter.END, f"\nApplying blur to {image_name}...")
                self.cal_calibration_textbox.see(tkinter.END)
                image = Image.fromarray(image_array.astype("uint8"))
                blur_radius_values = (0, 1, 2, 3, 4, 5)
                current_blurred_image_list = []
                for blur_radius_value in blur_radius_values:
                    blurred_image = image.filter(ImageFilter.GaussianBlur(radius=blur_radius_value))
                    current_blurred_image_list.append(blurred_image)
                    self.cal_calibration_progress_bar["value"] += 1
                self.cal_blurred_images.append(current_blurred_image_list)

                # Calculate threshold value for each individual blurred image
                self.cal_calibration_textbox.insert(tkinter.END, f"\nCalculating threshold values for {image_name}...")
                self.cal_calibration_textbox.see(tkinter.END)
                current_threshold_list = []
                for blurred_image in current_blurred_image_list:
                    image_array = numpy.array(blurred_image.convert("HSV"))

                    # Split the picture into sections
                    section_width = width / self.cal_confirmed_section_number
                    section_height = height / self.cal_confirmed_section_number

                    white_pixel_counter = 0
                    for section_x in range(self.cal_confirmed_section_number):
                        for section_y in range(self.cal_confirmed_section_number):
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
                            self.cal_calibration_progress_bar["value"] += 1

                    # Determine normalization threshold
                    white_percent = white_pixel_counter / (width * height)

                    threshold = numpy.ceil((1 - white_percent) * (self.cal_confirmed_pixel_number ** 2))
                    current_threshold_list.append(threshold)

                threshold_list.append(current_threshold_list)

            # File could not be opened
            except FileNotFoundError:
                # Print warning, re-enable file selection and settings, then stop function
                self.cal_calibration_textbox.insert(
                    tkinter.END, f"\n\nWARNING! Unable to find file for {image_name}!")
                self.cal_calibration_textbox.see(tkinter.END)

                self.calibration_side_tabs.tab(0, state="normal")
                self.calibration_side_tabs.tab(1, state="normal")
                self.cal_calibration_previous_button["state"] = "normal"

                return

        # Take geometric mean of thresholds
        for i in range(6):
            product = 1
            for j in range(len(threshold_list)):
                product *= threshold_list[j][i]

            average_threshold = round(product ** (1 / len(threshold_list)))
            self.cal_normalization_thresholds.append(average_threshold)

            self.cal_calibration_progress_bar["value"] += 1

        self.cal_calibration_textbox.insert(tkinter.END, f"\n\nPreparing brightness maps...\n")
        self.cal_calibration_textbox.see(tkinter.END)
        for i in range(len(self.cal_confirmed_files)):
            image_name = self.cal_confirmed_file_names[i]

            self.cal_calibration_textbox.insert(tkinter.END, f"\nCalculating brightness map for {image_name}...")
            self.cal_calibration_textbox.see(tkinter.END)
            current_brightness_map_list = []
            for j in range(len(self.cal_blurred_images[i])):
                width, height = self.cal_blurred_images[i][j].size
                image_array = numpy.array(self.cal_blurred_images[i][j].convert("HSV"))

                # Split the picture into sections
                section_width = width / self.cal_confirmed_section_number
                section_height = height / self.cal_confirmed_section_number
                normalization_threshold_array = numpy.zeros(
                    (self.cal_confirmed_section_number, self.cal_confirmed_section_number))

                # For each section, sample pixels, then find the normalization threshold
                for section_x in range(self.cal_confirmed_section_number):
                    for section_y in range(self.cal_confirmed_section_number):

                        sampled_values = []
                        for x in range(self.cal_confirmed_pixel_number):
                            for y in range(self.cal_confirmed_pixel_number):
                                pixel_x = round(
                                    section_width * (section_x + ((x + 0.5) / self.cal_confirmed_pixel_number)))
                                pixel_y = round(
                                    section_height * (section_y + ((y + 0.5) / self.cal_confirmed_pixel_number)))

                                sampled_values.append(image_array[pixel_y][pixel_x][2])

                        sampled_values.sort()
                        normalization_threshold_array[section_x][section_y] = \
                            sampled_values[self.cal_normalization_thresholds[j] - 1]
                        self.cal_calibration_progress_bar["value"] += 1

                # Parse through the image array and calculate brightness map
                brightness_map = numpy.zeros((height, width))
                for x in range(width):
                    for y in range(height):
                        brightness_map[y][x] = self.calculate_threshold(
                            x, y,
                            self.cal_confirmed_section_number,
                            normalization_threshold_array,
                            section_width, section_height)
                current_brightness_map_list.append(brightness_map)
                self.cal_calibration_progress_bar["value"] += 1

            self.cal_brightness_maps.append(current_brightness_map_list)

        # Take average of brightness deviations and set as blur radius
        if self.cal_confirmed_blur_radius < 0:
            average_brightness_deviation = sum(brightness_deviation_list) / len(brightness_deviation_list)
            self.cal_confirmed_blur_radius = \
                max(min(round(25 * average_brightness_deviation / ((-self.cal_confirmed_blur_radius) ** 2.5)), 5), 1)

        # Calculate noise filter

        current_blur_number = self.cal_confirmed_blur_radius
        if self.cal_confirmed_noise_filter == -1:
            brightness_deviation_list = []
            for i in range(len(self.cal_confirmed_files)):

                width, height = self.cal_blurred_images[i][current_blur_number].size
                image_array = numpy.array(self.cal_blurred_images[i][current_blur_number].convert("HSV"))

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
            self.cal_confirmed_noise_filter = \
                max(min(round(round((average_brightness_deviation / 10) / 0.05) * 0.05, 2), 0.5), 0)

        self.cal_calibration_textbox.insert(tkinter.END, f"\n\nPreparing output images...\n")
        self.cal_calibration_textbox.see(tkinter.END)
        for i in range(len(self.cal_confirmed_files)):
            image_name = self.cal_confirmed_file_names[i]

            self.cal_calibration_textbox.insert(tkinter.END, f"\nNormalizing {image_name}...")
            self.cal_calibration_textbox.see(tkinter.END)
            width, height = self.cal_blurred_images[i][current_blur_number].size
            image_array = numpy.array(self.cal_blurred_images[i][current_blur_number].convert("HSV"))

            # Normalize image using calculated brightness map
            normalized_image_array = self.normalize_image(
                image_array,
                self.cal_brightness_maps[i][current_blur_number],
                width, height,
                self.cal_confirmed_noise_filter)

            normalized_image = Image.fromarray(normalized_image_array.astype("uint8"), "HSV").convert("RGB")
            self.cal_processed_files.append(normalized_image)
            self.cal_calibration_progress_bar["value"] += 1

        self.cal_calibration_textbox.insert(
            tkinter.END,
            "\n\nCalibration complete! Press the \"Show result\" button to view calibration results.")
        self.cal_calibration_textbox.see(tkinter.END)

        # Update results tab with new results
        self.cal_confirmed_normal_threshold = self.cal_normalization_thresholds[current_blur_number]
        self.results_go_to_picture(0, "cal")
        self.cal_results_settings_value_label.config(
            text=f"{self.cal_confirmed_image_compression}\n"
                 f"{self.cal_confirmed_channel}\n"
                 f"{self.cal_confirmed_blur_radius}\n"
                 f"{self.cal_confirmed_section_number}\n"
                 f"{self.cal_confirmed_pixel_number}\n"
                 f"{self.cal_confirmed_normal_threshold}\n"
                 f"{self.cal_confirmed_noise_filter}\n"
                 f"{self.cal_confirmed_line_number}")
        self.cal_results_blur_radius.set(str(self.cal_confirmed_blur_radius))
        self.cal_results_noise_filter.set(str(self.cal_confirmed_noise_filter))

        # Re-enable tabs at the conclusion of calibration, then enable the next and previous buttons
        self.calibration_side_tabs.tab(0, state="normal")
        self.calibration_side_tabs.tab(1, state="normal")
        self.calibration_side_tabs.tab(3, state="normal")
        self.cal_calibration_previous_button["state"] = "normal"
        self.cal_calibration_confirm_button["state"] = "normal"

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

    def results_go_to_picture(self, image_number, tab):
        """
        Updates the results picture, label, and arrows for navigating the processed pictures
        :param image_number: Index of the processed image to go to
        :param tab: "cal" (calibration) or "anl" (analysis)
        :return: None
        """
        if tab == "cal":

            # Disable left arrow if at first image, and disable right arrow if at last image
            if image_number == 0:
                self.cal_results_picture_left_arrow_button["state"] = "disabled"
                self.cal_results_picture_right_arrow_button["state"] = "normal"
            elif image_number == len(self.cal_confirmed_files) - 1:
                self.cal_results_picture_left_arrow_button["state"] = "normal"
                self.cal_results_picture_right_arrow_button["state"] = "disabled"
            else:
                self.cal_results_picture_left_arrow_button["state"] = "normal"
                self.cal_results_picture_right_arrow_button["state"] = "normal"

            # Update text label
            self.cal_results_picture_label.configure(text=self.cal_confirmed_file_names[image_number])

            # Update image
            self.draw_results_image(image_number, tab)

            # Update current viewed image variable
            self.cal_current_viewed_picture = image_number
        elif tab == "anl":

            # Disable left arrow if at first image, and disable right arrow if at last image
            if image_number == 0:
                self.anl_results_picture_left_arrow_button["state"] = "disabled"
                self.anl_results_picture_right_arrow_button["state"] = "normal"
            elif image_number == len(self.anl_confirmed_files) - 1:
                self.anl_results_picture_left_arrow_button["state"] = "normal"
                self.anl_results_picture_right_arrow_button["state"] = "disabled"
            else:
                self.anl_results_picture_left_arrow_button["state"] = "normal"
                self.anl_results_picture_right_arrow_button["state"] = "normal"

            # Update text label
            self.anl_results_picture_label.configure(text=self.anl_confirmed_file_names[image_number])

            # Update image
            self.draw_results_image(image_number, tab)

            # Update current viewed image variable
            self.anl_current_viewed_picture = image_number

    def resize_image(self, image, width, height):
        """
        Resize an image to fit within a rectangle
        :param image: Image object containing the image to be resized
        :param width: maximum allowable width
        :param height: maximum allowable height
        :return: Resized image
        """
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

    def draw_results_image(self, image_number, tab):
        """
        Takes an image object, resizes it, then draws the image onto the results page
        :param image_number: Index of the processed image
        :param tab: "cal" (calibration) or "anl" (analysis)
        :return: None
        """
        image, label = 0, 0
        if tab == "cal":
            image = self.cal_processed_files[image_number]
            label = self.cal_results_picture_label
        elif tab == "anl":
            image = self.anl_processed_files[image_number]
            label = self.anl_results_picture_label

        # Resize image according to label's width and height
        label_width = label.winfo_width()
        label_height = label.winfo_height()
        displayed_image = image.copy()
        displayed_image = self.resize_image(displayed_image, label_width, label_height - 20)

        # Convert to tkinter image and display
        tk_displayed_image = ImageTk.PhotoImage(displayed_image)
        label.configure(image=tk_displayed_image)
        label.image = tk_displayed_image  # Prevent garbage collection

    def cal_update_results(self, new_blur, new_noise_filter):
        """
        Used to update the results when the blur/noise options are changed
        :param new_blur: New blur value
        :param new_noise_filter: New noise threshold value
        :return: None
        """

        # TODO figure out why i have blur_number
        blur_number = new_blur

        # Update internal blur radius and noise filter values
        self.cal_confirmed_blur_radius = new_blur
        self.cal_confirmed_normal_threshold = self.cal_normalization_thresholds[blur_number]
        self.cal_confirmed_noise_filter = new_noise_filter

        # Check for existing threads. If previous threads exist, prompt them to stop
        if self.cal_noise_filter_threads:
            for thread in self.cal_noise_filter_threads:
                thread.stop = True

        # Redraw images using new thread
        noise_filter_thread = self.CalNoiseCalculationThread(self)
        self.cal_noise_filter_threads.append(noise_filter_thread)
        noise_filter_thread.start()

        # Disable the slider and spinbox widgets
        self.cal_results_settings_blur_slider["state"] = "disabled"
        self.cal_results_settings_blur_spinbox["state"] = "disabled"
        self.cal_results_settings_noise_slider["state"] = "disabled"
        self.cal_results_settings_noise_spinbox["state"] = "disabled"

        # Update the label text
        settings_values = self.cal_results_settings_value_label.cget("text").split("\n")
        settings_values[2] = str(self.cal_confirmed_blur_radius)
        settings_values[5] = str(self.cal_confirmed_normal_threshold)
        settings_values[6] = str(self.cal_confirmed_noise_filter)
        self.cal_results_settings_value_label["text"] = "\n".join(settings_values)

    def cal_results_blur_spinbox_update(self, _):
        """
        Takes the current value from the blur spinbox in the calibration results page and updates the processed images
        :param _: Unknown - required for tkinter but is unused
        :return: None
        """
        self.sanitize_input(self.cal_results_blur_radius, False, "int", 0, 5)
        self.cal_update_results(int(self.cal_results_blur_radius.get()), self.cal_confirmed_noise_filter)

    def cal_results_noise_spinbox_update(self, _):
        """
        Takes the current value from the noise spinbox in the calibration results page and updates the processed images
        :param _: Unknown - required for tkinter but is unused
        :return: None
        """
        self.sanitize_input(self.cal_results_noise_filter, False, "float", -0.5, 0.5)
        self.cal_update_results(self.cal_confirmed_blur_radius, float(self.cal_results_noise_filter.get()))

    def cal_save_settings(self):
        """
        Opens a file select screen and saves the current calibration output to a file at the selected location
        :return: None
        """
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

            with open(save_path + "Settings " + self.current_version + ".txt", mode="w") as settings_file:
                settings_file.write(
                    f"compressed_image_size = {self.cal_confirmed_image_compression}\n"
                    f"channel = {self.cal_confirmed_channel}\n"
                    f"blur_radius = {self.cal_confirmed_blur_radius}\n"
                    f"section_size = {self.cal_confirmed_section_number}\n"
                    f"pixels_sampled = {self.cal_confirmed_pixel_number}\n"
                    f"normalization_cutoff = {self.cal_confirmed_normal_threshold}\n"
                    f"noise_cutoff = {self.cal_confirmed_noise_filter}\n"
                    f"lines = {self.cal_confirmed_line_number}")

            for i in range(len(self.cal_processed_files)):
                image_name = ".".join(self.cal_confirmed_file_names[i].split(".")[:-1])
                image = self.cal_processed_files[i]
                image.save(save_path + image_name + "_processed.png")

            messagebox.showinfo(
                "Settings saved successfully",
                "The settings have been saved successfully to:\n\n" +
                save_path)

    def anl_add_settings(self):
        """
        Opens a file select screen, where a calibration settings file can be imported. Scans the settings and imports
        the calibration settings
        :return: None
        """

        file_path = filedialog.askopenfilename()
        if file_path:
            if file_path.lower().endswith(".txt"):
                with open(file_path, mode="r") as settings:
                    setting_list = settings.readlines()

                    for setting in setting_list:
                        if "compressed_image_size" in setting:
                            self.anl_image_compression = int(setting[len("compressed_image_size = "):])
                        elif "channel" in setting:
                            self.anl_channel_selection = int(setting[len("channel = "):])
                        elif "blur_radius" in setting:
                            self.anl_blur_radius = int(setting[len("blur_radius = "):])
                        elif "section_size" in setting:
                            self.anl_section_number = int(setting[len("section_size = "):])
                        elif "pixels_sampled" in setting:
                            self.anl_pixel_number = int(setting[len("pixels_sampled = "):])
                        elif "normalization_cutoff" in setting:
                            self.anl_normal_threshold = int(setting[len("normalization_cutoff = "):])
                        elif "noise_cutoff" in setting:
                            self.anl_noise_filter = float(setting[len("noise_cutoff = "):])
                        elif "lines" in setting:
                            self.anl_line_number = int(setting[len("lines = "):])

                    # Update label values in settings page
                    self.anl_settings_value_label.config(
                        text=f"{self.anl_image_compression}\n"
                             f"{self.anl_channel_selection}\n"
                             f"{self.anl_blur_radius}\n"
                             f"{self.anl_section_number}\n"
                             f"{self.anl_pixel_number}\n"
                             f"{self.anl_normal_threshold}\n"
                             f"{self.anl_noise_filter}\n"
                             f"{self.anl_line_number}")

                    # Enable analysis button if files are confirmed
                    if self.anl_input_files == self.anl_confirmed_files:
                        self.anl_settings_confirm_button["state"] = "normal"

                    self.anl_has_uploaded_settings = True

            else:
                messagebox.showinfo(
                    "Incompatible file type selected",
                    "Incompatible file type selected!\n\nThis program can only accept TXT files.")

    def anl_go_to_analysis(self):
        """
        Sets the input variables for the analysis, sets the progress bar, and starts a thread to run the calibration
        :return: None
        """

        # Determine settings
        self.anl_confirmed_image_compression = self.anl_image_compression
        self.anl_confirmed_channel = self.anl_channel_selection
        self.anl_confirmed_blur_radius = self.anl_blur_radius
        self.anl_confirmed_section_number = self.anl_section_number
        self.anl_confirmed_pixel_number = self.anl_pixel_number
        self.anl_confirmed_normal_threshold = self.anl_normal_threshold
        self.anl_confirmed_noise_filter = self.anl_noise_filter
        self.anl_confirmed_line_number = self.anl_line_number

        # Set progress bar to 0, delete text in textbox, and clear results
        self.anl_processed_files = []
        self.anl_IJOQ_list = []
        progress_bar_maximum = len(self.anl_confirmed_files) * (6 + (self.anl_confirmed_section_number ** 2))
        self. anl_analysis_progress_bar.config(maximum=progress_bar_maximum)
        self.anl_analysis_progress_bar["value"] = 0
        self.anl_analysis_textbox.delete(1.0, tkinter.END)

        # Move to the analysis screen
        self.analysis_side_tabs.tab(2, state="normal")
        self.analysis_side_tabs.select(2)

        # Disable other tabs
        self.analysis_side_tabs.tab(0, state="disabled")
        self.analysis_side_tabs.tab(1, state="disabled")
        self.analysis_side_tabs.tab(3, state="disabled")
        self.anl_analysis_previous_button["state"] = "disabled"
        self.anl_analysis_confirm_button["state"] = "disabled"

        analysis_thread = Thread(target=self.anl_run_analysis, daemon=True)
        analysis_thread.start()

    def anl_run_analysis(self):
        """
        Runs the analysis. Should be run as a thread, otherwise the GUI won't update properly
        :return: None
        """

        # Run analysis
        for file in self.anl_confirmed_files:
            # Determine the image name
            image_name = file.split("/")[-1]

            try:
                self.anl_analysis_textbox.insert(tkinter.END, f"Analyzing {image_name}...")
                self.anl_analysis_textbox.see(tkinter.END)

                image = Image.open(file)
                width, height = image.size
                compression_amount = (self.anl_confirmed_image_compression / 2) * (width + height) / (width * height)
                image = image.resize((round(compression_amount * width), round(compression_amount * height)))
                width, height = image.size

                # Take the RGB values from all the pixels in the image as an array
                image_array = numpy.array(image.convert("RGB"))

                # Extract channel
                self.anl_analysis_textbox.insert(tkinter.END, f"\nExtracting channel from {image_name}...")
                self.anl_analysis_textbox.see(tkinter.END)
                for x in range(width):
                    for y in range(height):
                        image_array[y][x] = [image_array[y][x][self.anl_confirmed_channel]] * 3

                # Apply blur
                self.anl_analysis_textbox.insert(tkinter.END, f"\nApplying blur to {image_name}...")
                self.anl_analysis_textbox.see(tkinter.END)
                image = Image.fromarray(image_array.astype("uint8"))
                blurred_image = image.filter(ImageFilter.GaussianBlur(radius=self.anl_confirmed_blur_radius))
                image_array = numpy.array(blurred_image.convert("HSV"))
                self.anl_analysis_progress_bar["value"] += 1

                # Split the picture into sections
                self.anl_analysis_textbox.insert(tkinter.END, f"\nCalculating threshold values for {image_name}...")
                self.anl_analysis_textbox.see(tkinter.END)
                section_width = width / self.anl_confirmed_section_number
                section_height = height / self.anl_confirmed_section_number
                normalization_threshold_array = numpy.zeros(
                    (self.anl_confirmed_section_number, self.anl_confirmed_section_number))

                # For each section, sample pixels, then find the normalization threshold
                for section_x in range(self.anl_confirmed_section_number):
                    for section_y in range(self.anl_confirmed_section_number):

                        sampled_values = []
                        for x in range(self.anl_confirmed_pixel_number):
                            for y in range(self.anl_confirmed_pixel_number):
                                pixel_x = round(
                                    section_width * (section_x + ((x + 0.5) / self.anl_confirmed_pixel_number)))
                                pixel_y = round(
                                    section_height * (section_y + ((y + 0.5) / self.anl_confirmed_pixel_number)))

                                sampled_values.append(image_array[pixel_y][pixel_x][2])

                        sampled_values.sort()
                        normalization_threshold_array[section_x][section_y] = \
                            sampled_values[self.anl_confirmed_normal_threshold - 1]
                        self.anl_analysis_progress_bar["value"] += 1

                # Parse through the image array and calculate brightness map
                self.anl_analysis_textbox.insert(tkinter.END, f"\nCalculating brightness map for {image_name}...")
                self.anl_analysis_textbox.see(tkinter.END)
                brightness_map = numpy.zeros((height, width))
                for x in range(width):
                    for y in range(height):
                        brightness_map[y][x] = self.calculate_threshold(
                            x, y,
                            self.anl_confirmed_section_number,
                            normalization_threshold_array,
                            section_width, section_height)
                self.anl_analysis_progress_bar["value"] += 1

                # Normalize image using calculated brightness map
                normalized_image_array = self.normalize_image(
                    image_array,
                    brightness_map,
                    width, height,
                    self.anl_confirmed_noise_filter)
                normalized_image = Image.fromarray(normalized_image_array.astype("uint8"), "HSV").convert("RGB")
                self.anl_processed_files.append(normalized_image)
                self.anl_analysis_progress_bar["value"] += 1

                # Draw horizontal lines
                self.anl_analysis_textbox.insert(tkinter.END, f"\nCalculating IJOQ for {image_name}...")
                self.anl_analysis_textbox.see(tkinter.END)
                cell_border_frequency = 0
                for y in range(self.anl_confirmed_line_number):
                    pixel_y = round((y + 0.5) * height / self.anl_confirmed_line_number)

                    previous_pixel = image_array[pixel_y][0][2]
                    for x in range(1, width):
                        current_pixel = image_array[pixel_y][x][2]
                        # If the line detects a color change (i.e. black to white or white to black)
                        if not previous_pixel == current_pixel:
                            cell_border_frequency += 0.5 / width

                        # Set current pixel as the previous pixel before moving to the next pixel
                        previous_pixel = current_pixel

                # Increment progress bar
                self.anl_analysis_progress_bar["value"] += 1

                # Repeat the same steps vertical lines
                for x in range(self.anl_confirmed_line_number):
                    pixel_x = round((x + 0.5) * width / self.anl_confirmed_line_number)

                    previous_pixel = image_array[0][pixel_x][2]
                    for y in range(1, height):
                        current_pixel = image_array[y][pixel_x][2]
                        if not previous_pixel == current_pixel:
                            cell_border_frequency += 0.5 / height

                        # Set current pixel as the previous pixel before moving to the next pixel
                        previous_pixel = current_pixel

                # Increment progress bar
                self.anl_analysis_progress_bar["value"] += 1

                # Take average of all lines
                IJOQ = round(cell_border_frequency / (2 * self.anl_confirmed_line_number), 4)
                self.anl_analysis_textbox.insert(tkinter.END, f"\n{image_name} has an IJOQ value of {IJOQ}.\n\n")
                self.anl_analysis_textbox.see(tkinter.END)
                self.anl_IJOQ_list.append(IJOQ)
                self.anl_analysis_progress_bar["value"] += 1

            # File could not be opened
            except FileNotFoundError:
                # Print warning, re-enable file selection and settings, then stop function
                self.anl_analysis_textbox.insert(
                    tkinter.END, f"WARNING! Unable to find file for {image_name}!")
                self.anl_analysis_textbox.see(tkinter.END)

                self.analysis_side_tabs.tab(0, state="normal")
                self.analysis_side_tabs.tab(1, state="normal")
                self.anl_analysis_previous_button["state"] = "normal"

                return

        self.anl_analysis_textbox.insert(
            tkinter.END,
            "Analysis complete! Press the \"Show result\" button to view analysis results.")
        self.anl_analysis_textbox.see(tkinter.END)

        # Update results tab with new results
        self.results_go_to_picture(0, "anl")

        # Re-enable tabs at the conclusion of calibration, then enable the next and previous buttons
        self.analysis_side_tabs.tab(0, state="normal")
        self.analysis_side_tabs.tab(1, state="normal")
        self.analysis_side_tabs.tab(3, state="normal")
        self.anl_analysis_previous_button["state"] = "normal"
        self.anl_analysis_confirm_button["state"] = "normal"

    def anl_save_results(self):
        """
        Opens a file select screen and saves the analysis output to a folder at the selected location
        :return: None
        """
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

            with open(save_path + "IJOQ Results " + self.current_version + ".csv", mode="w", newline="") as results_file:
                data_writer = csv.writer(results_file)
                data_writer.writerow(["File name", "IJOQ"])
                for i in range(len(self.anl_confirmed_files)):
                    data_writer.writerow([self.anl_confirmed_file_names[i], self.anl_IJOQ_list[i]])

            for i in range(len(self.anl_processed_files)):
                image_name = ".".join(self.anl_confirmed_file_names[i].split(".")[:-1])
                image = self.anl_processed_files[i]
                image.save(save_path + image_name + "_processed.png")

            messagebox.showinfo(
                "Results saved successfully",
                "The analysis results have been saved successfully to:\n\n" +
                save_path)



    def gui_start(self):
        self.root.mainloop()

def send_message(message_title, message):
    messagebox.showinfo(message_title, message)


