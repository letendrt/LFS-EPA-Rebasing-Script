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

## Minimum Python Requirements 🐍🔧
1) Must be run in SP's Linux DV-DEV environement;
2) Minimum python version: 3.6+;
3) Libraries must be installed with binary method (requirements.txt file available in this repository).

## Setting up de DEV-DV Environment 🐚🔧
1) **Creating SSH Key**: Navigate to the Windows command terminal and enter ```ssh-keygen```. Press enter for passphrase (empty passphrase). It will create a ```.ssh``` directory with ```id_rsa``` and ```id_rsa.pub```  files. The ```.ssh``` directory will be a hidden directory. To see it, enter ```cd .ssh``` in the Windows powershell. Your private key will be found in  ```id_rsa``` - **do not show it to anyone**. Your public key is found in ```id_rsa.pub```.
2) **Formarding Public Key**: Forward your public key to IT. They will add it to the devdv account. Once done (and received the required permissions from IT), follow the following instructions to get started.
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



## File Requirements 📁🐛
Users of the present script must first follow the necessary pre-script procedures described in the [File Organiser and Zipper](https://github.com/letendrt/LFS-EPA-Rebasing-File-Organiser-and-Zipper/tree/main) repository. The present script is relatively useless otherwise. It may only run if the proper file architecture is built ahead of time. If you haven't yet done so, please go and do so now. Once that's done, you may follow the steps below.

1) 




