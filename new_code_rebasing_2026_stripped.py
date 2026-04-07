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

api_token_origin = "ENTER_API_KEY_HERE"
url_base_origin = 'https://borealisdata.ca'

headers_origin = {'X-Dataverse-key': api_token_origin}
api_origin = NativeApi(url_base_origin, api_token_origin)
data_api_origin = DataAccessApi(url_base_origin, api_token_origin)



# This function checks if a dataset is locked (for one reason or another; it could be due to .tab file ingestion, for instance)
# More documentation on what this entails available here: https://guides.dataverse.org/en/6.2/api/native-api.html#dataset-locks

def check_lock(dataset_id):

    time_start = datetime.now()
    print("Start check_lock")

    try:
        url = f"{url_base_origin}/api/datasets/{dataset_id}/locks"
        lock = requests.get(url, headers_origin)

        if lock.status_code == 503:
            print("503 - Server is unavailable")
            sys.exit()

        a = 0
        while len(lock.json()['data']) > 0:
            print(f"Lock {str(a)} times {dataset_id} {lock.json()}")
            print(lock.json())
            time.sleep(10)
            a += 1

            lock = requests.get(url, headers_origin)
            if lock.status_code == 503:
                print("503 - Server is unavailable")
                sys.exit()

            if lock.status_code != 200:
                print(f"check_lock func: lock status {str(lock.status_code)} for {dataset_id}")
                return False

    except Exception as e:
        print(f"check_lock. Error {str(e)}, dataset {dataset_id}")
        return False

    time_end = datetime.now()
    t = time_end - time_start
    print(f"Dataset {str(dataset_id)} was locked {str(t.total_seconds())} sec")

    return True



def get_var_metadata_dataverse(dataset_id, datafile_id):

    print("Start get_var_metadata_dataverse")
    lock = check_lock(dataset_id)
    url = url_base_origin

    if lock:
        url = f"{url}/api/access/datafile/{datafile_id}/metadata"
        resp = requests.get(url, headers=headers_origin)

        if resp.status_code == 200:
            tree = ET.fromstring(resp.content)
            return tree

        else:
            print(f"get_var_metadata_dataverse: dataset_id = {dataset_id} datafile_id = {datafile_id} url = {url}")
            return False

    else:
        print(f"get_var_metadata_dataverse: dataset_id = {dataset_id} datafile_id = {datafile_id} url ={url} locking problem")
        return False



# This function extracts variable data from the selected dataverse file

def map_label_var(dataDscr, ns):

    print("Start map_label_var")
    map_name_id = {}
    vars = dataDscr.findall(f'{ns}var')

    for var in vars:
        ID = var.attrib.get("ID")
        name = var.attrib.get("name")
        map_name_id[name] = ID

    return map_name_id



# This function matches variable IDs to their corresponding IDs in the new/old file.
# Takes arguments defined in a below function -> updated_dataset()
# map_current_file (i will change this) is the variable 'map_name_id_current_file'
# map_new_file (i will also change this) is the variable 'map_name_id_new_file'

def var_ids_correspondence(map_current_file, map_new_file):
    print("Start var_ids_correspondence")
    print(map_current_file)
    print(map_new_file)

    map_ids = {}
    map_ids_n_d = {}

    for item in map_new_file:
        if item in map_current_file:
            map_ids[map_new_file[item]] = map_current_file[item]
            
        else:
            if item.upper() in map_current_file:
                map_ids[map_new_file[item]] = map_current_file[item.upper()]

            else:
                if item.lower() in map_current_file:
                    map_ids[map_new_file[item]] = map_current_file[item.lower()]

    for item in map_current_file:
        if item in map_new_file:
            map_ids_n_d[map_current_file[item]] = map_new_file[item]

        else:
            if item.lower() in map_new_file:
                map_ids_n_d[map_current_file[item]] = map_new_file[item.lower()]

            else:
                if item.upper() in map_new_file:
                    map_ids_n_d[map_current_file[item]] = map_new_file[item.upper()]
                    
    return map_ids, map_ids_n_d



# This function updates variable metadata (harmonisation) between all the dictionaries and XML files.
# This function takes 6 arguments. map_ids and map_ids_n_d ({name: ID} dictionaries cross referencing old/new and new/old dictionaries)
# 2 dataDscr arguments (these are XML files from which <ns0:dataDscr> variable data is extracted - both in the new and old file)
# ns_var (new) and ns (old) file tags, i believe both are <ns:0>, or 'ns:0'

