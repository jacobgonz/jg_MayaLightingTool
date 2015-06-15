# jg_MayaLightingTool 

Running the tool:

import lightingTool

lightingTool.main()

-------

Setting the HDR Folder Path:

Option 1: Set the path when calling the main function

example: lightingTool.main("C:\myHdrFolderPath")

Option 2

Enter the path to the "HDR Folder Path:" field at the bottom of the HDRI Tab. Once you enter the path it will register to your user prefs. 

----------

HDR Folder Images Setup:

See the hdriFolder Example.
For every .exr or .hdr file you need a jpg Thumbnail named accordingly. 
Example: myHdriImage.exr -- myHdriImage_Thumb.jpg

----

Please note that the file resolution field is not supported yet. At the moment I am looking at the best approach to do this.

----- 

Maya Version and OS 
It has been tested mainly Windows and Mac OSX using Maya 2015.
Linux Centos 6.2 - Maya 2015

