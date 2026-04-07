# Original code by Victoria Lubitch and Thierry Letendre, Comments added by Thierry Letendre


# Importing libraries for systems set-up and info
from datetime import datetime
import sys
import time

# importing libraries for XML/HTML manipulation
import configparser
import xml.etree.ElementTree as ET
import lxml.etree as EL
import re
import io

# Importing libraries for dataverse api
# Documentation found here: https://pydataverse.readthedocs.io/en/latest/
import requests
import pyDataverse.utils as utils
from pyDataverse.api import NativeApi, DataAccessApi

# Importing libraries for file manipulation
from zipfile import ZipFile
import pyreadstat
import csv
import json
import pandas as pd


# CONFIGURATION SECTION
# This is the same thing as above, but without calling ini files


api_token_origin = "ENTER_API_KEY_HERE"                                # Enter API key as string
url_base_origin = 'https://borealisdata.ca'                            # Input base origin url as string

headers_origin = {'X-Dataverse-key': api_token_origin}                 # Create dictionary and insert API token as the value
api_origin = NativeApi(url_base_origin, api_token_origin)              # API call using the pyDataverse
data_api_origin = DataAccessApi(url_base_origin, api_token_origin)


# This function checks if a dataset is locked (for one reason or another; it could be due to .tab file ingestion, for instance)
# More documentation on what this entails available here: https://guides.dataverse.org/en/6.2/api/native-api.html#dataset-locks

def check_lock(dataset_id):

    time_start = datetime.now()                         # Set up internal timer
    print("Start check_lock")                           # Print start message

    try:
        url = f"{url_base_origin}/api/datasets/{dataset_id}/locks"          # Set up URL for access
        lock = requests.get(url, headers_origin)                            # Set up lock status

        if lock.status_code == 503:                                         # If URL is unavailable
            print("503 - Server is unavailable")                            # Print status
            sys.exit()                                                      # stop running the function

        a = 0
        while len(lock.json()['data']) > 0:
            print(f"Lock {str(a)} times {dataset_id} {lock.json()}")        # API returns jason file of all locked datasets
            print(lock.json())                                              # Print lock information
            time.sleep(10)                                                  # Start a 10 second timer
            a += 1                                                          # Update attempt tracker

            lock = requests.get(url, headers_origin)                        # Check lock status
            if lock.status_code == 503:                                     # If URL is unavailable
                print("503 - Server is unavailable")                        # Print status
                sys.exit()                                                  # Stop running the function

            if lock.status_code != 200:                                                              # If URL status code is not 200 (not successful)
                print(f"check_lock func: lock status {str(lock.status_code)} for {dataset_id}")        # Print lock information
                return False  # Return False

    except Exception as e:                                                     # This exception parameter prevents unwanted crashes or errors.
        print(f"check_lock. Error {str(e)}, dataset {dataset_id}")               # Print lock information
        return False                                                             # Return False

    time_end = datetime.now()                                                       # Provide date and time
    t = time_end - time_start                                                       # Give total time taken to ingest dataset
    print(f"Dataset {str(dataset_id)} was locked {str(t.total_seconds())} sec")     # Provide dataset information

    return True                                                                     # Return True


def get_var_metadata_dataverse(dataset_id, datafile_id):

    print("Start get_var_metadata_dataverse")
    lock = check_lock(dataset_id)                                             # Checks if dataset is locked with the function 'check_lock()'
    url = url_base_origin                                                     # Assigns previously defined url origin to the variable 'url'

    if lock:                                                                # if able to access the url
        url = f"{url}/api/access/datafile/{datafile_id}/metadata"           # assign new url to the 'url' variable
        resp = requests.get(url, headers=headers_origin)                    # Assign access information to the variable 'resp'

        if resp.status_code == 200:                                         # If access is successful
            tree = ET.fromstring(resp.content)                              # Assign string json() data to tree (creates a new json?)
            return tree

        else:                                                                                                           # If access code is not 200
            print(f"get_var_metadata_dataverse: dataset_id = {dataset_id} datafile_id = {datafile_id} url = {url}")     # Print assigned variables
            return False

    else:                                                                                      # If the url is locked (this could be for various different reasons)
        print(f"get_var_metadata_dataverse: dataset_id = {dataset_id} datafile_id = {datafile_id} url ={url} locking problem")  # Print an error message
        return False


# This function extracts variable data from the selected dataverse file

def map_label_var(dataDscr, ns):                        # Example: map_label_var('dataDscr_new_file', 'ns0:') - ns is a variable though

    print("Start map_label_var")
    map_name_id = {}                                    # Creating dictionary
    vars = dataDscr.findall(f'{ns}var')                 # Finds every instantiation of '<ns0:var>' in the XML file and adds in list variable 'vars'

    for var in vars:                                    # Creating for loop to parse through the list created above
        ID = var.attrib.get("ID")                       # Uses attrib from the ElementTree library to fetch IDs of each ns0:var
        name = var.attrib.get("name")                   # Same thing as above, but for name
        map_name_id[name] = ID                          # sets dictionary L (lock) as the name variable, sets the ID as K (key) variable
        

    return map_name_id  # Return the populated dictionary map_name_id, now with all names and IDs


# This function matches variable IDs to their corresponding IDs in the new/old file.
# Takes arguments defined in a below function -> updated_dataset()
# map_current_file (i will change this) is the variable 'map_name_id_current_file'
# map_new_file (i will also change this) is the variable 'map_name_id_new_file'