def update_var_ddi(map_ids, map_ids_n_d, dataDscr_new_file, dataDscr_current_file, ns_var, ns):

    print("Start update_var_ddi")
    print(map_ids)
    print(map_ids_n_d)

    grps = dataDscr_current_file.findall(f'{ns}varGrp')

#################################### GROUPS ####################################

    for var_grp in grps:
        grp_id = var_grp.get("ID")
        F1 = grp_id[-2:]

        # this F1 stuff is deprecated
        if F1 == "F1":
            lng = len(grp_id)
            grp_id = grp_id[0 : lng - 2]
            var_grp.set('ID', grp_id)

        wgt_var = var_grp.get("var")
        if wgt_var != None:
            w_var = wgt_var.split(" ")
            w_str = ""
            
            for w in w_var:
                if w in map_ids_n_d:

                    if w_str == "":
                        w_str = map_ids_n_d[w].strip()

                    else:
                        w_str = f'{w_str} {map_ids_n_d[w].strip()}'

                else:
                    print(w)

            if w_str != "":
                var_grp.set('var', w_str)

        dataDscr_new_file.append(var_grp)

################################# VARIABLES ####################################

    vars = dataDscr_new_file.findall(f'{ns_var}var')
    print(vars)

    for var in vars:
        id_new_file = var.attrib.get("ID")
        print(f"Dataverse ID: {id_new_file}")

        if id_new_file in map_ids:
            id_current_file = map_ids[id_new_file]
            print(f"Current_file ID: {id_current_file}")

        else:
            continue
        
########################## VARIABLE LEVEL METADATA #############################

        # WEIGHT VARIABLE
        var_current_file = dataDscr_current_file.find(f'{ns}var[@ID="{id_current_file}"]')
        wgt_var = var_current_file.get("wgt-var")
        print(ET.tostring(var_current_file, encoding='unicode'))
        print(wgt_var)

        if wgt_var != None:
            w_var = wgt_var.split(" ")
            w_str = ""

            for w in w_var:
                if w_str == "":
                    print(w)

                    if w in map_ids_n_d:
                        w_str = map_ids_n_d[w].strip()

                else:
                    if w in map_ids_n_d:
                        w_str = f'{w_str} {map_ids_n_d[w].strip()}'

            if w_str != "":
                var.set('wgt-var', w_str)

        wgt = var_current_file.get("wgt")
        if wgt != None:
            var.set("wgt", wgt)

        # VARIABLE QUESTION
        qstn_current_file = var_current_file.find(ns + 'qstn')
        print(ET.tostring(var_current_file, encoding='unicode'))
        print("-----")
        
        if qstn_current_file is not None:
            print(ET.tostring(qstn_current_file, encoding='unicode'))

        if qstn_current_file != None:
            var.append(qstn_current_file)

        # VARIABLE NOTES
        notes_current_file = var_current_file.findall(f'{ns}notes')
        for note in notes_current_file:
            var.append(note)

        # VARIABLE UNIVERSE
        universe_current_file = var_current_file.find(f'{ns}universe')
        if (universe_current_file != None):
            var.append(universe_current_file)

            # VARIABLE FREQUENCY WEIGHT
            catgry_current_file = var_current_file.findall(f'{ns}catgry')
            catgrys = var.findall(f'{ns_var}catgry')

            for catgry in catgry_current_file:
                catStat_current_file = catgry.find(f'{ns}catStat[@wgtd="wgtd"]')

                if catStat_current_file != None:
                    catValu = catgry.find(f'{ns}catValu')

                    if catValu != None:
                        text = (catValu.text)

                        for ct in catgrys:
                            if ct.find(f'{ns_var}catValu').text.strip() == text.strip():
                                ct.append(catStat_current_file)
                                break

    return dataDscr_new_file



# This function takes three arguments. id, file_id_new, xml_string from the 'update_dataset()' function
# Refer to the function mentioned in the previous online for more information
# Arguments (in order) are the variables id, file_id_new, and xml_string

def var_update_dataset(dataset_id, datafile_id, xml):
    print("Start var_update_dataset")

    url = f'{url_base_origin}/api/edit/{str(datafile_id)}'
    check = check_lock(dataset_id)
    if check == False:
        return check 

    try:
        resp = requests.put(url, headers=headers_origin, data=xml)
        if resp.status_code != 200:
            print(resp.json())
            return False

        else:
            print("Updated")

    except Exception as e:
        print(f"var_update_dataset: {str(e)} {url}")
        return False

    return True



