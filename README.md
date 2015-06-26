# CMIXIDE
Integrated Development Environment for RTcmix

## Installation
Place the cmixide.py file and the gui folder inside your RTcmix/bin installation.  
Some Linux distributions (eg. Ubuntu) don't include the Tkinter python library. You will need to  
`apt-get install python-tkinter`

## Running
Just `cd` to your RTcmix/bin folder and type `python cmixide.py`

For convenience, you may prefer to put these files in a separate location, and then `cd` to your RTcmix/bin folder and create a symlink:  
`ln -s [your-cmixide-folder]/cmixide.py cmixide`  
`chmod 755 cmixide`  
This will allow you to run cmixide from anywhere by just typing `cmixide` (as long as you have RTcmix/bin on your PATH)

## Finding your CMIX and PYCMIX binaries
If cmixide.py is running from your RTcmix/bin folder, it will find CMIX and PYCMIX automatically. Otherwise it will ask you for the location of your RTCMIX/bin folder, and add that to .cmixiderc for future use.