def var_ids_correspondence(map_current_file, map_new_file):
    print("Start var_ids_correspondence")
    print(map_current_file)                                                        # Printing old file {Name: ID} dictionary
    print(map_new_file)                                                            # Printing new file {Name: ID} dictionary

    map_ids = {}                                                                   # Creating empty dictionary mapping old IDs to the new IDs
    map_ids_n_d = {}                                                               # Creating empty dictionary mapping new IDs to the old ones

    for item in map_new_file:                                                      # For all {Name: ID} in the new file dictionary
        if item in map_current_file:                                               # If the {Name: ID} in the old file dictionary appears in the new file dictionary
            map_ids[map_new_file[item]] = map_current_file[item]                   # Add the matching {name: ID} dictionary to the newly created map_ids dictionary

        else:                                                                      # Else, if the {name: ID} dictionary does not appear in the in the old file dictionary
            if item.upper() in map_current_file:                                   # Check if the dictionary in upper case is present in the old dictionary
                map_ids[map_new_file[item]] = map_current_file[item.upper()]       # Add to map_ids dictionary if present

            else:                                                                    # Else, if the upper case iteration is not there either
                if item.lower() in map_current_file:                                 # Check if there is a lower case equivalent in the old dictionary
                    map_ids[map_new_file[item]] = map_current_file[item.lower()]     # Add to map_ids dictionary if present

    for item in map_current_file:                                                    # For all {Name: ID} in the old file dictionary
        if item in map_new_file:                                                     # If the {Name: ID} in the new file dictionary appears in the old file dictionary
            map_ids_n_d[map_current_file[item]] = map_new_file[item]                 # Add the matching {name: ID} dictionary to the newly created map_ids_n_d dictionary

        else:                                                                           # Else, if the {name: ID} dictionary does not appear in the in the new file dictionary
            if item.lower() in map_new_file:                                            # Check if the dictionary in upper case is present in the new dictionary
                map_ids_n_d[map_current_file[item]] = map_new_file[item.lower()]        # Add to map_ids_n_d dictionary if present

            else:                                                                       # Else, if the upper case iteration is not there either
                if item.upper() in map_new_file:                                        # Check if there is a lower case equivalent in the new dictionary
                    map_ids_n_d[map_current_file[item]] = map_new_file[item.upper()]    # Add to map_ids_n_d dictionary if present

    return map_ids, map_ids_n_d


# This function updates variable metadata (harmonisation) between all the dictionaries and XML files.
# This function takes 6 arguments. map_ids and map_ids_n_d ({name: ID} dictionaries cross referencing old/new and new/old dictionaries)
# 2 dataDscr arguments (these are XML files from which <ns0:dataDscr> variable data is extracted - both in the new and old file)
# ns_var (new) and ns (old) file tags, i believe both are <ns:0>, or 'ns:0'


def update_var_ddi(map_ids, map_ids_n_d, dataDscr_new_file, dataDscr_current_file, ns_var, ns):

    print("Start update_var_ddi")                                       # Prints previously defined dictionaries (these are in the function arguments)
    print(map_ids)
    print(map_ids_n_d)

    grps = dataDscr_current_file.findall(f'{ns}varGrp')                 # Finds all variable groups in the old file

    #################################### GROUPS ####################################

    for var_grp in grps:                                        # For variable groups in the list of groups created above
        grp_id = var_grp.get("ID")                              # Fetch the group ID
        F1 = grp_id[-2:]                                        # Assign the second last group ID to the variable F1 (I don't know why that's the case yet, must be a marker of some sort)

        # this F1 stuff is deprecated
        if F1 == "F1":                                          # Check if group is F1 (?) Ask Victoria about this
            lng = len(grp_id)                                   # Assign the number of items to the variable 'lng'
            grp_id = grp_id[0 : lng - 2]                        # Updates the grp_id list - omits the last 2 items (?)
            var_grp.set('ID', grp_id)                           # Creates a dictionary with L (lock) as ID, and K (keys) as all the variable IDs in the group

        wgt_var = var_grp.get("var")                            # Grouping variables for weighting
        if wgt_var != None:                                     # If the list of to-be weighted items is populated
            w_var = wgt_var.split(" ")                          # Split the items of the string at the empty space (" "), creates list of strings
            w_str = ""                                          # Assign empty string to new variable

            for w in w_var:                                     # For items in the list of strings
                if w in map_ids_n_d:                            # If the item is in the old file dictionary

                    if w_str == "":                                         # If w_str is an empty string (which it should always be given the for loop)
                        w_str = map_ids_n_d[w].strip()                      # Removes the empty spaces in the variable name (if there are any)

                    else:                                                   # If string is not empty (meaning the loop has already iterated once - I think?)
                        w_str = f'{w_str} {map_ids_n_d[w].strip()}'         # put an empty string at the front? not clear why.

                else:                                                       # If the item is not in the old item list
                    print(w)                                                # Print the item name

            if w_str != "":                                                 # If the string is populated (steps above)
                var_grp.set('var', w_str)                                   # Assign the w_str K (key) to L (lock) 'var'

        dataDscr_new_file.append(var_grp)                                   # Add the group of to-be weighted variables at the end of the XML file.

    ################################# VARIABLES ####################################

    vars = dataDscr_new_file.findall(f'{ns_var}var')                        # Create a list of variables.
    print(vars)

    for var in vars:                                                        # For every item in the list
        id_new_file = var.attrib.get("ID")                                  # Assign IDs to id_new_file
        print(f"Dataverse ID: {id_new_file}")                               # Print IDs fetched above.

        if id_new_file in map_ids:                                          # If fetched IDs are present in the dictionary of IDs from the correspondance function
            id_current_file = map_ids[id_new_file]                          # Assign the mutual ID to the variable id_current_file (need to change naming convention)
            print(f"Current_file ID: {id_current_file}")                    # Print IDs from the above variable.

        else:                                                               # If the ID is not present
            continue                                                        # Procede

        ########################## VARIABLE LEVEL METADATA #############################

        # WEIGHT VARIABLE
        var_current_file = dataDscr_current_file.find(f'{ns}var[@ID="{id_current_file}"]')          # Find all tabular file variables from the old file and assign to var_current_file
        wgt_var = var_current_file.get("wgt-var")                                                   # Assigns the corresponding weight variable to 'wgt_var'. Weight variable is labeled 'wgt-var' in the XML file
        print(ET.tostring(var_current_file, encoding='unicode'))
        print(wgt_var)

        if wgt_var != None:                                                     # If the wgt_var variable is populated
            w_var = wgt_var.split(" ")                                          # Split at spaces (string) and assign to the variable 'w_var' (this could be for cleaning?)
            w_str = ""                                                          # Create empty string variable w_str

            for w in w_var:                                                     # For every entry in the w_var variable
                if w_str == "":                                                 # If the empty string has yet to be populated
                    print(w)                                                    # Print the weight variable

                    if w in map_ids_n_d:                                        # If the weight variable is present in the old file dictionary (this means it is the same between the old and new tabular files)
                        w_str = map_ids_n_d[w].strip()                          # Update the empty string to now hold the weight variable name

                else:                                                           # If w_str is already populated (meaning that there is more than one weight variable?)
                    if w in map_ids_n_d:                                        # If the weight variable is present in the old file dictionary (this means it is the same between the old and new tabular files)
                        w_str = f'{w_str} {map_ids_n_d[w].strip()}'             # Update 'w_str' - add the other weight variable after the first.

            if w_str != "":                                                     # If w_str is populated (meaning there IS a weight variable)
                var.set('wgt-var', w_str)                                       # Add weight variable Lock and Key as a dictionary entry for that variable list

        wgt = var_current_file.get("wgt")                                       # Fetch 'wgt' from the old file XML
        if wgt != None:                                                         # If the 'wgt' variable defined above is populated
            var.set("wgt", wgt)                                                 # Add weight variable Lock and Key as a dictionary entry for that variable list

        # VARIABLE QUESTION
        qstn_current_file = var_current_file.find(ns + 'qstn')                  # Find XML tags for variable question in the old file
        print(ET.tostring(var_current_file, encoding='unicode'))                # Print formatted XML for old file
        print("-----")                                                          # Insert space marker
        
        if qstn_current_file is not None:                                               # Add check for None
            print(ET.tostring(qstn_current_file, encoding='unicode'))                   # Print question found in old file

        if qstn_current_file != None:                                                   # If there is a variable question in the old file
            var.append(qstn_current_file)                                               # Add this question string to the variable list

        # VARIABLE NOTES
        notes_current_file = var_current_file.findall(f'{ns}notes')                     # Parse old XML file for variable level notes
        for note in notes_current_file:                                                 # For notes parsed above
            var.append(note)                                                            # Add them to the variable list

        # VARIABLE UNIVERSE
        universe_current_file = var_current_file.find(f'{ns}universe')                  # Parse old XML file for variable level universe information
        if (universe_current_file != None):                                             # If the above task results in a populated variable
            var.append(universe_current_file)                                           # Add to the variable list

            # VARIABLE FREQUENCY WEIGHT
            catgry_current_file = var_current_file.findall(f'{ns}catgry')               # Parse old XML file for all variable response categories (possible response types)
            catgrys = var.findall(f'{ns_var}catgry')                                    # In the current variable being for-looped much higher, fetch all response type categories

            for catgry in catgry_current_file:                                          # If the categories of the present variable are also found in the old file (meaning no change between old and new files)
                catStat_current_file = catgry.find(f'{ns}catStat[@wgtd="wgtd"]')        # Fetch the weight statistics (presumably post weighing calculations) and add to list

                if catStat_current_file != None:                                        # If the above task results in a populated catStat_current_file variable
                    catValu = catgry.find(f'{ns}catValu')                               # Parse the categories to see if values have been computed

                    if catValu != None:                                                                 # If values have been computed, and catValu is populated
                        text = (catValu.text)                                                           # Reads value as string? I don't think I have ever seen ".text" before.

                        for ct in catgrys:                                                              # For items in the list of variable response categories
                            if ct.find(f'{ns_var}catValu').text.strip() == text.strip():                # If the computed values are the same between the new file and the old file
                                ct.append(catStat_current_file)                                         # Add the computed variable category valoue to the list
                                break                                                                   # Break loop and go to next variable

    return dataDscr_new_file