# This function is used to update updated datasets
# It takes 3 arguments, all of which are defined and listed in the main() function
# 'File_id_old' is 'tab_id_old' (old tabular file), 'file_id_new' is 'tab_id_new'(new tabular file),
# and 'id' is the dataset id (stays the same i reckon)

def update_dataset(id, file_id_old, file_id_new):

    print(f"Draft id {file_id_new}")
    var_xml = get_var_metadata_dataverse(id, file_id_new)

    if var_xml != False and var_xml != None:
        result = re.search(r'{(.*)}', var_xml.tag)

        if result == None:
            ns_var = ''

        else:
            ns_var = result.group(0)

        dataDscr_new_file = var_xml.find(f"{ns_var}dataDscr")
        print(f"Published id {file_id_old}")
        
        # This step is the same as the one above
        var_xml_current_file = get_var_metadata_dataverse(id, file_id_old)
        print(var_xml_current_file)


        if var_xml_current_file != False and var_xml_current_file != None:
            result = re.search(r'{(.*)}', var_xml_current_file.tag)

            if result == None:
                ns = ''
            else:
                ns = result.group(0)

        else:
            return False

        dataDscr_current_file = var_xml_current_file.find(f"{ns}dataDscr")

        # At this point, we have retrieved the metadata content on the old and new tabular file, and extracted their XML metadata.
        # In order to transfer metadata (similarly to 'Import XML' in data explorer) we need to match the two XML files in terms of variable IDs
        # The following called functions do just that. These functions are defined and commented in an above section.
        map_name_id_new_file = map_label_var(dataDscr_new_file, ns_var)
        map_name_id_current_file = map_label_var(dataDscr_current_file, ns)
        ids_maps = var_ids_correspondence(map_name_id_current_file, map_name_id_new_file)
        print("Before update_var_ddi")

        dataDscr_dv_updated = update_var_ddi(ids_maps[0], ids_maps[1], dataDscr_new_file, dataDscr_current_file, ns_var, ns)
        
        print("After update var ddi")

        xml_updated = ET.ElementTree(dataDscr_dv_updated)
        xml_string = ET.tostring(dataDscr_dv_updated, encoding='utf8', method='xml')

        if var_update_dataset(id, file_id_new, xml_string):
            return True

    return False



# This function is called in the main function. It takes 2 arguments
# The first is the ID of the dataset we wish to update. And the second is the cell
# for which the column is labeled 'File Description'. (the cell that contains the description)

def update_file_metadata(tab_id_new, description):

    metadata_file = '{"description":' + '"' + description + '"}'
    url = f'{url_base_origin}/api/files/{str(tab_id_new)}/metadata'

    print(url)
    print(metadata_file)

    resp = api_origin.update_datafile_metadata(tab_id_new, metadata_file, False)
    print(resp)



# This function is used to update the dataset citation information. It takes 3 arguments - latest_version, row, and doi
# Latest version is a version code pulled from an API call in main (?) - latest old version
# row is a variable that is obtained by parsing through a CSV - it is for-looped in the main function
# doi is extracted from the csv file used for the rebasing.

def update_citation(latest_version, row, doi):

    updated_fields = {}
    updated_fields['fields'] = []
    metadataBlocks = latest_version['metadataBlocks']
    fields = metadataBlocks['citation']['fields']
    access_to_sources = False
    notes = False
    note = row['Variable Revision in Metadata: Citation > Notes'].strip()
    omission = row['Remove from Title']

    print('############################')
    print(fields)
    print('############################')

    for field in fields:
        if field['typeName'] == 'title':

            if omission in field['value']:
                field['value'] = field['value'].replace(omission, "")

            field['value'] = f"{field['value']} {row['Title > Additions']}"
            updated_fields['fields'].append(field)

        if field['typeName'] == 'dsDescription':
            value = field['value']

            for v in value:
                if ('dsDescriptionValue' in v):
                    print(v['dsDescriptionValue'])
                    print(v['dsDescriptionValue']['value'])
                    v['dsDescriptionValue']['value'] = row['Revision Additions: Citation > Descriptions']
                    
            updated_fields['fields'].append(field)


        # KEYWORD VALUE UPDATE SECTION
        if field['typeName'] == 'keyword':
            new_keywords = row['Keywords'].split(', ')
            print(f'Adding new Keywords: {new_keywords}')
            keyword_list = []

            for words in new_keywords:
                main_keyword_field = {}
                field_keyword = {}
                field_keyword['typeName'] = 'keywordValue'
                field_keyword['multiple'] = 'False'
                field_keyword['typeClass'] = 'primitive'
                field_keyword['value'] = words
                main_keyword_field['keywordValue'] = field_keyword
                keyword_list.append(main_keyword_field)

            print(keyword_list)
            keyword_rep = {}
            keyword_rep['typeName'] = 'keyword'
            keyword_rep['multiple'] = True
            keyword_rep['typeClass'] = 'compound'
            keyword_rep['value'] = keyword_list
            updated_fields['fields'].append(keyword_rep)

        if field['typeName'] == 'notesText':
            notes = True
            if note != None and note != '':
                field['value'] = notes
                updated_fields['fields'].append(field)

    if not notes and note != None and note != '':
        print('No notes')

        field_notes = {}
        field_notes['typeName'] = "notesText"
        field_notes['multiple'] = False
        field_notes['typeClass'] = "primitive"
        field_notes['value'] = row['Variable Revision in Metadata: Citation > Notes']
        updated_fields['fields'].append(field_notes)

    url = f'{url_base_origin}/api/datasets/:persistentId/editMetadata?persistentId={doi}&replace=true'
    print(url)

    resp = requests.put(url, data=json.dumps(updated_fields), headers=headers_origin)
    print(resp.status_code)

    if resp.status_code == 200:
        return True
    else:
        return False




