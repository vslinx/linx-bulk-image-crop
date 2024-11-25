# Bulk image cropper
Tool to crop a folder of images, mainly intended to make the workflow of cropping images for AI training easier.

![Open Settings Menu](/resources/img/screenshot1.png)

# Features
* Load Folder with images
* Crop one image after another
* Saving in same folder
* Duplication feature to save multiple singular objects/characters in one image
* Preview of all the saved crop'd images
* Keyboard shortcuts to save time

# Setup
### Requirements
Only applies if you want to start the program via your terminal through the checked out code instead of the release.
* Python installed (tested with ^3.10)

### Installation/How to use

#### Use .exe on Windows
Easiest way to use is to visit the [release](https://github.com/vslinx/linx-bulk-image-crop/releases) page and download the latest "crop.zip" which contains the .exe file with all required resources.
<br>
Simply start the .exe files and begin using the tool.

#### Check out code
If you want to start the software yourself via console because you don't trust the .exe or are using a different OS do the following:
1. Open your command line
2. navigate to the folder containing the checked out code
3. run the following command to install required librarys: <br>
    ``` pip install -r requirements.txt ```
4. start program by running the following command: <br>
    ``` py crop.py ```

#### Using the Tool
* Open the program as mentioned above and click on "Select Folder" in the top left context menu.
* Select the area of the image you'd like to either save or duplicate
![Select image area](/resources/img/screenshot2.png)
* Clicking the "save" icon will save current selection of the image and jump to the next image in the folder
* Clicking the "duplicate" icon will create a new image of your selectiong and will stay at the current image for you to make another selection (useful if you have multiple subjects in one image that you need to cut out)
* You can use the arrow keys on your keyboard or to the left and right of the program to navigate between images in the folder if you want to skip some or want to go back to previous ones
* At the bottom you see all of the images you created, clicking on one will open that image in your default image viewer
* All images will get saved inside the original directory of your selected folder containing the images, they will be in a new folder called "result"
* Clicking the "Settings" context menu on top will let you change the shortcuts for saving or duplicating images and switching to the previous or next image, this is very helpful if you're going through screen captures of a show and want to quickly go through a large dataset wihout having to click the buttons for save or duplicate every time