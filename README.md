# IJOQ
This repository contains the Python scripts used in the paper, "Dynamic Python-based method provides robust analysis of intercellular junction organization during *S. pneumoniae* infection of the respiratory epithelium." More specifically, it contains the set-up script (*IJOQ Setup.py*), the calibration script (*IJOQ Calibration.py*), and the IJOQ script (*IJOQ.py*). It also includes the Simulator script (*Simulator.py*) that was used to generate simulated monolayer images. The project is released under the GNU General Public License version 3. In brief, users are free to download, share, and modify any and all parts of this project; however, any projects derived from the IJOQ project must also be released under the GNU General Public License as well. The script functions on Windows and Mac. It has not been tested on Linux. The repository is maintained by Devons Mo.

# How to Use

To set up the IJOQ script, first install the latest version of Python 3 from https://www.python.org/downloads/ and download the latest verson of IJOQ from https://github.com/DevonsMo/IJOQ/releases. Next, run *IJOQ Setup.py* with Python. This can generally be performed by double clicking the file. If this does not work, ensure that your computer recognizes .py files as Python executable files. The Setup script will install all the libraries required to run IJOQ and the IJOQ calibration: NumPy, Tkinter, and Pillow. On Mac, you may need to click on "Run" in the menu on the top of the screen after opening the file.

For each new cell type or imaging settings, a calibration should be performed. Run *IJOQ Calibration.py* in the same way that the *IJOQ Setup.py* file was run. The script will request three negative control images to analyze, as well as ask for analysis settings. When the file selection window appears, please select the negative control images. Then, when the script prompts for analysis settings, please type in the desired numbers underneath the prompt and press enter. In general, the default settings should be sufficient unless otherwise noted. Settings derived from calibration can be saved as a .txt file after calibration. Check the calibration output images to ensure the calibration is sufficient. Images denoted with ~1 are intermediate images saved after the blur is applied. Images denoted with ~2 are final images. If the ~2 image has cell borders that are too thick (i.e. greater than ~1/2 of a cell's width), consider recalibrating with less blur. If the ~2 image has too much noise, consider recalibrating with a higher noise cutoff. Alternately, if not enough cell borders are visible in the ~2 image, the noise cutoff could be too aggressive. In this case, consider recalibrating with a lower noise cutoff. If the calibration appears sufficient, save the settings so that they may be imported during IJOQ analysis.

To perform IJOQ analysis on an image or a set of images, run *IJOQ.py* in the same way that the previous scripts were run. This script will first prompt for a single image to analyze. If analysis of a single image is sufficient, then an image can be selected. If multiple images are to be analyzed, then close the file selection window. This will prompt the script to request a folder instead. Use the folder selection window to select the folder to be analyzed. All images within the folder (even those that are within folders within the selected folder) will be analyzed. Folders with "Output" in their names will be ignored. After the desired input images are selected, a final file selection window will appear. This file selection is used to select the desired settings to be used. Select the .txt file obtained from calibration. Upon selection, analysis will begin. This process is fully automatic and does not require user supervision. After analysis of all selected images, the data will be automatically saved to a .csv file. If a single image was selected, analysis results will not be saved.

The Simulator script is not intended to be used for analysis and is only included for archival purposes.