def update_geographic_field(latest_version, row, doi):

    updated_geo = {}
    metadataBlocks_geo = latest_version['metadataBlocks']
    geo_fields = metadataBlocks_geo['geospatial']['fields']

    print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
    print(geo_fields)
    print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%')

    unit_to_replace = geo_fields[1]
    print(unit_to_replace)

    new_unit = [row['Geographic Unit']]
    print(f'New Geographic Unit: {new_unit}')

    new_geo_entry = {}
    new_geo_entry['typeName'] = 'geographicUnit'
    new_geo_entry['multiple'] = True
    new_geo_entry['typeClass'] = 'primitive'
    new_geo_entry['value'] = new_unit

    print(new_geo_entry)
    geo_fields[1] = new_geo_entry

    updated_geo['fields'] = geo_fields
    print(json.dumps(updated_geo))

    url = f'{url_base_origin}/api/datasets/:persistentId/editMetadata?persistentId={doi}&replace=true'
    print(url)
    print(updated_geo)

    resp = requests.put(url, data=json.dumps(updated_geo), headers=headers_origin)
    print(resp.status_code)

    if resp.status_code == 200:
        return True
    else:
        return False



# Update alt titles.

def update_alt_titles(latest_version, row, doi):

    metadataBlocks = latest_version['metadataBlocks']
    fields = metadataBlocks['citation']['fields']

    print('*********************************************************')
    print(fields)
    print('*********************************************************')

    print(row)
    fore = row['Other Language Name']
    print(fore)
    center = row['Other Language Month']
    print(center)
    center_2 = row['\ufeffYear']
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

    new_title_entry = {}
    new_title_entry['typeName'] = 'alternativeTitle'
    new_title_entry['multiple'] = True
    new_title_entry['typeClass'] = 'primitive'
    new_title_entry['value'] = alt_list
    print(new_title_entry)

    url = f'{url_base_origin}/api/datasets/:persistentId/editMetadata?persistentId={doi}&replace=true'
    resp = requests.put(url, json.dumps(new_title_entry), headers=headers_origin)
    print(resp.status_code)

    if resp.status_code == 200:
        return True
    else:
        return False



# This function takes no argument, it is run after the initial_ingest series of function.
# This function fetches information about the dataset DOI, weight variable, and weight exception data from the CSV file
# It then pulls information from the dataset by doing an API call
# Also conducts file formatting for later use.