# This function takes three arguments. id, file_id_new, xml_string from the 'update_dataset()' function
# Refer to the function mentioned in the previous online for more information
# Arguments (in order) are the variables id, file_id_new, and xml_string


def var_update_dataset(dataset_id, datafile_id, xml):
    print("Start var_update_dataset")

    url = f'{url_base_origin}/api/edit/{str(datafile_id)}'                      # curl -H "X-Dataverse-key:xxxxxxxxxx" -X PUT https://demo.dataverse.org/api/edit/24 --upload-file dct.xml
    check = check_lock(dataset_id)                                              # Assign check_lock function return to the variable 'check'
    if check == False:                                                          # If check_lock returns False
        return check                                                            # Return False (?)

    try:
        resp = requests.put(url, headers=headers_origin, data=xml)              # Fetch request information, assign to the variable 'resp'
        # print(resp.status_code())
        if resp.status_code != 200:                                             # If access is unsuccessful
            print(resp.json())                                                  # Print failure information
            return False                                                        # Return False

        else:                                                                   # If access is successful
            print("Updated")                                                    # Print status
            # print(resp.json())                                                # Print access information

    except Exception as e:                                                      # In the event of an exception (not sure when this actually happens)
        print(f"var_update_dataset: {str(e)} {url}")                            # print url related to the exception
        return False                                                            # Return False

    return True                                                                 # If all works fine, return True


# This function is used to update updated datasets
# It takes 3 arguments, all of which are defined and listed in the main() function
# 'File_id_old' is 'tab_id_old' (old tabular file), 'file_id_new' is 'tab_id_new'(new tabular file),
# and 'id' is the dataset id (stays the same i reckon)


def update_dataset(id, file_id_old, file_id_new):

    print(f"Draft id {file_id_new}")
    var_xml = get_var_metadata_dataverse(id, file_id_new)                       # Calls a function defined above. ---------- if var_xml != tree, it crashes

    if var_xml != False and var_xml != None:                                    # If the newly created file is NOT empty - meaning it successfully pulled content in get_var_metadata_dataverse()
        result = re.search(r'{(.*)}', var_xml.tag)                              # Using regex library to capture and group all instances of the html/XML tag <ns:0>

        if result == None:                                                      # If 'result' from the above if statement is empty
            ns_var = ''                                                         # Assign an empty string to 'ns_var'

        else:                                                                   # Else, if result is populated
            ns_var = result.group(0)                                            # Assign ns:0 to the variable 'ns_var'

        dataDscr_new_file = var_xml.find(f"{ns_var}dataDscr")                   # Fetches all instances of '<ns0:dataDscr>', and assigns them to the variable 'dataDscr_new_file'
        print(f"Published id {file_id_old}")                                    # Prints the old tabular file ID (i don't know why)

        # This step is the same as the one above
        var_xml_current_file = get_var_metadata_dataverse(id, file_id_old)          # Calls a function defined above.
        print(var_xml_current_file)                                                 # Prints the XML data extracted from the above statement


        if var_xml_current_file != False and var_xml_current_file != None:
            result = re.search(r'{(.*)}', var_xml_current_file.tag)                 # Using regex library to capture and group all instances of the html/XML tag <ns:0>

            if result == None:                                                      # If 'result' from the above if statement is empty
                ns = ''                                                             # Assign an empty string to 'ns_var'
            else:                                                                   # Else, if result is populated
                ns = result.group(0)                                                # Assign ns:0 to the variable 'ns_var'

        else:
            return False

        dataDscr_current_file = var_xml_current_file.find(f"{ns}dataDscr")              # Fetches all instances of '<ns0:dataDscr>', and assigns them to this new variable.

        # At this point, we have retrieved the metadata content on the old and new tabular file, and extracted their XML metadata.
        # In order to transfer metadata (similarly to 'Import XML' in data explorer) we need to match the two XML files in terms of variable IDs
        # The following called functions do just that. These functions are defined and commented in an above section.

        map_name_id_new_file = map_label_var(dataDscr_new_file, ns_var)                         # Assigns new file variable Names and IDs to new variable
        map_name_id_current_file = map_label_var(dataDscr_current_file, ns)                     # Assigns old file variable Names and IDs to new variable
        ids_maps = var_ids_correspondence(map_name_id_current_file, map_name_id_new_file)       # Calls function defined above to match variables IDs
        print("Before update_var_ddi")                                                          # Print update DDI status message

        dataDscr_dv_updated = update_var_ddi(ids_maps[0], ids_maps[1],
            dataDscr_new_file, dataDscr_current_file, ns_var, ns)                               # Run function defined above
        
        print("After update var ddi")                                                           # Print updated DDI status message

        xml_updated = ET.ElementTree(dataDscr_dv_updated)                                       # Create a new variable holding the updated DDI XML information
        xml_string = ET.tostring(dataDscr_dv_updated, encoding='utf8', method='xml')            # Creates an XML file with updated metadata with function called a few lines above

        if var_update_dataset(id, file_id_new, xml_string):                                     # Calls function defined above. If True.
            return True

    return False                                                                                # Otherwise, return False


