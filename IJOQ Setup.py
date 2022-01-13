# Version 0.1.2 (Updated 1/13/2022)
# Made by Devons Mo

import subprocess
import sys

required_library = ("pillow", "numpy", "tk")

subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])

for library in required_library:
    print("Installing " + library + "...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", library])

input("Done! Press enter to finish")