def post_processing(date):

    with open(f'/data/data_lfs_rebased/data_EPA_Remanie/Rebasing/{date}', newline='') as csvfile:

        reader = csv.DictReader(csvfile)

        for row in reader:
            print(row)

            doi = row['Persistent Identifier']
            weight_var = row['WeightVariable']
            omission = row['WeightException']
            print(doi)

            resp = api_origin.get_dataset(doi, version="5.0")

            if resp.status_code == 200:
                id = resp.json()['data']['id']
                latest_version = resp.json()['data']['latestVersion']

                files = latest_version['files']
                dataset_id = latest_version['datasetId']

                for file in files:
                    dataFile = file['dataFile']
                    
                    if dataFile['contentType'] == 'text/tab-separated-values':
                        tab_id_old = dataFile['id']
                        print(dataFile)
                        print(tab_id_old)

                        tab_xml = get_var_metadata_dataverse(id, tab_id_old)
                        print(tab_xml)

                        if tab_xml != False and tab_xml is not None:
                            result = re.search(r'{((.*))}', tab_xml.tag)

                            if result == None:
                                ns_var = ''

                            else:
                                ns_var = result.group(0)

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

    weight_var = row['WeightVariable']
    omission = row['WeightException']

    vars = xml.findall(f'{ns_var}var')

    for var in vars:
        var_name = var.attrib.get("name")
        if var_name == weight_var:
            var.attrib['wgt'] = 'wgt'
            weight_id = var.attrib.get('ID')

    for var in vars:
        var_name = var.attrib.get('name')
        if var_name != omission and var_name != weight_var:
            var.attrib['wgt-var'] = weight_id

    main_dict = {}
    for var in xml.findall(f'{ns_var}var'):
        var_name = var.attrib.get('name')
        category_data = {}

        for catgry in var.findall(f'{ns_var}catgry'):
            labl_element = catgry.find(f'{ns_var}labl')
            print(f'HERE ARE THE LABEL ELEMENTS: {labl_element}')

            if labl_element is not None:
                label = labl_element.text
                frequency_value = catgry.find(f'{ns_var}catStat')
                
                if frequency_value is not None:
                    frequency = frequency_value.text
                    category_data[label] = [frequency]

        main_dict[var_name] = category_data

    print(main_dict)
    updated_dictionary = calculate_weights(row, main_dict)
    print(updated_dictionary)

    for var in xml.findall(f'{ns_var}var'):
        var_name = var.attrib.get('name')

        if var_name in updated_dictionary:
            if updated_dictionary[var_name] != {}:

                for catgry in var.findall(f'{ns_var}catgry'):
                    labl_element = catgry.find(f'{ns_var}labl')

                    if labl_element is not None:
                        label = labl_element.text
                        print(f'THIS IS THE LABEL: {label}')
                        val = updated_dictionary[var_name][label]
                        print(f'THIS IS VAL: {val}')
                        new_entry = ET.Element(f'{ns_var}catStat')
                        new_entry.set('type', 'freq')
                        new_entry.set('wgtd', 'wgtd')
                        new_entry.set('wgt-var', weight_id)

                        if len(val) == 1:
                            new_entry.text = str(val[0])
                        else:
                            new_entry.text = str(val[1])

                        catgry.append(new_entry)

    updated_xml = xml.getroot()
    newest_xml = new_groups(updated_xml, ns_var)

    namespace = 'http://www.icpsr.umich.edu/DDI'
    new_parent = ET.Element(f"{{{namespace}}}codeBook", version="2.0")
    new_parent.append(newest_xml)

    xml_string = ET.tostring(new_parent, encoding='utf8', method='xml').decode('utf8')

    xml_string = xml_string.replace('ns0:', '')

    with open(f"/data/data_lfs_rebased/data_EPA_Remanie/XML_FILES/{row['Month Name and Year']}.xml", 'w') as f:
        f.write(xml_string)
        
    var_update_dataset(dataset_id, tab_id_old, xml_string)



# This function takes 2 arguments and calculates the weighted frequencies of various variables.
# row: used to select the CSV row in whcih valuable information is stored.
# main_dict: dictionary of categories and associated values extracted from the DDI XML file.

def calculate_weights(row, main_dict):

    weight_var = row['WeightVariable']
    omission = row['WeightException']
    print(weight_var)
    print(omission)

    filename = row['sav directory']
    print(filename)

    new_prefix = '/data/data_lfs_rebased/data_EPA_Remanie'
    filename = f'{new_prefix}{filename}'
    print(filename)

    filename = filename.replace("\\", "/")
    print(filename)
    df = pd.read_spss(filename)
    print(df.head())

    variable_list = []
    for col in df:
        if col != weight_var and col != omission:
            variable_list.append(col)

    for key in main_dict:
        if key in variable_list:
            weighted_df = df.groupby([key], observed=False).FINALWT.sum().reset_index()

            for index, row in weighted_df.iterrows():
                label = row[key]
                frequency = row[weight_var]

                if label in main_dict[key]:
                    main_dict[key][label].append(frequency)

    return main_dict



# This function creates new groups and takes 2 arguments - though it also requires an XML template file
# updated_xml: variable derived from the dataverse-retrieved variable metadata (meaning it is an xml format that uses ns0:)
# ns_var: namespace tag ns0: (that's how I understand ns0: at least)