# This function is called in the main function. It takes 2 arguments
# The first is the ID of the dataset we wish to update. And the second is the cell
# for which the column is labeled 'File Description'. (the cell that contains the description)


def update_file_metadata(tab_id_new, description):

    metadata_file = '{"description":' + '"' + description + '"}'                    # Create string in dictionary format for API call below
    url = f'{url_base_origin}/api/files/{str(tab_id_new)}/metadata'                 # Creating URL for subsequent API access (I don't see it being used below though...)

    print(url)                                                                      # Printing URL
    print(metadata_file)                                                            # Printing description update

    resp = api_origin.update_datafile_metadata(tab_id_new, metadata_file, False)    # API call via pyDataverse
    print(resp)


# This function is used to update the dataset citation information. It takes 3 arguments - latest_version, row, and doi
# Latest version is a version code pulled from an API call in main (?) - latest old version
# row is a variable that is obtained by parsing through a CSV - it is for-looped in the main function
# doi is extracted from the csv file used for the rebasing.


def update_citation(latest_version, row, doi):

    updated_fields = {}                                                         # Creating empty dictionary for indexing (I am aware that this is json formatting as well as dictionary)
    updated_fields['fields'] = []                                               # Creating new dictionary lock for keywords
    metadataBlocks = latest_version['metadataBlocks']                           # Retrieving metadata for the dataset and assining it to the variable metadataBlocks
    fields = metadataBlocks['citation']['fields']                               # Retrieving metadata fields from the extracted metadata blocks
    access_to_sources = False                                                   # This is the only time this surfaces - access to sources is set to false (not sure what this does)
    notes = False                                                               # Notes set to False
    note = row['Variable Revision in Metadata: Citation > Notes'].strip()       # note is assigned the data held in the corresponding CSV cell
    omission = row['Remove from Title']                                         # Fetching title segment to remove from existing record

    print('############################')
    print(fields)
    print('############################')

    for field in fields:                                                        # For all items in metadata fields
        if field['typeName'] == 'title':                                        # If the field is that of the title

            if omission in field['value']:                                      # If segment of title is to be removed
                field['value'] = field['value'].replace(omission, "")           # Replace to-be removed part with empty string.

            field['value'] = f"{field['value']} {row['Title > Additions']}"     # Add the information from the CSV sheet
            updated_fields['fields'].append(field)                              # Add newly created title back in the field string

        if field['typeName'] == 'dsDescription':                                # Description is multiple - pertains to different types of information (I think) - perhaps different metadata sections
            value = field['value']                                              # Assigns the metadata block section 'value' to the variable value

            for v in value:                                                                                 # For items in the field 'value'
                if ('dsDescriptionValue' in v):                                                             # If the dataset description is present in value
                    print(v['dsDescriptionValue'])                                                          # Print the subset
                    print(v['dsDescriptionValue']['value'])                                                 # Print the value of the subset
                    v['dsDescriptionValue']['value'] = row['Revision Additions: Citation > Descriptions']   # Updating record with corresponding cell in the CSV file
                    
            updated_fields['fields'].append(field)                                                          # Once for-loop completed, add new values in the metadata block

        # KEYWORD VALUE UPDATE SECTION

        if field['typeName'] == 'keyword':                                      # Fetch keyword field from XML record
            new_keywords = row['Keywords'].split(', ')                          # Splits keywords in the csv file at the commas (, ) and adds them to a list
            print(f'Adding new Keywords: {new_keywords}')                       # Printing new keywords
            keyword_list = []                                                   # Creating new list in which to add new keyword records

            for words in new_keywords:                                          # For every keyword in the list of keywords
                main_keyword_field = {}                                         # Create a new dictionary entry in which to add all subsequent fielf keyword dictionaries
                field_keyword = {}                                              # Create new dictionary for keyword level information (see below)
                field_keyword['typeName'] = 'keywordValue'                      # Setting up XML field in dictionary
                field_keyword['multiple'] = 'False'                             # Setting up XML field in dictionary
                field_keyword['typeClass'] = 'primitive'                        # Setting up XML field in dictionary
                field_keyword['value'] = words                                  # Adding the keyword as the field value
                main_keyword_field['keywordValue'] = field_keyword              # Adding the above keyword metadata in the main keyword dictionary
                keyword_list.append(main_keyword_field)                         # Add all main keyword records to a list

            print(keyword_list)                                                 # Print the list of XML formatted keywords
            keyword_rep = {}                                                    # Creating dictionary for updated keyword fields
            keyword_rep['typeName'] = 'keyword'                                 # Setting up XML field in dictionary
            keyword_rep['multiple'] = True                                      # Setting up XML field in dictionary
            keyword_rep['typeClass'] = 'compound'                               # Setting up XML field in dictionary
            keyword_rep['value'] = keyword_list                                 # Assigning the list to the field value
            updated_fields['fields'].append(keyword_rep)                        # Add newly created dictionary to the updated record

        if field['typeName'] == 'notesText':                                    # If the metadata block field is that of the notes
            notes = True                                                        # Then notes is True (meaning there are dataset notes)
            if note != None and note != '':                                     # If note is populated and is not an empty string
                field['value'] = notes                                          # Assign True to the corresponding section of the metadata block?
                updated_fields['fields'].append(field)                          # Assign a new field section to the updated metadata block (at least, I think that's what it does)

    if not notes and note != None and note != '':                               # If there are no notes in existing record
        print('No notes')                                                       # Indicate that there are no notes

        field_notes = {}                                                                    # Create new note field
        field_notes['typeName'] = "notesText"                                               # Retrieve note section in the metadata block
        field_notes['multiple'] = False                                                     # Indicate there there is only one note field
        field_notes['typeClass'] = "primitive"                                              # I don't know what this means - perhaps that this new note should come first? or vice-versa?
        field_notes['value'] = row['Variable Revision in Metadata: Citation > Notes']       # Assign CSV cell note metadata to the new notes section
        updated_fields['fields'].append(field_notes)                                        # Add to updated metadata field


    url = f'{url_base_origin}/api/datasets/:persistentId/editMetadata?persistentId={doi}&replace=true'        # Update URL variable for API call
    print(url)                                                                                                # Print URL

    resp = requests.put(url, data=json.dumps(updated_fields), headers=headers_origin)               # Upload the updated metadata fields after converting the dictionaries to json format
    print(resp.status_code)                                                                         # Fetch status code

    if resp.status_code == 200:                                                 # If access is successful
        return True                                                             # Return True
    else:                                                                       # Otherwise
        return False                                                            # Return False


