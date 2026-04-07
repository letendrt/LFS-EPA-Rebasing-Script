# LFS/EPA Rebasing Script 🚚🗃️
Script used for mass datafile rebasing. This code is necessary to rebase all the English LFS and French EPA. The code must be used in conjunction with the [File Organiser and Zipper](https://github.com/letendrt/LFS-EPA-Rebasing-File-Organiser-and-Zipper) script (also available with instructions on GitHub). The rebasing process also requires some knowledge of our Linux dev environment. As such, it is **imperative** that users go over the required training documentation prior to any rebasing attempts. This process is complicated, RUNNING ANY AI MODIFICATIONS ON THE CODE WILL BREAK IT. DO NOT RUN GENAI MODELS ON THE SCRIPT. THE LACK OF OPTIMISATION IS, AT TIMES, BY DESIGN.

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

## File Requirements 📁🐛

