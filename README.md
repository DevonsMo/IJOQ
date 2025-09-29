# IJOQ
This repository contains the Python scripts used in the paper, "Dynamic Python-based method provides robust analysis of intercellular junction organization during *S. pneumoniae* infection of the respiratory epithelium." In version 1.0.1, the calibration script ("IJOQ Calibration.py") was merged with the IJOQ script into a singular script. The repository also includes the Simulator script (*Simulator.py*) that was used to generate simulated monolayer images. The project is released under the GNU General Public License version 3. In brief, users are free to download, share, and modify any and all parts of this project; however, any projects derived from the IJOQ project must also be released under the GNU General Public License as well. The script functions on Windows, Mac, and Linux (Debian-based distributions). The repository is maintained by Devons Mo with contributions from Nicole Homez.

# Setting up IJOQ

The process for setting up IJOQ differs depending on the OS. Please see the below steps and follow the appropriate instructions to set up IJOQ properly.

1. First, ensure that Python 3 is installed.
   * On Windows, download and install the latest version of Python 3 from https://www.python.org/downloads/
   * On Mac and Linux, Python 3 should be pre-installed. Go to the next step.
2. Download the latest version of IJOQ from https://github.com/DevonsMo/IJOQ/releases/latest. Extract the IJOQ files from the downloaded file.
3. Next, run *IJOQ Installer.py* with Python. The script will install all libraries required to run IJOQ: NumPy, Pillow, and Requests. The script will ask for a confirmation before installing. Type "install" then press enter to confirm the install.
   * On Windows, double click the file to run the script.
   * On Mac, double click the file to open the file. In the menu on the top of the screen, click on "Run" to run the script.
   * On Linux, *IJOQ Installer.py* can be run using terminal commands. First, locate where the file is. In the terminal, change the directory using the ```cd``` command so that working directory is where the file is (e.g. if the file is at *~/Downloads/IJOQ/IJOQ Installer.py*, then use this command: ```cd ~/Downloads/IJOQ/```). Then, run the file using the following command: ```python3 "IJOQ Installer.py"```. This setup script will set up a Python virtual environment and install the required libraries into the virtual environment. In addition, the script will also install Tkinter as a system-wide package. The script will also create an entry for IJOQ on the applications menu. A restart may be required for the entry to appear. Note that this script can only function on Linux distributions that can use the *apt* package manager (Debian, Ubuntu, Linux Mint, Pop!_OS, etc.). If the script does not work, ensure that the file *IJOQ/scripts/IJOQ Linux Setup Script.sh* is executable. This can often be done by checking the properties of the file and marking the file as executable. 

# Using IJOQ

To run IJOQ, run *IJOQ.py* in the same way that the *IJOQ Installer.py* file was run (for Windows and Mac). On Linux, IJOQ can be run by selecting the IJOQ entry from the applications menu.

For each experimental protocol, junction of interest, cell type, or imaging settings, a calibration should be performed. Under the "Calibrate IJOQ" tab, add at least 3 negative control images (images showing undisrupted junctions) to analyze. Confirm the selection, then select the preferred analysis settings. Using "Basic" settings will cause the program to estimate the analysis parameters of the images. "Advanced" settings allows the user to manually input analysis parameters. In most cases, "Basic" settings is sufficient for IJOQ analysis. Click on "Run calibration" to begin the calibration process. Upon completion, click on "Show result" to view processed images and to save the calibration settings. Under this page, visually confirm that the processed images have been sufficiently thresholded. Adequately thresholded images will have thin yet consistently thick and solid lines. The blur radius and noise filter sliders at the bottom right of the results page may be used to adjust the calibration settings before saving. For optimal results, set the noise filter to as high as possible that can still produce reasonably thresholded images. Click on "Save settings" to save the calibration settings.

To perform IJOQ analysis on an image or a set of images, go to the "IJOQ analysis" tab. Add the images to be analyzed, then confirm the selection. Under the next page, select the calibration settings file obtained from calibration, then click on "Run analysis" to begin the analysis process. Upon completion, click on "Show result" to view processed images and to save the results. Under this page, you may visually inspect the processed images. Click on "Save result" to save the analysis results.

The Simulator script is not intended to be used for analysis and is only included for archival purposes.

# Uninstalling IJOQ

To uninstall IJOQ, run *IJOQ Installer.py* in the same way that the file was run during setup. The script will ask for a confirmation before uninstalling. Type "uninstall" then press enter to confirm the uninstall. Note that the script will uninstall all required libraries. If other Python projects are present on the computer that use any of these packages, uninstalling may disrupt the functionality of these projects. If this occurs, ensure that the relevant packages are re-installed afterward.

On Linux, the uninstall procedure will also delete the Python virtual environment that was created during the setup process.
