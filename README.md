# IJOQ
This repository contains the Python scripts used in the paper, "Dynamic Python-based method provides robust analysis of intercellular junction organization during *S. pneumoniae* infection of the respiratory epithelium." More specifically, it contains the set-up script (*IJOQ Setup.py*) and the IJOQ script (*IJOQ.py*). In version 1.0.1, the calibration script ("IJOQ Calibration.py") was merged with the IJOQ script into a singular script. It also includes the Simulator script (*Simulator.py*) that was used to generate simulated monolayer images. The project is released under the GNU General Public License version 3. In brief, users are free to download, share, and modify any and all parts of this project; however, any projects derived from the IJOQ project must also be released under the GNU General Public License as well. The script functions on Windows and Mac. It has not been tested on Linux. The repository is maintained by Devons Mo.

# How to Use

To set up the IJOQ script, first install the latest version of Python 3 from https://www.python.org/downloads/ and download the latest verson of IJOQ from https://github.com/DevonsMo/IJOQ/releases. Note that the IJOQ script requires Python version 3.10 or later to run. Next, run *IJOQ Setup.py* with Python. This can generally be performed by double clicking the file. If this does not work, ensure that your computer recognizes .py files as Python executable files. The Setup script will install all the libraries required to run IJOQ: NumPy, Tkinter, and Pillow. On Mac, you may need to click on "Run" in the menu on the top of the screen after opening the file.

For each experimental protocol, junction of interest, cell type, or imaging settings, a calibration should be performed. Run *IJOQ.py* in the same way that the *IJOQ Setup.py* file was run. Under the "Calibrate IJOQ" tab, add at least 3 negative control images to analyze. Confirm the selection, then select the preferred analysis settings. Using "Basic" settings will cause the program to estimate the analysis parameters of the images. "Advanced" settings allows the user to manually input analysis parameters. In most cases, "Basic" settings is sufficient for IJOQ analysis. Click on "Run calibration" to begin the calibration process. Upon completion, click on "Show result" to view processed images and to save the calibration settings. Under this page, visually confirm that the processed images have been sufficiently thresholded. Adequately thresholded images will have thin yet consistently thick and solid lines. The blur radius and noise filter sliders at the bottom right of the results page may be used to adjust the calibration settings before saving. For optimal results, set the noise filter to as high as possible that can still produce reasonably thresholded images. Click on "Save settings" to save the calibration settings.

To perform IJOQ analysis on an image or a set of images, run *IJOQ.py*, then go to the "IJOQ analysis" tab. Add the images to be analyzed, then confirm the selection. Under the new page, select the calibration settings file obtained from calibration, then click on "Run analysis" to begin the analysis process. Upon completion, click on "Show result" to view processed images and to save the results. Under this page, you may visually inspect the processed images. Click on "Save result" to save the analysis results.

The Simulator script is not intended to be used for analysis and is only included for archival purposes.