def update_geographic_field(latest_version, row, doi):

    updated_geo = {}                                                            # Creating empty dictionary for indexing (I am aware that this is json formatting as well as dictionary)
    metadataBlocks_geo = latest_version['metadataBlocks']                       # Retrieving metadata for the dataset and assining it to the variable metadataBlocks
    geo_fields = metadataBlocks_geo['geospatial']['fields']                     # Retrieving metadata fields from the extracted metadata blocks

    print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
    print(geo_fields)
    print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%')

    unit_to_replace = geo_fields[1]                                             # Geographic data only has 2 entries for our purposes, which is why an index is used, there is a more efficient way of doing this I'm sure.
    print(unit_to_replace)                                                      # Print fetched content

    new_unit = [row['Geographic Unit']]                                         # Splits keywords in the csv file at the commas (, ) and adds them to a list. Geographic unit values take arrays (which is why new unit is made into a list)
    print(f'New Geographic Unit: {new_unit}')                                   # Printing new geographic unit

    new_geo_entry = {}                                                          # Creating new geo unit record
    new_geo_entry['typeName'] = 'geographicUnit'                                # Setting up XML field in dictionary
    new_geo_entry['multiple'] = True                                            # Setting up XML field in dictionary
    new_geo_entry['typeClass'] = 'primitive'                                    # Setting up XML field in dictionary
    new_geo_entry['value'] = new_unit                                           # Assigning the list to the field value

    print(new_geo_entry)                                                        # Printing new dictionary entry
    geo_fields[1] = new_geo_entry                                               # Inserting new entry in previous value field

    updated_geo['fields'] = geo_fields                                          # Adding updated field to new dictionary
    print(json.dumps(updated_geo))                                              # Print new metadata field (converts python dictionary to json format)

    url = f'{url_base_origin}/api/datasets/:persistentId/editMetadata?persistentId={doi}&replace=true'  # Update URL variable for API call
    print(url)                                                                                          # Print URL
    print(updated_geo)                                                                                  # Print updated fields metadata block

    resp = requests.put(url, data=json.dumps(updated_geo), headers=headers_origin)             # Upload the updated metadata fields after converting the dictionaries to json format
    print(resp.status_code)                                                                    # Fetch status code

    if resp.status_code == 200:                                     # If access is successful
        return True                                                 # Return True
    else:                                                           # Otherwise
        return False                                                # Return False


# Update alt titles.


def update_alt_titles(latest_version, row, doi):

    metadataBlocks = latest_version['metadataBlocks']               # Retrieving metadata for the dataset and assining it to the variable metadataBlocks
    fields = metadataBlocks['citation']['fields']

    print('*********************************************************')
    print(fields)
    print('*********************************************************')

    print(row)
    fore = row['Other Language Name']
    print(fore)
    center = row['Other Language Month']
    print(center)
    center_2 = row['\ufeffYear']                                    # put \ufeff -- \ufeffyear -- if running the real thing
    print(center_2)

    post = row['Other Language Additions']
    val_list = [fore, center, center_2, post]
    value = ' '.join(val_list)
    print(value)

    short_form = row['Month Name and Year']
    short_list = ['EPA', short_form]
    short_value = ' '.join(short_list)
    print(short_value)

    alt_list = [value, short_value]

    new_title_entry = {}                                            # Creating new geo unit record
    new_title_entry['typeName'] = 'alternativeTitle'                # Setting up XML field in dictionary
    new_title_entry['multiple'] = True                              # Setting up XML field in dictionary
    new_title_entry['typeClass'] = 'primitive'                      # Setting up XML field in dictionary
    new_title_entry['value'] = alt_list
    print(new_title_entry)

    url = f'{url_base_origin}/api/datasets/:persistentId/editMetadata?persistentId={doi}&replace=true'
    resp = requests.put(url, json.dumps(new_title_entry), headers=headers_origin)                                 # Upload the updated metadata fields after converting the dictionaries to json format
    print(resp.status_code)

    if resp.status_code == 200:                                     # If access is successful
        return True                                                 # Return True
    else:                                                           # Otherwise
        return False


# This function takes no argument, it is run after the initial_ingest series of function.
# This function fetches information about the dataset DOI, weight variable, and weight exception data from the CSV file
# It then pulls information from the dataset by doing an API call
# Also conducts file formatting for later use.


