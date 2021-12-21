# Version 0.1.1 (Updated 9/24/2021)
# Made by Devons Mo

import subprocess
import sys

required_library = ("pillow", "numpy", "tk")

subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])

for library in required_library:
    subprocess.check_call([sys.executable, "-m", "pip", "install", library])

input()
