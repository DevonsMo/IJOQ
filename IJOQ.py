# Devons Mo and Shane Nicole Homez 9/3/2025
# Global variables
valid_image_types = (".png", ".jpg", ".jpeg", ".tif", ".tiff")
current_version = "v1.3.2"

# Initialize program
if __name__ == "__main__":
    # Check if all required modules are present by importing them
    # Reports an error if the program is unable to open up the required modules
    try:
        import requests
        from os import path
        import modules.IJOQ_backend as Backend
        import modules.IJOQ_package_manager as Pacman

        # Not necessary in here
        import tkinter
        import PIL
        import numpy

    except (ModuleNotFoundError, ImportError) as e:

        # Set error message
        message = ("You may be missing a required library! "
                   "Be sure to run the IJOQ Setup before running this program! "
                   f"Please see below message for missing packages: \n{e}")

        Pacman.send_message(message)

    # Import is successful
    else:

        working_directory = path.dirname(path.abspath(__file__))

        # Opens up tkinter, set up window, and start IJOQ
        window = Backend.GuiWindow(800, 600,
                        750, 500,
                        f"IJOQ {current_version}", "IJOQ_icon.png",
                        valid_image_types, current_version, working_directory)

        # Check for updates
        latest_version_link = requests.get("https://github.com/DevonsMo/IJOQ/releases/latest")
        latest_version = latest_version_link.url.split("/")[-1]

        if current_version != latest_version:
            Backend.send_message("New update found!",
                                 "A new update has been released. "
                                 "Please download the new version at "
                                 "https://github.com/DevonsMo/IJOQ/releases/latest\n\n"
                                 f"Latest version: {latest_version}")

        window.gui_start()
