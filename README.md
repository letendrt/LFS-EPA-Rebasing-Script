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


## File Requirements 📁🐛
Users of the present script must first follow the necessary pre-script procedures described in the [File Organiser and Zipper](https://github.com/letendrt/LFS-EPA-Rebasing-File-Organiser-and-Zipper/tree/main) repository. The present script is relatively useless otherwise. It may only run if the proper file architecture is built ahead of time. If you haven't yet done so, please go and do so now. Once that's done, you may follow the steps below.

1) 




