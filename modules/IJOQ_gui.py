import csv
from os import path, mkdir, walk
import tkinter
from tkinter import filedialog, ttk, messagebox
from PIL import ImageTk
import modules.IJOQ_backend as Backend

class GuiWindow:

    class MainTab:

        def __init__(self, parent, calculation_type, calculation_class):
            """
            Creates the GUI for either the calibration tab or the analysis tab
            :param parent: the class containing the main GUI window
            :param calculation_type: "calibration" or "analysis"
            :param calculation_class: the class containing either the calibration or analysis class
            """

            self.parent = parent
            self.calculation_type = calculation_type
            self.calculation_class = calculation_class

            # Create main tab
            main_frame = ttk.Frame(self.parent.upper_tabs)
            main_frame.pack(fill="both", expand=True)

            conditional_text = f'{"Calibrate IJOQ":^80s}' if self.calculation_type == "calibration" \
                else f'{"IJOQ analysis":^80s}'
            self.parent.upper_tabs.add(main_frame, text=conditional_text)

            # ==CALIBRATION==
            # Add calibration tabs
            self.sub_tabs = ttk.Notebook(main_frame)
            self.sub_tabs.pack(fill="both", expand=True)

            file_select_frame = ttk.Frame(self.sub_tabs)
            settings_frame = ttk.Frame(self.sub_tabs)
            calculation_frame = ttk.Frame(self.sub_tabs)
            results_frame = ttk.Frame(self.sub_tabs)
            file_select_frame.pack(fill="both", expand=True)
            settings_frame.pack(fill="both", expand=True)
            calculation_frame.pack(fill="both", expand=True)
            results_frame.pack(fill="both", expand=True)

            conditional_text = f'{"3. Calibration":^25s}'  if self.calculation_type == "calibration" \
                else f'{"3. Analysis":^25s}'
            self.sub_tabs.add(file_select_frame, text=f'{"1. Select images":^25s}')
            self.sub_tabs.add(settings_frame, text=f'{"2. Select settings":^25s}')
            self.sub_tabs.add(calculation_frame, text=conditional_text)
            self.sub_tabs.add(results_frame, text=f'{"4. View Results":^25s}')
            self.sub_tabs.tab(1, state="disabled")
            self.sub_tabs.tab(2, state="disabled")
            self.sub_tabs.tab(3, state="disabled")

            self.sub_tabs.bind(
                "<<NotebookTabChanged>>",
                lambda e: self.update_current_tab()) # TODO What is e doing?

            # ==CALIBRATION:SELECT IMAGE PAGE==
            # Add calibration frames
            # Frame for calibration file entry
            file_select_frame.columnconfigure(0, weight=1)
            file_select_frame.columnconfigure(1, weight=0)
            file_select_frame.rowconfigure(0, weight=0)
            file_select_frame.rowconfigure(1, weight=1)
            file_select_frame.rowconfigure(2, weight=0)

            # Add description label to the top

            if self.calculation_type == "calibration":
                conditional_text = \
                    ("Calibration is required to determine proper settings for IJOQ analysis. "
                    "Once calibrated, recalibrating is not required until the experimental protocol is changed.\n\n"
                    "To begin, please select at least 3 negative control images.\n"
                    "All files located in folders that have \"Output\" in their names will be automatically excluded.")
            else:
                conditional_text = \
                    ("Calibration should be performed before IJOQ analysis.\n\n"
                    "To begin IJOQ analysis, please select the images to be analyzed.\n"
                    "All files located in folders that have \"Output\" in their names will be automatically excluded.")

            file_description_label = ttk.Label(master=file_select_frame, text=conditional_text)
            file_description_label.bind(
                "<Configure>",
                lambda e, label=file_description_label: label.config(wraplength=label.winfo_width())) #TODO probably don't need e?
            file_description_label.grid(padx=10, pady=10, row=0, column=0, columnspan=2, sticky="nsew")

            # Add center frames
            file_list_frame = ttk.Frame(file_select_frame)
            file_options_frame = ttk.Frame(file_select_frame)
            file_list_frame.grid(padx=10, row=1, column=0, sticky="nsew")
            file_options_frame.grid(row=1, column=1, sticky="nsew")

            # Add file list # TODO: file name can get very long. Somehow you can scroll horizontally sometimes. Prevent horizontal scroll (or shorten name to fit in textbox)
            # TODO in file list, detect file name conflicts and show folder path if conflict occurs
            file_list_frame.columnconfigure(0, weight=1)
            file_list_frame.columnconfigure(1, weight=0)
            file_list_frame.rowconfigure(0, weight=0)
            file_list_frame.rowconfigure(1, weight=1)

            file_list_label = ttk.Label(master=file_list_frame, text="Selected files:")
            self.file_list_box = tkinter.Listbox(master=file_list_frame, selectmode=tkinter.EXTENDED)
            file_list_scrollbar = ttk.Scrollbar(master=file_list_frame, orient="vertical")
            self.file_list_box.config(yscrollcommand=file_list_scrollbar.set)
            file_list_scrollbar.config(command=self.file_list_box.yview)
            file_list_label.grid(row=0, column=0, sticky="nsew")
            self.file_list_box.grid(row=1, column=0, sticky="nsew")
            file_list_scrollbar.grid(row=1, column=1, sticky="ns")

            # Add file options
            file_add_button = ttk.Button(
                master=file_options_frame, text="Add file",
                command=self.add_file)
            folder_add_button = ttk.Button(
                master=file_options_frame, text="Add folder",
                command=self.add_folder)
            file_delete_button = ttk.Button(
                master=file_options_frame, text="Delete selection",
                command=self.del_file)
            file_clear_button = ttk.Button(
                master=file_options_frame, text="Clear all",
                command=self.clear_file)
            file_add_button.pack(padx=10, pady=2, fill="both")
            folder_add_button.pack(padx=10, pady=2, fill="both")
            file_delete_button.pack(padx=10, pady=2, fill="both")
            file_clear_button.pack(padx=10, pady=2, fill="both")

            # Add lower button
            self.file_select_button = ttk.Button(
                master=file_select_frame,
                text="Confirm selection",
                width=20,
                state="disabled",
                command=self.confirm_files)
            self.file_select_button.grid(padx=10, pady=10, row=2, column=1, sticky="se")

            if calculation_type == "calibration":
                # ==CALIBRATION:SETTINGS PAGE==
                # Frame for determining the settings
                settings_frame.columnconfigure(0, weight=1)
                settings_frame.columnconfigure(1, weight=1)
                settings_frame.rowconfigure(0, weight=1)
                settings_frame.rowconfigure(1, weight=0)

                # Add Basic and Advanced settings tab
                self.cal_settings_options_tabs = ttk.Notebook(settings_frame, style="centered.TNotebook")
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
                    lambda e, label=cal_settings_description_label: label.config(wraplength=label.winfo_width())) # TODO what is e doing?
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
                cal_settings_cell_number_x_spinbox = self.spinbox_setup(
                    cal_settings_basic_frame, self.calculation_class.cell_number_x,
                    False, "int", 0, 99)
                cal_settings_cell_number_y_spinbox = self.spinbox_setup(
                    cal_settings_basic_frame, self.calculation_class.cell_number_y,
                    False, "int", 0, 99)

                # Basic Setting Dropdown
                cal_settings_channel_dropdown = ttk.OptionMenu(
                    cal_settings_basic_frame, self.calculation_class.channel_selection,
                    self.calculation_class.channel_options[0], *self.calculation_class.channel_options)
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
                cal_settings_image_compression_spinbox = self.spinbox_setup(
                    cal_settings_advanced_frame, self.calculation_class.image_compression,
                    False, "int", 128, 1024)
                cal_settings_blur_radius_spinbox = self.spinbox_setup(
                    cal_settings_advanced_frame, self.calculation_class.blur_radius,
                    False, "int", 0, 5)
                cal_settings_section_number_spinbox = self.spinbox_setup(
                    cal_settings_advanced_frame, self.calculation_class.section_number,
                    False, "int", 0, 10)
                cal_settings_pixel_number_spinbox = self.spinbox_setup(
                    cal_settings_advanced_frame, self.calculation_class.pixel_number,
                    False, "int", 0, 99)
                cal_settings_noise_filter_spinbox = self.spinbox_setup(
                    cal_settings_advanced_frame, self.calculation_class.noise_filter,
                    False, "float", -0.5, 0.5)
                cal_settings_line_number_spinbox = self.spinbox_setup(
                    cal_settings_advanced_frame, self.calculation_class.line_number,
                    False, "int", 0, 99)

                # Advanced Settings Dropdown
                cal_settings_advanced_channel_dropdown = ttk.OptionMenu(
                    cal_settings_advanced_frame, self.calculation_class.channel_selection,
                    self.calculation_class.channel_options[0], *self.calculation_class.channel_options)
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

            else: # analysis

                # ==ANALYSIS:SETTINGS PAGE==
                settings_frame.columnconfigure(0, weight=0)
                settings_frame.columnconfigure(1, weight=1)
                settings_frame.columnconfigure(2, weight=0)
                settings_frame.rowconfigure(0, weight=1)
                settings_frame.rowconfigure(1, weight=0)
                settings_frame.rowconfigure(2, weight=2)
                settings_frame.rowconfigure(3, weight=0)

                # Description for the settings
                anl_settings_description_label = ttk.Label(
                    master=settings_frame,
                    text="Please upload the settings file obtained from calibration.",
                    anchor=tkinter.NW)
                anl_settings_description_label.grid(padx=10, pady=10, row=0, column=0, columnspan=3, sticky="nsew")

                # Parameter label for the settings
                anl_settings_label = ttk.Label(
                    master=settings_frame,
                    text="Parameters:")
                anl_settings_label.grid(padx=10, row=1, column=0, sticky="nsew")
                anl_settings_parameter_labels = ttk.Label(
                    master=settings_frame,
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
                    master=settings_frame,
                    anchor=tkinter.NW, width=20,
                    justify=tkinter.LEFT)
                self.anl_settings_value_label.grid(pady=2, row=2, column=1, sticky="nsew")

                # Add settings file button
                anl_add_settings_button = ttk.Button(
                    master=settings_frame, text="Upload settings",
                    command=self.anl_add_settings)
                anl_add_settings_button.grid(padx=10, row=1, rowspan=2, column=2, sticky="new")

            # Add previous and confirm button

            conditional_command = self.calculation_class.go_to_calibration if self.calculation_type == "calibration" \
                else self.calculation_class.go_to_analysis #TODO integrate better

            conditional_num = 1 if self.calculation_type == "calibration" else 3
            conditional_num2 = 1 if self.calculation_type == "calibration" else 2
            settings_previous_button = ttk.Button(
                master=settings_frame,
                text="Previous",
                width=20,
                command=self.go_to_previous_page)
            self.settings_confirm_button = ttk.Button(
                master=settings_frame,
                text="Run calibration",
                width=20,
                state="disabled",
                command=conditional_command)
            settings_previous_button.grid(padx=10, pady=10, row=conditional_num, column=0, sticky="sw")
            self.settings_confirm_button.grid(padx=10, pady=10, row=conditional_num, column=conditional_num2, sticky="se")

            # ==CALIBRATION:CALIBRATION PAGE==
            calculation_frame.columnconfigure(0, weight=1)
            calculation_frame.columnconfigure(1, weight=1)
            calculation_frame.rowconfigure(0, weight=0)
            calculation_frame.rowconfigure(1, weight=1)
            calculation_frame.rowconfigure(2, weight=0)

            # Add a progress bar #TODO edit progress bar formula to make more smooth during the brightness map calculations
            self.calculation_progress_bar = ttk.Progressbar(
                master=calculation_frame,
                orient="horizontal",
                mode='determinate')
            self.calculation_progress_bar.grid(padx=10, pady=10, row=0, column=0, columnspan=2, sticky="ew")

            # Add a frame for text box and scrollbar
            calculation_text_frame = ttk.Frame(calculation_frame)
            calculation_text_frame.grid(padx=10, pady=0, row=1, column=0, columnspan=2, sticky="nsew")

            calculation_text_frame.columnconfigure(0, weight=1)
            calculation_text_frame.columnconfigure(1, weight=0)
            calculation_text_frame.rowconfigure(0, weight=1)

            # Add scroll bar for text box
            self.calculation_textbox = tkinter.Text(calculation_text_frame)
            self.calculation_textbox.bind(
                "<Key>",
                lambda e: "break")
            calculation_text_scrollbar = ttk.Scrollbar(master=calculation_text_frame, orient="vertical")
            self.calculation_textbox.config(yscrollcommand=calculation_text_scrollbar.set)
            calculation_text_scrollbar.config(command=self.calculation_textbox.yview)
            self.calculation_textbox.grid(row=0, column=0, sticky="nsew")
            calculation_text_scrollbar.grid(row=0, column=1, sticky="ns")

            # Add previous and confirm button
            self.calculation_previous_button = ttk.Button(
                master=calculation_frame,
                text="Previous",
                width=20,
                state="disabled",
                command=self.go_to_previous_page)
            self.calculation_confirm_button = ttk.Button(
                master=calculation_frame,
                text="Show result",
                width=20,
                state="disabled",
                command=lambda: self.sub_tabs.select(3))
            self.calculation_previous_button.grid(padx=10, pady=10, row=2, column=0, sticky="sw")
            self.calculation_confirm_button.grid(padx=10, pady=10, row=2, column=1, sticky="se")

            # ==CALIBRATION:RESULTS PAGE==
            results_frame.columnconfigure(0, weight=1)
            results_frame.columnconfigure(1, weight=0)
            results_frame.rowconfigure(0, weight=0)
            results_frame.rowconfigure(1, weight=1)
            results_frame.rowconfigure(2, weight=0)

            # Add description label
            if calculation_type == "calibration":
                conditional_text = \
                    ("If the basic settings were selected, "
                    "the calibration settings were estimated to the best of the program's abilities. "
                    "Please review the processed images and ensure that the identified "
                    "junctions are smooth and the noise filter is as high as possible without removing junctions. \n\n"
                    "You may edit the blur radius and the noise threshold at the bottom right "
                    "to make adjustments to the calibration settings before saving. "
                    "It may take a moment for the image to update after adjusting the blur radius or noise threshold.")
                conditional_num = 5
                conditional_num2 = 2
            else:
                conditional_text = \
                    ("Please review the processed images and ensure that the program is "
                    "adequately thresholding the images before saving the results.")
                conditional_num = 10
                conditional_num2 = 1

            results_description_label = ttk.Label(master=results_frame, text=conditional_text)
            results_description_label.bind(
                "<Configure>",
                lambda e, label=results_description_label: label.config(wraplength=label.winfo_width())) # TODO e probably not necessary?
            results_description_label.grid(
                padx=10, pady=conditional_num,
                row=0, column=0, columnspan=conditional_num2, sticky="new")

            # Frame for picture

            if calculation_type == "calibration":
                conditional_num = 5
                conditional_num2 = 1
            else:
                conditional_num = 10
                conditional_num2 = 2

            results_picture_frame = ttk.Frame(results_frame)
            results_picture_frame.grid(
                padx=conditional_num, pady=5,
                row=1, column=0, columnspan=conditional_num2, sticky="nsew")
            results_picture_frame.columnconfigure(0, weight=1)
            results_picture_frame.columnconfigure(1, weight=3)
            results_picture_frame.columnconfigure(2, weight=1)
            results_picture_frame.rowconfigure(0, weight=1)

            # Arrows for picture
            self.results_picture_left_arrow_button = ttk.Button(
                master=results_picture_frame,
                text="←",
                width=3,
                command=lambda: self.results_go_to_picture(self.calculation_class.current_viewed_picture - 1)
            )
            self.results_picture_right_arrow_button = ttk.Button(
                master=results_picture_frame,
                text="→",
                width=3,
                command=lambda: self.results_go_to_picture(self.calculation_class.current_viewed_picture + 1)
            )
            self.results_picture_left_arrow_button.grid(row=0, column=0, sticky="e")
            self.results_picture_right_arrow_button.grid(row=0, column=2, sticky="w")

            # Textbox for Picture

            self.results_picture_label = ttk.Label(results_picture_frame, compound=tkinter.TOP,
                                                       anchor=tkinter.CENTER)
            self.results_picture_label.grid(row=0, column=1, sticky="nsew")
            self.results_picture_label.bind(
                "<Configure>",
                lambda e: self.draw_results_image(self.calculation_class.current_viewed_picture)) # TODO e probably not necessary?

            if calculation_type == "calibration":

                # Frame for settings
                cal_results_settings_frame = ttk.Frame(results_frame)
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
                    variable=self.calculation_class.results_blur_radius,
                    length=200,
                    command=lambda e: self.calculation_class.results_blur_radius.set( # TODO what is e doing?
                        str(int(round(float(self.calculation_class.results_blur_radius.get()))))))
                self.cal_results_settings_blur_slider.bind(
                    "<ButtonRelease-1>",
                    lambda e: self.cal_update_results(int(self.calculation_class.results_blur_radius.get()),
                                                      self.calculation_class.confirmed_noise_filter))
                self.cal_results_settings_blur_slider.grid(padx=2, row=3, column=0, columnspan=2, sticky="ew")

                # Spinbox for the blur radius
                self.cal_results_settings_blur_spinbox = self.spinbox_setup(
                    cal_results_settings_frame, self.calculation_class.results_blur_radius,
                    False, "int", 0, 5)
                # FocusOut runs a special function here, so override the default FocusOut function
                self.cal_results_settings_blur_spinbox.bind(
                    "<FocusOut>",
                    self.cal_results_blur_spinbox_update)
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
                    variable=self.calculation_class.results_noise_filter,
                    length=200,
                    command=lambda e: self.calculation_class.results_noise_filter.set(
                        str(round(round(float(self.calculation_class.results_noise_filter.get()) / 0.005) * 0.005, 3))))
                self.cal_results_settings_noise_slider.bind(
                    "<ButtonRelease-1>",
                    lambda e: self.cal_update_results(self.calculation_class.confirmed_blur_radius,
                                                      float(self.calculation_class.results_noise_filter.get())))
                self.cal_results_settings_noise_slider.grid(padx=2, row=5, column=0, columnspan=2, sticky="ew")

                # Spinbox for the noise threshold
                self.cal_results_settings_noise_spinbox = self.spinbox_setup(
                    cal_results_settings_frame, self.calculation_class.results_noise_filter,
                    False, "float", -0.5, 0.5)
                # FocusOut runs a special function here, so override the default FocusOut function
                self.cal_results_settings_noise_spinbox.bind(
                    "<FocusOut>",
                    self.cal_results_noise_spinbox_update)
                self.cal_results_settings_noise_spinbox.grid(padx=2, row=5, column=2, sticky="e")

            # Add previous and confirm button

            conditional_text = "Save settings" if self.calculation_type == "calibration" else "Save results"
            conditional_command = self.cal_save_settings if self.calculation_type == "calibration" else self.anl_save_results
            results_previous_button = ttk.Button(
                master=results_frame,
                text="Previous",
                width=20,
                command=self.go_to_previous_page)
            results_save_button = ttk.Button(
                master=results_frame,
                text=conditional_text,
                width=20,
                command=conditional_command)
            results_previous_button.grid(padx=10, pady=10, row=2, column=0, sticky="sw")
            results_save_button.grid(padx=10, pady=10, row=2, column=1, sticky="se")

        def spinbox_setup(self, frame, variable_name, is_even, var_type, var_min, var_max):
            """
            Sets up a ttk spinbox and adds sanitization binding to the spinbox
            :param frame: the tk frame that the spinbox belongs to
            :param variable_name: variable that the spinbox controls (using tk.StringVar for some reason - check why)
            :param is_even: boolean for if variable should be always even or not (only used for ints)
            :param var_type: "int" or "float"
            :param var_min: minimum allowed value of the variable
            :param var_max: maximum allowed value of the variable
            :return: spinbox
            """

            # Set the appropriate validation command depending on the variable type
            if var_type == "int":
                validate_command = self.parent.vcmd_int
            else:  # variable type is float
                validate_command = self.parent.vcmd_float

            spinbox = ttk.Spinbox(
                frame, from_=var_min, to=var_max,
                wrap=True, textvariable=variable_name, width=6,
                validate="key", validatecommand=validate_command)
            spinbox.bind("<FocusOut>", lambda e: self.sanitize_input(variable_name, is_even, var_type, var_min,
                                                                     var_max))  # TODO Might need to fix...? check variable scope
            spinbox.bind("<Return>", lambda e: self.parent.root.focus())  # TODO what is e doing?

            return spinbox

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

        def add_file(self):  # TODO: each button remembers the previous directory that was used, but directory does not share across buttons. Make directory shared?
            """
            Opens a file selection window and adds the selected file to a listbox,
            then adds the file to the internal calibration/analysis file selection list.
            Can only pick 1 file at a time.
            :return: None
            """

            file_path = filedialog.askopenfilename()
            if file_path:
                if file_path.lower().endswith(self.parent.valid_image_types):
                    if "Output" not in file_path:
                        # Check current file count
                        if len(self.calculation_class.input_files) < 99:
                            file_name = file_path.split("/")[-1]
                            self.calculation_class.input_files.append(file_path)
                            self.file_list_box.insert(tkinter.END, file_name)
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
            # and at least 1 selection for analysis # TODO would be easier to just run a file update check function...

            if len(self.calculation_class.input_files) >= self.calculation_class.minimum_files:
                self.file_select_button["state"] = "normal"

        def add_folder(self):
            """
            Opens a folder selection window and adds all files within the folder to a listbox,
            then adds the files to the internal calibration/analysis file selection list.
            Can only pick 1 file at a time.
            :return: None
            """

            folder_path = filedialog.askdirectory()
            if folder_path:
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
                                if file.lower().endswith(self.parent.valid_image_types):
                                    # Check calibration file count
                                    if len(self.calculation_class.input_files) < 99:
                                        self.calculation_class.input_files.append(dirpath + "/" + file)
                                        self.file_list_box.insert(tkinter.END, file)
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
            if len(self.calculation_class.input_files) >= self.calculation_class.minimum_files:
                self.file_select_button["state"] = "normal"

        def del_file(self):  # TODO add function to highlight next file in file list? Also add option to select multiple files at once?
            """
            Deletes the selected option from the listbox and removes the file from
            the internal calibration/analysis file selection list.
            :return: None
            """

            # Delete from the largest index first to maintain the index order
            for i in sorted(self.file_list_box.curselection(), reverse=True):
                del self.calculation_class.input_files[i]
                self.file_list_box.delete(i)

            # Disable the confirm files button if there are less than the required number of selections
            if len(self.calculation_class.input_files) < self.calculation_class.minimum_files:
                self.file_select_button["state"] = "disabled"

        def clear_file(self):
            """
            Deletes all files from the listbox and removes the files from
            the internal calibration/analysis file selection list.
            :return: None
            """

            self.calculation_class.input_files.clear()
            self.file_list_box.delete(0, tkinter.END)

            # Disable the confirm files button
            self.file_select_button["state"] = "disabled"

        def confirm_files(self):
            """
            Confirm file selection. Copies the list of files to a confirmed_files list,
            then enables the calibration/analysis button (files must be confirmed in order to run calibration/analysis)
            :return: None
            """

            # Enable next page, then move to next page
            self.sub_tabs.tab(1, state="normal")
            self.sub_tabs.select(1)

            # Copy input files into confirmed files
            self.calculation_class.confirmed_files = self.calculation_class.input_files.copy()
            self.calculation_class.confirmed_file_names = self.file_list_box.get(0, self.file_list_box.size() - 1)

            # Enable the button to start calibration
            self.settings_confirm_button["state"] = "normal"

        def update_current_tab(self):
            """
            Updates the current tab when a tab change is detected
            :return: None
            """

            # If there are unconfirmed files in the input, send message that calibration cannot be performed
            if self.calculation_class.current_tab == 0 and self.calculation_class.input_files != self.calculation_class.confirmed_files:
                self.settings_confirm_button["state"] = "disabled"

                conditional_text = "a calibration" if calculation_type == "calibration" else "an analysis"

                messagebox.showinfo(
                    "Unconfirmed file selection",
                    "Unconfirmed file selection detected!\n\nYou will not be able "
                    f"to run {conditional_text} unless the file selection is confirmed.")

            self.calculation_class.current_tab = self.sub_tabs.index("current")

        def go_to_previous_page(self):
            """
            Goes to the previous page in the calibration or analysis process
            :return: None
            """

            self.sub_tabs.select(self.calculation_class.current_tab - 1)

        def results_go_to_picture(self, image_number):
            """
            Updates the results picture, label, and arrows for navigating the processed pictures
            :param image_number: Index of the processed image to go to
            :return: None
            """

            # Disable left arrow if at first image, and disable right arrow if at last image
            if image_number == 0:
                self.results_picture_left_arrow_button["state"] = "disabled"
                self.results_picture_right_arrow_button["state"] = "normal"
            elif image_number == len(self.calculation_class.confirmed_files) - 1:
                self.results_picture_left_arrow_button["state"] = "normal"
                self.results_picture_right_arrow_button["state"] = "disabled"
            else:
                self.results_picture_left_arrow_button["state"] = "normal"
                self.results_picture_right_arrow_button["state"] = "normal"

            # Update text label
            self.results_picture_label.configure(
                text=self.calculation_class.confirmed_file_names[image_number])

            # Update image
            self.draw_results_image(image_number)

            # Update current viewed image variable
            self.calculation_class.current_viewed_picture = image_number

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

        def draw_results_image(self, image_number):
            """
            Takes an image object, resizes it, then draws the image onto the results page
            :param image_number: Index of the processed image
            :return: None
            """
            image = self.calculation_class.processed_files[image_number]
            label = self.results_picture_label

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
            self.calculation_class.confirmed_blur_radius = new_blur
            self.calculation_class.confirmed_normal_threshold = self.calculation_class.normalization_thresholds[blur_number]
            self.calculation_class.confirmed_noise_filter = new_noise_filter

            # Check for existing threads. If previous threads exist, prompt them to stop
            if self.calculation_class.noise_filter_threads:
                for thread in self.calculation_class.noise_filter_threads:
                    thread.stop = True

            # Redraw images using new thread
            noise_filter_thread = Backend.NoiseCalculationThread(self, self.calculation_class)
            self.calculation_class.noise_filter_threads.append(noise_filter_thread)
            noise_filter_thread.start()

            # Disable the slider and spinbox widgets
            self.cal_results_settings_blur_slider["state"] = "disabled"
            self.cal_results_settings_blur_spinbox["state"] = "disabled"
            self.cal_results_settings_noise_slider["state"] = "disabled"
            self.cal_results_settings_noise_spinbox["state"] = "disabled"

            # Update the label text
            settings_values = self.cal_results_settings_value_label.cget("text").split("\n")
            settings_values[2] = str(self.calculation_class.confirmed_blur_radius)
            settings_values[5] = str(self.calculation_class.confirmed_normal_threshold)
            settings_values[6] = str(self.calculation_class.confirmed_noise_filter)
            self.cal_results_settings_value_label["text"] = "\n".join(settings_values)

        def cal_results_blur_spinbox_update(self, _):
            """
            Takes the current value from the blur spinbox in the calibration results page and updates the processed images
            :param _: Unknown - required for tkinter but is unused
            :return: None
            """

            self.sanitize_input(self.calculation_class.results_blur_radius, False, "int", 0, 5) # TODO: might be simpler if I use a dict for these variables? So that I don't have to retype these every time
            self.cal_update_results(int(self.calculation_class.results_blur_radius.get()),
                                    self.calculation_class.confirmed_noise_filter)

        def cal_results_noise_spinbox_update(self, _):
            """
            Takes the current value from the noise spinbox in the calibration results page and updates the processed images
            :param _: Unknown - required for tkinter but is unused
            :return: None
            """

            self.sanitize_input(self.calculation_class.results_noise_filter, False, "float", -0.5, 0.5)
            self.cal_update_results(self.calculation_class.confirmed_blur_radius,
                                    float(self.calculation_class.results_noise_filter.get()))

        def cal_save_settings(self):  # TODO: save with folder names to prevent naming conflict
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

                with open(save_path + "Settings " + self.parent.current_version + ".txt", mode="w") as settings_file:
                    settings_file.write(
                        f"compressed_image_size = {self.calculation_class.confirmed_image_compression}\n"
                        f"channel = {self.calculation_class.confirmed_channel}\n"
                        f"blur_radius = {self.calculation_class.confirmed_blur_radius}\n"
                        f"section_size = {self.calculation_class.confirmed_section_number}\n"
                        f"pixels_sampled = {self.calculation_class.confirmed_pixel_number}\n"
                        f"normalization_cutoff = {self.calculation_class.confirmed_normal_threshold}\n"
                        f"noise_cutoff = {self.calculation_class.confirmed_noise_filter}\n"
                        f"lines = {self.calculation_class.confirmed_line_number}")

                for i in range(len(self.calculation_class.processed_files)):
                    image_name = ".".join(self.calculation_class.confirmed_file_names[i].split(".")[:-1])
                    image = self.calculation_class.processed_files[i]
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
                                self.calculation_class.image_compression = int(setting[len("compressed_image_size = "):])
                            elif "channel" in setting:
                                self.calculation_class.channel_selection = int(setting[len("channel = "):])
                            elif "blur_radius" in setting:
                                self.calculation_class.blur_radius = int(setting[len("blur_radius = "):])
                            elif "section_size" in setting:
                                self.calculation_class.section_number = int(setting[len("section_size = "):])
                            elif "pixels_sampled" in setting:
                                self.calculation_class.pixel_number = int(setting[len("pixels_sampled = "):])
                            elif "normalization_cutoff" in setting:
                                self.calculation_class.normal_threshold = int(setting[len("normalization_cutoff = "):])
                            elif "noise_cutoff" in setting:
                                self.calculation_class.noise_filter = float(setting[len("noise_cutoff = "):])
                            elif "lines" in setting:
                                self.calculation_class.line_number = int(setting[len("lines = "):])

                        # Update label values in settings page
                        self.anl_settings_value_label.config(
                            text=f"{self.calculation_class.image_compression}\n"
                                 f"{self.calculation_class.channel_selection}\n"
                                 f"{self.calculation_class.blur_radius}\n"
                                 f"{self.calculation_class.section_number}\n"
                                 f"{self.calculation_class.pixel_number}\n"
                                 f"{self.calculation_class.normal_threshold}\n"
                                 f"{self.calculation_class.noise_filter}\n"
                                 f"{self.calculation_class.line_number}")

                        # Enable analysis button if files are confirmed
                        if self.calculation_class.input_files == self.calculation_class.confirmed_files:
                            self.settings_confirm_button["state"] = "normal"

                        self.calculation_class.has_uploaded_settings = True

                else:
                    messagebox.showinfo(
                        "Incompatible file type selected",
                        "Incompatible file type selected!\n\nThis program can only accept TXT files.")

        def anl_save_results(self):  # TODO save with folder names to prevent naming conflicts
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

                with open(save_path + "IJOQ Results " + self.parent.current_version + ".csv", mode="w",
                          newline="") as results_file:
                    data_writer = csv.writer(results_file)
                    data_writer.writerow(["File name", "IJOQ"])
                    for i in range(len(self.calculation_class.confirmed_files)):
                        data_writer.writerow([self.calculation_class.confirmed_file_names[i], self.calculation_class.IJOQ_list[i]])

                for i in range(len(self.calculation_class.processed_files)):
                    image_name = ".".join(self.calculation_class.confirmed_file_names[i].split(".")[:-1])
                    image = self.calculation_class.processed_files[i]
                    image.save(save_path + image_name + "_processed.png")

                messagebox.showinfo(
                    "Results saved successfully",
                    "The analysis results have been saved successfully to:\n\n" +
                    save_path)

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

        # Set window variables
        self.root = tkinter.Tk()
        self.root.geometry(f"{x}x{y}")
        self.root.minsize(min_x, min_y)
        self.root.title(title)
        icon = tkinter.PhotoImage(file=f"{directory}/{icon_name}")
        self.root.iconphoto(False, icon)

        self.valid_image_types = image_formats
        self.current_version = version

        # Initiate classes that handle calibration and analysis calculations
        self.calibration = Backend.Calculations("calibration", self)
        self.analysis = Backend.Calculations("analysis", self)

        # Set styles
        centered_tab_style = ttk.Style()
        centered_tab_style.configure("centered.TNotebook", tabposition="n")

        # Input validation
        self.vcmd_int = (self.root.register(self.validate_input_int), "%P")
        self.vcmd_float = (self.root.register(self.validate_input_float), "%P")

        # Add upper tabs
        self.upper_tabs = ttk.Notebook(self.root, style="centered.TNotebook")
        self.upper_tabs.pack(fill="both", expand=True)

        self.calibration_tab = self.MainTab(self, "calibration", self.calibration)
        self.analysis_tab = self.MainTab(self, "analysis", self.analysis)

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

    def gui_start(self):
        """
        Starts the gui window
        :return: None
        """
        self.root.mainloop()

def send_message(message_title, message):
    """
    Opens a tkinter messagebox
    :param message_title: Title of the message (shown in the window bar)
    :param message: Message to be shown
    :return: None
    """
    messagebox.showinfo(message_title, message)


