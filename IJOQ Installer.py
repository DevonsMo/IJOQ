from os import path
import modules.IJOQ_package_manager as Pacman

working_directory = path.dirname(path.abspath(__file__))

is_installed = Pacman.check_install()

# Needs to be installed
if not is_installed:
    confirm = input("This script will install and set up IJOQ.\n\n"
                    "Type \"install\" to confirm. Otherwise, type \"quit\" to exit: ")

    while confirm != "install" and confirm != "quit":
        print(confirm)
        confirm = input("Unexpected input. Please type either \"install\" or \"quit\": ")

    if confirm == "install":
        Pacman.install(working_directory)

# If everything is installed, ask to uninstall
else:
    confirm = input("IJOQ appears to be installed. Would you like to uninstall IJOQ?\n"
                    "NOTE: The uninstaller will remove all required packages for IJOQ. "
                    "If you have other projects that use these packages, the functionality of those projects may be "
                    "disturbed. Make sure to re-install the relevant packages if this occurs.\n\n"
                    "Type \"uninstall\" to uninstall or \"quit\" to exit: ")

    while confirm != "uninstall" and confirm != "quit":
        confirm = input("Unexpected input. Please type either \"uninstall\" or \"quit\": ")

    if confirm == "uninstall":
        Pacman.uninstall(working_directory)
