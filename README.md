# Project 2 : Item Catalog

## Project Details:

You will develop an application that provides a list of items within a variety of categories as well as provide a user registration and authentication system. Registered users will have the ability to post, edit and delete their own items.

## Getting Started:

To start on this project, you'll need database software (provided by a Linux virtual machine) and the data to analyze.

### The virtual machine

1. Install VirtualBox from https://www.virtualbox.org/wiki/Download_Old_Builds_5_1

2. Install Vagrant from https://www.vagrantup.com/downloads.html

3. Download and unzip the VM configuration from https://s3.amazonaws.com/video.udacity-data.com/topher/2018/April/5acfbfa3_fsnd-virtual-machine/fsnd-virtual-machine.zip

4.  Change to this directory in your terminal with `cd`. Inside, you will find another directory called vagrant. Change directory to the vagrant directory.

### Start the virtual machine

5. From your terminal, inside the vagrant subdirectory, run the command `vagrant up`. This will cause Vagrant to download the Linux operating system and install it. This may take quite a while (many minutes) depending on how fast your Internet connection is.

6. When vagrant up is finished running, you will get your shell prompt back. At this point, you can run `vagrant ssh` to log in to your newly installed Linux VM.

### Running the code

7. Clone this repository and `cd` to its directory.
 
8. From your terminal run the command `python server.py`

9. Open `http://localhost:8000/` in your Chrome browser.

### Website design

10. Log in is required for adding new items, edit and delete existing items. To log in, click `Click to Log In` button and then choose using google or facebook account for authentication.

11. After logged in, click `Add Item` and then fill in the detail to create new item.

12. For items creadted by your account, you can click `Edit` to edit the details or `Delete` to delete an item.

13. You can view all items by clicking `All items` or items in one category by clicking its name on the left.

### JSON Api

14. For retrieve all exiting categories in the website: 
```
http://localhost:8000/catalog/allcategories/JSON
```
15. For retrieve all exiting items in the website: 
```
http://localhost:8000/catalog/allitems/JSON
```

### Create Empty Database (Optional)

16. Delete `catalog.db` in your Clone folder and then run 
```
python database_setup.py
```