def post_processing(date):

    with open(f'/data/data_lfs_rebased/data_EPA_Remanie/Rebasing/{date}', newline='') as csvfile:           # Select CSV file

        reader = csv.DictReader(csvfile)                                         # Set up reader

        for row in reader:                                                      # Reading lines within the CSV file.
            print(row)                                                          # Prints the row it is currently parsing through

            doi = row['Persistent Identifier']                                  # Assigning dataset DOI to the variable "doi"
            weight_var = row['WeightVariable']                                  # Assigning CSV file weight variable to the variable weight_var
            omission = row['WeightException']                                   # Assigning CSV file weight omissions to the variable 'omission'
            print(doi)

            resp = api_origin.get_dataset(doi, version="5.0")                   # Doesn't need to set to most recent version, it would seem.

            if resp.status_code == 200:                                         # If API call is successful (marker 200)
                id = resp.json()['data']['id']                                  # old dataset ID is assigned to variable id
                latest_version = resp.json()['data']['latestVersion']           # Latest old dataset version is set to variable list "latest_version"

                files = latest_version['files']                                 # old file latest version is set to variable list 'files'
                dataset_id = latest_version['datasetId']                        # sets old dataset ID to variable 'dataset_id' - this could be added on the step at line 54

                for file in files:                                              # For loop running curl commands to create new dataset version?
                    dataFile = file['dataFile']                                 # Assigns file name to a variable.
                    
                    if dataFile['contentType'] == 'text/tab-separated-values':          # If the file name finishes by .tab
                        tab_id_old = dataFile['id']                                     # Assign file ID to 'tab_id_old'
                        print(dataFile)
                        print(tab_id_old)

                        tab_xml = get_var_metadata_dataverse(id, tab_id_old)            # Get variable metadata from the dataverse record
                        print(tab_xml)

                        if tab_xml != False and tab_xml is not None:                    # If the newly created file is NOT empty - meaning it successfully pulled content in get_var_metadata_dataverse()
                            result = re.search(r'{((.*))}', tab_xml.tag)                # Using regex library to capture and group all instances of the html/XML tag <ns:0>

                            if result == None:                                          # If 'result' from the above if statement is empty
                                ns_var = ''                                             # Assign an empty string to 'ns_var'

                            else:                                                       # Else, if result is populated
                                ns_var = result.group(0)                                # Assign ns:0 to the variable 'ns_var'

                            dataDscr = tab_xml.find(f"{ns_var}dataDscr")
                            xml = ET.ElementTree(dataDscr)

                            weight_formatter(row, ns_var, xml, dataset_id, tab_id_old)


# This function takes 5 arguments and converts XML files to dictionaries, which are submited to a weighted frequency function.
# which is then used to add weighted frequencies directly in the XML file. This function also pushes the change to the API by calling a previouys function

# row: used to select the CSV row in whcih valuable information is stored.
# ns_var: marker of tags when they're pulled from data explorer/Dataverse
# xml: dataset record holding dataDscr records
# dataset_id: latest version dataset ID
# tab_id_old: ID of the tabular file


def weight_formatter(row, ns_var, xml, dataset_id, tab_id_old):

    weight_var = row['WeightVariable']                                          # Assigning CSV file weight variable to the variable weight_var
    omission = row['WeightException']                                           # Assigning CSV file weight omissions to the variable 'omission'

    vars = xml.findall(f'{ns_var}var')                                          # Create a list of variables.

    for var in vars:                                                            # For all variables in the vars list
        var_name = var.attrib.get("name")                                       # Assigning eTree attribute name to var_name
        if var_name == weight_var:                                              # If the variable name is that of the weight variable
            var.attrib['wgt'] = 'wgt'                                           # Assign it as the weight variable
            weight_id = var.attrib.get('ID')                                    # Assign the variable id to the variable weight_id

    for var in vars:                                                            # For all variables in the vars list (doing 2 for loops here as to identify the weight, and then loop to assign weight var to weighted variables)
        var_name = var.attrib.get('name')                                       # Create list of vars.
        if var_name != omission and var_name != weight_var:                     # If the var name is not a to-be omitted (not-weighted) variable or the weight variable
            var.attrib['wgt-var'] = weight_id                                   # Assign to 'wgt-var' the weight variable ID (e.g. v1432609)

    main_dict = {}                                                              # Create an empty dictionary
    for var in xml.findall(f'{ns_var}var'):                                     # For every variable in the XML file
        var_name = var.attrib.get('name')                                       # Assign eTree attribute 'name' to the variable var_name
        category_data = {}                                                      # Create a new empty dictionary inside the for loop

        for catgry in var.findall(f'{ns_var}catgry'):                           # For every variable category
            labl_element = catgry.find(f'{ns_var}labl')                         # fetch the label element and assign it to the variable labl_element
            print(f'HERE ARE THE LABEL ELEMENTS: {labl_element}')

            if labl_element is not None:                                        # If the label is not empty
                label = labl_element.text                                       # Assign its name to the variable 'label'
                frequency_value = catgry.find(f'{ns_var}catStat')               # Extract the frequency value of the category statistic

                if frequency_value is not None:                                 # If the extracted category frequency is not empty/Null
                    frequency = frequency_value.text                            # Assign the frequency value to the variable 'frequency'
                    category_data[label] = [frequency]

        main_dict[var_name] = category_data                                     # Add the variable name as the main dictionary key, and the previously created dictionary as its value

    print(main_dict)                                                            # Print the main dictionary
    updated_dictionary = calculate_weights(row, main_dict)                      # Assign the result of the function 'calculate weights' to the variable 'updated_dictionary'
    print(updated_dictionary)                                                   # Print the dictionary returned from the above function

    for var in xml.findall(f'{ns_var}var'):                                     # For every variable in the XML file
        var_name = var.attrib.get('name')                                       # Assign eTree attribute 'name' to the variable var_name

        if var_name in updated_dictionary:                                      # for variable keys in the updated dictionary
            if updated_dictionary[var_name] != {}:                              # If the updated dictionary variable is not an empty dictionary

                for catgry in var.findall(f'{ns_var}catgry'):                   # For all the categories in the variable subset
                    labl_element = catgry.find(f'{ns_var}labl')                 # Extract the category label

                    if labl_element is not None:                                # If the label is not empty
                        label = labl_element.text                               # Assign the label the variable 'label'
                        print(f'THIS IS THE LABEL: {label}')
                        val = updated_dictionary[var_name][label]               # Fetches the list value of the category
                        print(f'THIS IS VAL: {val}')
                        new_entry = ET.Element(f'{ns_var}catStat')              # Create a new element location
                        new_entry.set('type', 'freq')                           # Create necessary attribute documentation for the element
                        new_entry.set('wgtd', 'wgtd')                           # Create necessary attribute documentation for the element
                        new_entry.set('wgt-var', weight_id)

                        if len(val) == 1:                                       # if the length of the list value is 1 in length (meaning the numerical text value is 0)
                            new_entry.text = str(val[0])                        # Reuse value 0
                        else:                                                   # Otherwise
                            new_entry.text = str(val[1])                        # Use index 1 to fetch the weighted frequency

                        catgry.append(new_entry)                                # Append new element as a subelement of the category

    updated_xml = xml.getroot()                                                 # Return to the XML file root
    newest_xml = new_groups(updated_xml, ns_var)

    namespace = 'http://www.icpsr.umich.edu/DDI'
    new_parent = ET.Element(f"{{{namespace}}}codeBook", version="2.0")
    new_parent.append(newest_xml)

    xml_string = ET.tostring(new_parent, encoding='utf8', method='xml').decode('utf8')      # up xml as a string (must be a string to push to dataverse)

    xml_string = xml_string.replace('ns0:', '')

    with open(f"/data/data_lfs_rebased/data_EPA_Remanie/XML_FILES/{row['Month Name and Year']}.xml", 'w') as f:
        f.write(xml_string)
        
    var_update_dataset(dataset_id, tab_id_old, xml_string)                                  # Maybe an issue with XML string?


