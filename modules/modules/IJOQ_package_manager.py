from os import path, system, uname, listdir
import sys

def find_os():
    """
    Determine the system OS. Used to determine where error messages should be sent to upon import errors
    :return: "Linux", "Windows" or mac (Mac returns the codename for the current Mac version)
    """

    return uname().sysname

def send_message(message):
    """
    Opens a terminal and sends a message on the terminal.
    Used for if tkinter's messagebox doesn't work (ie during import errors)
    :param message: Message to send
    :return: None
    """

    system_os = find_os()

    # If the system OS is linux, open up the preferred terminal emulator and send the error message
    # Note: x-terminal-emulator isn't available on all distributions, but should be present in
    # all Debian-based distributions
    if system_os == "Linux":
        system(f"x-terminal-emulator --hold -e 'echo {message}'")
    elif system_os == "Windows":  # system OS is Windows
        system(f"start cmd /k echo {message}")
    else:  # system OS is Mac
        system(f"osascript -e 'echo {message}'")

def check_install():
    """
    Checks if the required libraries are installed and checks if the venv and .desktop file are set up on Linux systems
    :return: True if all are set up and False if at least one condition is not met
    """

    system_os = find_os()

    if system_os == "Linux":
        # Check if tkinter can be imported. Because tkinter is installed globally, it should not matter if
        # script is run from a venv or not
        try:
            import tkinter
        except ImportError:
            return False
        else:

            # Check if the venv exists
            if not path.isdir(path.expanduser("~/IJOQ-venv/lib/")):
                return False

            # Extract the python version from the venv
            python_version = listdir(path.expanduser("~/IJOQ-venv/lib/"))

            # Check within the venv path for requests, pillow, and numpy
            for folder in python_version:
                package_path = path.expanduser(f"~/IJOQ-venv/lib/{folder}/site-packages")

                if path.isdir(f"{package_path}/requests/") \
                    and path.isdir(f"{package_path}/PIL/") \
                    and path.isdir(f"{package_path}/numpy/"):

                    # Check for a .desktop file in ~/.local/share/applications
                    if path.exists(path.expanduser("~/.local/share/applications/IJOQ.desktop")):
                        return True

            return False

    else: # System OS is Windows or Mac

        # Check if modules are installed by attempting to import
        try:
            import tkinter
            import pillow
            import numpy
            import requests
        except ImportError:
            return False
        else:
            return True

def install(directory):
    """
    Installs the required libraries for IJOQ. Also sets up a venv and a .desktop file on Linux systems
    :param directory: Working directory of IJOQ
    :return: None
    """

    system_os = find_os()

    # If the system OS is Linux, run the Linux setup script
    if system_os == "Linux":
        system(f"'{directory}/scripts/IJOQ Linux Setup Script.sh'")
    else: # system OS is Windows or Mac

        # Update pip, then use pip to install libraries
        system(f"{sys.executable} -m pip install --upgrade pip")
        system(f"{sys.executable} -m pip install numpy pillow requests")

        input("Done! Press enter to finish")

def uninstall(directory):
    """
    Uninstalls libraries
    :return: None
    """

    system_os = find_os()

    # If the system OS is Linux, run the Linux setup script
    if system_os == "Linux":
        system(f"'{directory}/scripts/IJOQ Linux Uninstall Script.sh'")
    else: # system OS is Windows or Mac

        # Use pip to uninstall libraries
        system(f"{sys.executable} -m pip uninstall numpy pillow requests")

        input("Done! Press enter to finish")

