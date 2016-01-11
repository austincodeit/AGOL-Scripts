#  PPM Updater v2.05

#  Created by John Clary; Nov 2015

import csv
import json
import getpass
import urllib
import urllib2
from datetime import datetime
import pdb

ppmInputFile = "ppm_list.csv"
tcad_database = "source_files/TCAD_Homesteads_2015.csv"
source_template = "source_files/arc_json_template.json"
service_url = "http://services.arcgis.com/0L95CJ0VTaxqcmED/ArcGIS/rest/services/ppm_services/FeatureServer/0/"
username = raw_input("Enter ArcGIS Online username: ")
password = getpass.getpass() #  this should prevent echo when run as a binary file

def add_features(data, service_url, token):

    fail_list = []
    success_list = []
    
    if len(data) == 0:
        print str(len(success_list)), "features added,", str(len(fail_list)), "features failed to add."
        return "None"

    upload = json.dumps(data['features'])
    addUrl = service_url + 'addFeatures'
    addValues = { 'f':'json','features': upload ,'token':token}
    addData = urllib.urlencode(addValues)
    addRequest = urllib2.Request(addUrl, addData)
    addResponse = urllib2.urlopen(addRequest)
    responseData = json.load(addResponse)

    for response in responseData["addResults"]:
        if response["success"] == True:
            success_list.append(response["objectId"])
        else:
            fail_list.append(response["objectId"])
    
    print str(len(success_list)), "features added,", str(len(fail_list)), "features failed to add."
    
    return (responseData)
    
def update_features(data, service_url, token):
    
    fail_list = []
    success_list = []
    
    if len(data) == 0:
        print str(len(success_list)), "features updated,", str(len(fail_list)), "features failed to update."
        return "None"
    
    fail_list = []
    success_list = []
    
    upload = json.dumps(data)
    updateUrl = service_url + 'updateFeatures'
    updateValues = { 'f':'json','features': upload ,'token':token}
    updateData = urllib.urlencode(updateValues)
    updateRequest = urllib2.Request(updateUrl, updateData)
    updateResponse = urllib2.urlopen(updateRequest)
    responseData = json.load(updateResponse)

    for response in responseData["updateResults"]:
        if response["success"] == True:
            success_list.append(response["objectId"])
        else:
            fail_list.append(response["objectId"])
    
    print str(len(success_list)), "features updated,", str(len(fail_list)), "features failed to update."

def build_arc_json(data, source_template):
    template_file = open(source_template, "r")
    raw_json = template_file.read()
    template = json.loads(raw_json)
    objectid = 0
    for record in data:
        feature = {}    
        try:
            feature["geometry"] = {"x":float(record["lon"]),"y":float(record["lat"])}
        except ValueError:
            print "\nWARNING: " + record["address"] + " does not have valid X/Y and will be ignored."
            continue
        objectid += 1
        feature["attributes"] = {}
        feature["attributes"]["status"] = "ACTIVE PPM"
        feature["attributes"]["address"] = record["address"]
        feature["attributes"]["street_name"] = record["street_name"]
        feature["attributes"]["master_rsn"] = record["master_rsn"]
        feature["attributes"]["rsns"] = record["rsns"]
        feature["attributes"]["case_count"] = record["case_count"]
        feature["attributes"]["propertyroll"] = record["propertyroll"]
        feature["attributes"]["nov_sent"] = record["nov_sent"]
        feature["attributes"]["cut_date"] = record["cut_date"]
        feature["attributes"]["hs_exempt"] = record["hs_exempt"]
        feature["attributes"]["source"] = record["source"]
        feature["attributes"]["lon"] = record["lon"]
        feature["attributes"]["lat"] = record["lat"]
        template["features"].append(feature)
    template_file.close()

    #  pdb.set_trace()
    return template

def create_update_dict(data, service_data):
    
    print "Create update dictionary."
    
    update_dict = {"add": [] , "update": [] }
    service_rsns = []
    input_rsns = []
    
    for record in data:
        input_rsns.append(data[record]['master_rsn'])

    for feature in service_data:
        service_rsns.append(feature['attributes']['master_rsn'])
        
        if feature['attributes']['status'] == "CLOSED PPM":
            continue #  Closed PPM features will never be updated, deleted, or reopened.
        
        if feature['attributes']['master_rsn'] not in input_rsns:
            feature['attributes']['status'] = "CLOSED PPM"
            update_dict["update"].append(feature)
            
    for record in data:
        if data[record]['master_rsn'] not in service_rsns:
            data[record]['status'] = "ACTIVE PPM"
            update_dict["add"].append(data[record])

    #  pdb.set_trace()

    return update_dict

