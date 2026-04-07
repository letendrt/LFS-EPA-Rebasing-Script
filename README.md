# LFS/EPA Rebasing Script 🚚🗃️
Script used for mass datafile rebasing. This code is necessary to rebase all the English LFS and French EPA. The code must be used in conjunction with the [File Organiser and Zipper](https://github.com/letendrt/LFS-EPA-Rebasing-File-Organiser-and-Zipper) script (also available with instructions on GitHub). The rebasing process also requires some knowledge of our Linux dev environment. As such, it is **imperative** that users go over the required training documentation prior to any rebasing attempts. This process is complicated, RUNNING ANY AI MODIFICATIONS ON THE CODE WILL BREAK IT. DO NOT RUN GENAI MODELS ON THE SCRIPT. THE LACK OF OPTIMISATION IS, AT TIMES, BY DESIGN.

Note that there are two versions of the script:
1) Stripped version: no comments other than basic function descriptions. Great if you don't want any visual clutter. 
2) Annotated: line by line comments explaining the script. Great for those who want to better understand the Borealis/Dataverse infrastructure. Also recommended if ever errors surface while running the script.

## Code Purpose 🤔❓
1) Mass deletes and uploads new file versions in Borealis;
2) Mass updates metadata blocks (Geographic Unit, Alternative Titles, and Citation Information);
3) Maps previous variable-level metadata to new tabular file;
4) Calculates and sets new variable weights in Data Explorer;
5) Creates new variable groups in Data Explorer;
6) Updates DDI records;
7) Creates individual XML files for each dataset (Quality Control purposes).

## Python Requirements 🐍🔧
1) Must be run in SP's Linux DV-DEV environement;
2) Minimum python version: 3.6+;
3) Libraries must be installed with binary method (requirements.txt file available in this repository).

## Setting up de DEV-DV and Python Environments 🐚🔧
1) **Creating SSH Key**: Navigate to the Windows command terminal and enter ```ssh-keygen```. Press enter for passphrase (empty passphrase). It will create a ```.ssh``` directory with ```id_rsa``` and ```id_rsa.pub```  files. The ```.ssh``` directory will be a hidden directory. To see it, enter ```cd .ssh``` in the Windows powershell. Your private key will be found in  ```id_rsa``` - **do not show it to anyone**. Your public key is found in ```id_rsa.pub```.
2) **Forwarding Public Key**: Forward your public key to IT. They will add it to the devdv account. Once done (and received the required permissions from IT), follow the following instructions to get started.
3) **Accessing the virtual environment**: Once permissions are granted, you can access your virtual environment by entering the line below from your powershell home directory (the active one when opening powershell). Depending on who you are (the reader) your user name may be your UTORId. If staff (and not a student) your user ID will be the one you use when logging in your work station.

    Example: ```ssh UserName@devdv.scholarsportal.info```
4) **Creating a New Project Folder**: It is good practice to create a new folder when starting a new project (organisation wise). We’ll start by navigating to our user folder by entering ```cd your_username``` in the command line (you can find out what directories are available by entering ```ls``` (LS, in lower case). In this case, I first navigate to my user directory before creating my new project folder. To create a new folder, enter:  ```mkdir name_of_folder```

    Example:  ```mkdir PythonProject```

    Folder can be deleted using the following:<br>
    Example: ```rmdir *FolderName*``` (if it is an empty directory)<br>
    Example: ```rm -r *FolderName*``` (if the directory is populated)

    Once created navigate to this new folder using ```cd *FolderName*```.

5) **Creating the Python Environment in DEV-DV**: Create a python environment in powershell from inside the directory by following the command line below. The default python in dvdev is Python 2.7.5 - this version is relatively old, so we want to make sure we create a virtual environment with a more up-to-date version of python. Follow the command lines below to do so:

   ```/usr/local/bin/python3.11 -m venv env```

   The environment can then be activated by entering the following in the command line:

    ```source env/bin/activate```

    The environment can then be deactivated by entering ```deactivate``` in the command line.