# This function takes 2 arguments and calculates the weighted frequencies of various variables.
# row: used to select the CSV row in whcih valuable information is stored.
# main_dict: dictionary of categories and associated values extracted from the DDI XML file.


def calculate_weights(row, main_dict):

    weight_var = row['WeightVariable']                                          # Assigning CSV file weight variable to the variable weight_var
    omission = row['WeightException']                                           # Assigning CSV file weight omissions to the variable 'omission'
    print(weight_var)
    print(omission)

    filename = row['sav directory']
    print(filename)

    new_prefix = '/data/data_lfs_rebased/data_EPA_Remanie'
    filename = f'{new_prefix}{filename}'                                        #filename.replace("D:\My_windows_files\data_EPA_Remanie", new_prefix)
    print(filename)

    filename = filename.replace("\\", "/")
    print(filename)
    df = pd.read_spss(filename)
    print(df.head())

    variable_list = []                                                          # Creating and empty list
    for col in df:                                                              # For columns in the dataframe
        if col != weight_var and col != omission:                               # If the column name is not that of the weight variable or omitted variables
            variable_list.append(col)                                           # Add it to variable_list

    for key in main_dict:                                                                   # For keys in the main dictionary
        if key in variable_list:                                                            # If the key is in the list of variables
            weighted_df = df.groupby([key], observed=False).FINALWT.sum().reset_index()     # Collapse and sum all FINALWT values as a function of category

            for index, row in weighted_df.iterrows():                                   # For columns and rows in the newly created weighted_df dataframe
                label = row[key]                                                        # Category label is fetched by parsing through the dataframe column and finding
                frequency = row[weight_var]                                             # Weighted frequency is extracted from the corresponding category row

                if label in main_dict[key]:                                         # If the label is in the main dictionary category dictionary
                    main_dict[key][label].append(frequency)                         # Append the weighted frequency next to the corresponding non-weighted frequency.

    return main_dict                                                                # Return the updated main_dict


# This function creates new groups and takes 2 arguments - though it also requires an XML template file
# updated_xml: variable derived from the dataverse-retrieved variable metadata (meaning it is an xml format that uses ns0:)
# ns_var: namespace tag ns0: (that's how I understand ns0: at least)

# for this function to work, it assumes that the user has identified the directory of a local xml file
# This XML file should have all the variable groups already created (it can be a download from a dataverse tab file)

# This pulls the IDs from each group, seeks and lists their variable names
# The function then uses this list of names to fetch all IDs of the variables that have the same name in the current XML file


def new_groups(updated_xml, ns_var):

    template = ET.parse('/data/data_lfs_rebased/data_EPA_Remanie/xml_template.xml')             # Parsing XML file used as template
    template_root = template.getroot()                                                          # Setting up etree root
    namespaces = {'ddi': 'http://www.icpsr.umich.edu/DDI'}                                      # Defining the namespace dictionary - this seems to be mandatory when we import an XML proper (not necessary when extracted from dataverse)

    grouping = updated_xml.findall(f'{ns_var}varGrp')                                           # Creating list of all variable groups currently existing in the current file xml
    for grp in grouping:                                                                        # For every variable group in the list of variable groups
        updated_xml.remove(grp)                                                                 # Delete the group from the XML record

    x = 0                                                                                       # Create an index variable ======= Note: x starts 0 - that way var groups appear at the top of the XML record under dataDscr (relevant later)
    vars = updated_xml.findall(f'{ns_var}var')                                                  # From the file XML, retrieve and list all variables
    groups_template = template_root.findall('ddi:dataDscr/ddi:varGrp', namespaces)              # From the etree template, retrieve and list all variable groups

    for group in groups_template:
        labl_element = group.find('ddi:labl', namespaces)                                  # Retrieve the label of the variable using its ID

        if labl_element is not None:                                                       # If the label is not empty (it shouldn't ever be empty to be honest)
            label = labl_element.text                                                      # Assign the text value to the variable "label"

        variables_template = group.attrib.get('var')                                       # Retrieve the variable IDs (all in a same string) from the variable group
        var_grp_template = variables_template.split(' ')                                   # List all variables in the string by delineating them at spaces

        group_list_template = []                                                           # Create an empty list
        variable_name = template_root.findall('ddi:dataDscr/ddi:var', namespaces)          # List all variables found in the template

        for ids in var_grp_template:                                                       # for variable IDs in the variable groups
            for var in variable_name:                                                      # For the variables in the variable name list
                tex_val = var.attrib.get('ID')                                             # Assigns the ID to the variable tex_val
                if ids == tex_val:                                                         # If the ID the loop is parsing through is the same as tex_val
                    group_list_template.append(var.attrib.get('name'))                     # Add the variable name to group_list

        new_id_list = []                                                        # Create an empty list that will hold IDs

        for var in vars:                                                        # for all variables pulled from the current dataverse record
            var_name = var.attrib.get('name')                                   # Assign the variable name to var_name
            if var_name in group_list_template:                                 # If the pulled variable name appears in the template group list
                new_id_list.append(var.attrib.get('ID'))                        # Add the ID from the dataverse record to new_id_list

        string_setup = " ".join(new_id_list)                                    # Create a list holding the list items (joined at spaces)
        print(string_setup)                                                     # This is optional - good for comparing to an XML record

        group_entry = ET.Element(f'{ns_var}varGrp')                             # Here we create the new element to be added in the dataverse XML record
        group_entry.set('ID', group.attrib.get('ID'))                           # Create necessary attribute documentation for the element
        group_entry.set('var', string_setup)                                    # Create necessary attribute documentation for the element
        print(ET.tostring(group_entry))                                         # Print the to-be added varGrp entry

        group_label = ET.SubElement(group_entry, 'labl')                        # Create a subelement for the above group entry, name it labl (this follows DDI standards)
        group_label.text = label                                                # Label text value is set to the name of the group (pulled from the XML template earlier)
        print(ET.tostring(group_label))                                         # Print the to-be added labl subelement

        updated_xml.insert(x, group_entry)                                      # Insert the created group entry at index x - note that group_label is automatically added as a subelement of the group entry
        x += 1                                                                  # Update index parser by one (otherwise the groups are added in descending order)

    return updated_xml                                                          # Retrun the updated xml record