# for this function to work, it assumes that the user has identified the directory of a local xml file
# This XML file should have all the variable groups already created (it can be a download from a dataverse tab file)

# This pulls the IDs from each group, seeks and lists their variable names
# The function then uses this list of names to fetch all IDs of the variables that have the same name in the current XML file

def new_groups(updated_xml, ns_var):

    template = ET.parse('/data/data_lfs_rebased/data_EPA_Remanie/xml_template.xml')
    template_root = template.getroot()
    namespaces = {'ddi': 'http://www.icpsr.umich.edu/DDI'}

    grouping = updated_xml.findall(f'{ns_var}varGrp')
    for grp in grouping:
        updated_xml.remove(grp)

    x = 0
    vars = updated_xml.findall(f'{ns_var}var')
    groups_template = template_root.findall('ddi:dataDscr/ddi:varGrp', namespaces)

    for group in groups_template:
        labl_element = group.find('ddi:labl', namespaces)

        if labl_element is not None:
            label = labl_element.text

        variables_template = group.attrib.get('var')
        var_grp_template = variables_template.split(' ')

        group_list_template = []
        variable_name = template_root.findall('ddi:dataDscr/ddi:var', namespaces)

        for ids in var_grp_template:
            for var in variable_name:
                tex_val = var.attrib.get('ID')
                if ids == tex_val:
                    group_list_template.append(var.attrib.get('name'))

        new_id_list = []

        for var in vars:
            var_name = var.attrib.get('name')
            if var_name in group_list_template:
                new_id_list.append(var.attrib.get('ID'))

        string_setup = " ".join(new_id_list)
        print(string_setup)

        group_entry = ET.Element(f'{ns_var}varGrp')
        group_entry.set('ID', group.attrib.get('ID'))
        group_entry.set('var', string_setup)
        print(ET.tostring(group_entry))

        group_label = ET.SubElement(group_entry, 'labl')
        group_label.text = label
        print(ET.tostring(group_label))

        updated_xml.insert(x, group_entry)
        x += 1

    return updated_xml



# This function is called in the main function. It takes 2 arguments
# The first is the ID of the dataset we wish to update. And the second is the cell
# for which the column is labeled 'File Description'. (the cell that contains the description)

def production_initial_ingest(date):

    dir_prefix = "/data/data_lfs_rebased/data_EPA_Remanie"

    with open(f"{dir_prefix}/Rebasing/{date}", newline='') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            print(row)

            doi = row['DOI in Dataverse']
            print(doi)

            filename = row['Replace with /path']
            print(filename)

            filename = f'{dir_prefix}{filename}'
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

            resp = api_origin.get_dataset(doi, version="5.0")
            tab_id_old = 0
            tab_file_old = {}
            tab_id_new = 0
            tab_file_new = {}

            if resp.status_code == 200:
                id = resp.json()['data']['id']
                latest_version = resp.json()['data']['latestVersion']

                files = latest_version['files']
                dataset_id = latest_version['datasetId']
                print(files)

                for file in files:
                    print(file)
                    dataFile = file['dataFile']
                    print(dataFile)

                    if dataFile['contentType'] == 'text/tab-separated-values':
                        tab_id_old = dataFile['id']
                        tab_file_old = file

                    delete_file_url = (url_base_origin + "/api/files/" + str(dataFile['id']))
                    print(delete_file_url)

                    req = requests.delete(delete_file_url, headers=headers_origin)
                    print(req.status_code)

                    if not check_lock(dataset_id):
                        print(f"Could not delete dataset {doi}")
                        exit(0)

                print(doi)
                print(filename)

                resp = api_origin.upload_datafile(doi, filename)

                if resp.status_code == 200:

                    if check_lock(dataset_id):
                        print("Upload success")
                        resp = api_origin.get_dataset(doi)
                        draft = resp.json()['data']['latestVersion']
                        files = draft['files']

                        for file in files:
                            dataFile = file['dataFile']
                            print(file)
                            print(dataFile)

                            if dataFile['contentType'] == 'text/tab-separated-values':
                                tab_id_new = dataFile['id']
                                tab_file_new = file

                        print(id)
                        print(tab_id_old)
                        print(tab_id_new)

                        update_dataset(id, tab_id_old, tab_id_new)
                        update_file_metadata(tab_id_new, row['File Description'])

                    else:
                        print("Upload failed")
                        continue

                else:
                    continue

                update_citation(latest_version, row, doi)
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