6) **Importing libraries in virtual env and creating requirements file**: Let’s navigate to our project directory in the DEV-DV environment and activate the python env. Downloading packages here is not work as usual, largely because of our GCC compiler version. Here, we need to import the binary version of the code. For your purposes, if not bringing any modifications to the code, you can simply download the requirements.txt file and skip to the last part of this step. Below is an example for the pandas library.

    Example: ```pip install pandas --only-binary=:all:```

    We will repeat this process for all of our libraries (in our case: Numpy, Pandas, PyDataverse, Pyreadstat, Requests). Once they are all installed, do the following to save them as a requirement file as depicted below:

    ```pip freeze > requirements.txt```

    You can then load them all at once the next time you open your virtual environment by entering the following on the command line:

    ```pip install -r requirements.txt```


## File Requirements and Manipulation 📁🐛
Users of the present script must first follow the necessary pre-script procedures described in the [File Organiser and Zipper](https://github.com/letendrt/LFS-EPA-Rebasing-File-Organiser-and-Zipper/tree/main) repository. The present script is relatively useless otherwise. It may only run if the proper file architecture is built ahead of time. If you haven't yet done so, please go and do so now. Once that's done, you may follow the steps below.

1) **Importing Files in DEV-DV Environment**: We will start by importing our python script, as well as the CSV file created by the [File Organiser and Zipper](https://github.com/letendrt/LFS-EPA-Rebasing-File-Organiser-and-Zipper/tree/main) script (of course the CSV may not be entirely complete after running the File Organiser and Zipper - please ensure that you have done your due diligence). We will start by creating a new data directory inside our ```PythonProject``` directory. 

    Example:  ```mkdir ProjectData```

    In order to send files into the DEV-DV environment, we need to run the following command in the home directory in windows’ powershell (this will not work in the DEV-DV environment, unless you have created an SSH key there as well): 

    Example (all on the same line in powershell):<br>
   ```scp -r \Users\joe3\PyProject joe3@devdv.scholarsportal.info:/home/joe3/PythonProject/ProjectData``` <br>
    (note that if you are sending a singular file, you only need to enter ```scp``` as ```scp -r``` is specifically for copying folders over)

    When we return to our DEV-DV environment, we will find our files copied in the selected directory after refreshing. You can copy files from the linux environment to your local environemnt by reordering the command above. Note that this command must be run in your local shell environment, not the Linux environment:

   ```scp -r joe3@devdv.scholarsportal.info:/home/joe3/PythonProject/ProjectData \Users\joe3\PyProject```

3) **Updating Python File from Linux shell using vi**: It is likely that the initial python file is not up to date (perhaps you'll have to edit the CSV file path if you are running the python script in batches, or perhaps it has yet to be fine tuned to the current environment). In this step, we will go over how to edit the python file from inside the Linux environment. First we need to navigate to our file and open it using:

    Example: ```vi new_code_rebasing_2026_annotated.py```

    At this point, the file should now be open. There are two modes you can use to edit and navigate through the file: the ```--INSERT--``` mode (which can be accessed by pressing ```i```), or the command mode (accessed by pressing ```Esc``` or ```Escape```). Note that at this point, you can exit with ```Ctrl + Z```, though the file will still be active in the background. To fully exit without saving progress enter ```:q!```, but make sure to save your changes if any are made (see below).

    Once modifications are made, you can save your progress by entering ```:w```. You can then quit using ```:q```. Alternatively you can save and quit by using the ```:wq```. Entering ```:``` at any time from command mode will prompt users to enter their command. Below are some other useful commands to navigate through the file in the Linux environment.

    ```Ctrl + u``` scrolls up (half-screen)<br>
    ```Ctrl + d``` scrolls down (half-screen)<br>
    ```Ctrl + b``` scrolls up (full screen)<br>
    ```Ctrl + f``` scrolls down (full screen)<br>

## Running the Python Script 🏃‍♂️💨🐍
we can finally run our script. To run it, first make sure to activate your virtual environment:
Example: ```source env/bin/activate```

From there, you can navigate to the directory of the python and use the following command to run the script:
Example:  ```python new_code_rebasing_2026_annotated.py```

Before doing so, however, you'll need to fetch your Borealis API key. Using ```vi new_code_rebasing_2026_annotated.py```, paste your API key in place of the placeholder text for ```api_token_origin``` on line 34:

<kbd> </kbd>