def query_features(service_url, token):
  
    print "Get feature service data."
    crUrl = service_url + 'query'
    whereCL= "OBJECTID > 0"
    crValues = {'f' : 'json',"where": whereCL , "outFields"  : '*','token' : token, "returnGeometry":True }  #  query to fetch all feature data
    crData = urllib.urlencode(crValues)
    crRequest = urllib2.Request(crUrl, crData)
    crResponse = urllib2.urlopen(crRequest)
    crJson = json.load(crResponse)
    return crJson['features']

def get_token():
    print "Generate token."
    gtUrl = 'https://www.arcgis.com/sharing/rest/generateToken'
    gtValues = {'username' : username,'password' : password,'referer' : 'http://www.arcgis.com','f' : 'pjson' }
    gtData = urllib.urlencode(gtValues)
    gtRequest = urllib2.Request(gtUrl, gtData)
    gtResponse = urllib2.urlopen(gtRequest)
    gtJson = json.load(gtResponse)
    token = gtJson['token']
    return token


def get_homestead_status(data, tcad_database):
    record_count = 0
    tcad_dict = {}
    #  create dictionary of geo_ids as key with values as hs status
    with open(tcad_database, "r") as tcad_data:
        tcad_dictReader = csv.DictReader(tcad_data)
        for record in tcad_dictReader:
            geo_id = record["GEO_ID"]
            hs_status = record["HS_EXEMPT"]
            if hs_status == 'F':
                hs_status = 'Not Exempt'
            if hs_status == 'T':
                hs_status = 'Exempt'
            tcad_dict[geo_id] = hs_status
    
    #  iterate through PPM records and lookup hs value from tcad dict
    for record in data:
        record_count += 1
        geo_id = data[record]["propertyroll"]
        if geo_id in tcad_dict:
            data[record]["hs_exempt"] = tcad_dict[geo_id]
    return data
    
def group_ppm_records(ppmInputFile):
    input_data = open(ppmInputFile, "r")
    data = csv.DictReader(open(ppmInputFile))
    input_data.close()
    
    addressList = []
    rsn_list = []
    grouped_data = {}
    input_record_count = 0
    
    for record in data:
        input_record_count += 1
        address = record["FOLDERNAME"]
        rsn = record["FOLDERRSN"]
        rsn_list.append(rsn)
        if address not in addressList:
            addressList.append(address)
            grouped_data[address] = {} #  records are grouped by address; and the master RSN will become the basis for retiring cases as 12-month window closes
            grouped_data[address]["master_rsn"] = { datetime.strptime(record["NOV_SENT"], '%m/%d/%Y') : rsn } #  convert date and set as dict key for rsn 
            grouped_data[address]["address"] = address
            grouped_data[address]["street_name"] = record["PROPSTREET"]
            grouped_data[address]["rsns"] = rsn
            grouped_data[address]["case_count"] = 1
            grouped_data[address]["lon"] = record["LONGITUDE"]
            grouped_data[address]["lat"] = record["LATITUDE"]
            grouped_data[address]["propertyroll"] = record["PROPERTYROLL"]
            grouped_data[address]["nov_sent"] = record["NOV_SENT"]
            grouped_data[address]["cut_date"] = record["CUTDATE"]
            grouped_data[address]["hs_exempt"] = "unknown"
            grouped_data[address]["source"] = "AMANDA"
        
        else:
            
            grouped_data[address]["case_count"] += 1
            
            if rsn not in rsn_list:
                rsn_list.append(rsn)
                grouped_data[address]["rsns"] = grouped_data[address]["rsns"] + " " + rsn
                
            grouped_data[address]["master_rsn"][datetime.strptime(record["NOV_SENT"], '%m/%d/%Y')] = rsn #  at this point, master_rsn becomes a dict of nov dates with rsns
            grouped_data[address]["cut_date"] = grouped_data[address]["cut_date"] + " " + record["CUTDATE"]
            grouped_data[address]["nov_sent"] = grouped_data[address]["nov_sent"] + " " + record["NOV_SENT"]

    for record in grouped_data: #  identify the newest nov date set at the address and use that folder as the master rsn
        nov_dates = []
        for key in grouped_data[record]["master_rsn"]:
            nov_dates.append(key)

        grouped_data[record]["master_rsn"] = grouped_data[record]["master_rsn"][max(nov_dates)]
    
    print str(input_record_count) + " records grouped to " + str(len(grouped_data)) + " unique cases."
    return grouped_data

def main(ppmInputFile):
    data = group_ppm_records(ppmInputFile)
    data = get_homestead_status(data, tcad_database)
    token = get_token()
    service_data = query_features(service_url, token)
    update_dict = create_update_dict(data, service_data)
    update_features(update_dict["update"], service_url, token)
    add_data = build_arc_json(update_dict["add"], source_template)
    results = add_features(add_data, service_url, token)
    return results

results = main(ppmInputFile)

