import subprocess
import sys

required_library = ("numpy", "pillow", "requests")

subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])

for library in required_library:
    print("Installing " + library + "...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", library])

input("Done! Press enter to finish")