# This function is called in the main function. It takes 2 arguments
# The first is the ID of the dataset we wish to update. And the second is the cell
# for which the column is labeled 'File Description'. (the cell that contains the description)

def production_initial_ingest(date):

    dir_prefix = "/data/data_lfs_rebased/data_EPA_Remanie"                      # setting up directory (this is likely to change)

    with open(f"{dir_prefix}/Rebasing/{date}", newline='') as csvfile:          # Reading in file using the rebasing CSV file created by Ethan (in English) and Thierry (in French)
        reader = csv.DictReader(csvfile)

        for row in reader:                                                      # Reading lines within the CSV file.
            print(row)

            doi = row['DOI in Dataverse']              # Fetch DOI from imported CSV file (in this case the LFS/EPA rebasing)
            print(doi)

            filename = row['Replace with /path']
            print(filename)

            filename = f'{dir_prefix}{filename}'        #filename.replace("D:\My_windows_files\data_EPA_Remanie", dir_prefix)
            print(filename)

            filename = filename.replace("\\", "/")
            print(filename)

            if 'doi.org/' in doi:
                doi = doi.replace('doi.org/', 'doi:')
            print(doi)

            ################################################################################
            ################################################################################
            ################################################################################
            ################################################################################
            ################################################################################
            ################################################################################
            ################################################################################

            resp = api_origin.get_dataset(doi, version="5.0")                   # Doesn't need to set to most recent version, it would seem.
            tab_id_old = 0                                                      # Creating empty dictionaries, and setting IDs at 0.
            tab_file_old = {}
            tab_id_new = 0
            tab_file_new = {}

            if resp.status_code == 200:                                         # If API call is successful (marker 200)
                id = resp.json()['data']['id']                                  # old dataset ID is assigned to variable id
                latest_version = resp.json()['data']['latestVersion']           # Latest old dataset version is set to variable list "latest_version"

                files = latest_version['files']                                 # old file latest version is set to variable list 'files'
                dataset_id = latest_version['datasetId']                        # sets old dataset ID to variable 'dataset_id' - this could be added on the step at line 54
                print(files)

                for file in files:                                              # For loop running curl commands to create new dataset version?
                    print(file)                                                 # curl -H "X-Dataverse-key:$API_TOKEN" -X DELETE "$SERVER_URL/api/files/$ID" (curl command equivalent)
                    dataFile = file['dataFile']                                 # Assigns file name to a variable.
                    print(dataFile)

                    if dataFile['contentType'] == 'text/tab-separated-values':      # If the file name finishes by .tab
                        tab_id_old = dataFile['id']                                 # Assign file ID to 'tab_id_old'
                        tab_file_old = file                                         # Assign the file in question in dictionary 'tab_file_old'

                    delete_file_url = (url_base_origin + "/api/files/" + str(dataFile['id']))       # Creating to-be deleted URL containg the old file ID
                    print(delete_file_url)

                    req = requests.delete(delete_file_url, headers=headers_origin)                  # If dataset is locked (for whatever reason), do not delete the URL
                    print(req.status_code)

                    if not check_lock(dataset_id):                                                  # Running check_lock function defined above.
                        print(f"Could not delete dataset {doi}")
                        exit(0)

                print(doi)
                print(filename)

                resp = api_origin.upload_datafile(doi, filename)                        # Setting up to-be uploaded files information - assigning to variable resp

                if resp.status_code == 200:                                             # Checking if status code is 200 (successful access)

                    if check_lock(dataset_id):                                          # Checking if submission successful
                        print("Upload success")
                        resp = api_origin.get_dataset(doi)
                        draft = resp.json()['data']['latestVersion']                    # Assigning most recent version as draft
                        files = draft['files']                                          # Adding all submitted files to list variable 'files'

                        for file in files:                                              # For loop parsing through files list
                            dataFile = file['dataFile']                                 # curl -H "X-Dataverse-key:$API_TOKEN" -X DELETE "$SERVER_URL/api/files/$ID" (curlo command equivalent)
                            print(file)
                            print(dataFile)

                            if dataFile['contentType'] == 'text/tab-separated-values':      # Checking if selected file is tabular
                                tab_id_new = dataFile['id']                                 # Assigns tab file ID to variable tab_id_new
                                tab_file_new = file

                        print(id)                                                       # Printing the dataset ID
                        print(tab_id_old)                                               # Printing old tabular file ID
                        print(tab_id_new)                                               # Printing new tabular file ID

                        update_dataset(id, tab_id_old, tab_id_new)                      # Running functions defined in a different section of the code above
                        update_file_metadata(tab_id_new, row['File Description'])       # Running function described above

                    else:                                                               # Otherwise, if submission is not successful
                        print("Upload failed")                                          # Print upload failure update
                        continue                                                        # Procede to next item

                else:                                                                   # Otherwise, if the response code is not 200
                    continue                                                            # continue to the next item

                update_citation(latest_version, row, doi)                               # Runs function defined above
                update_geographic_field(latest_version, row, doi)
                update_alt_titles(latest_version, row, doi)

            else:
                exit(0)


# MAIN FUNCTION


#  _    _           _       _         _____  _               _                     _    _
# | |  | |         | |     | |       |  __ \(_)             | |                   | |  | |
# | |  | |_ __   __| | __ _| |_ ___  | |  | |_ _ __ ___  ___| |_ ___  _ __ _   _  | |__| | ___ _ __ ___
# | |  | | '_ \ / _` |/ _` | __/ _ \ | |  | | | '__/ _ \/ __| __/ _ \| '__| | | | |  __  |/ _ \ '__/ _ \
# | |__| | |_) | (_| | (_| | ||  __/ | |__| | | | |  __/ (__| || (_) | |  | |_| | | |  | |  __/ | |  __/
#  \____/| .__/ \__,_|\__,_|\__\___| |_____/|_|_|  \___|\___|\__\___/|_|   \__, | |_|  |_|\___|_|  \___|
#        | |                                                                __/ |
#        |_|                                                               |___/


def main():
    date = 'path/to/year/file/2022-2021.csv'
    production_initial_ingest(date)
    post_processing(date)


if __name__ == '__main__':
    main()
