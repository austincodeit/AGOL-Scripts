#  PPM Updater v 2.0
#  Created by John Clary; Nov 2015

#  records missing X/Y are ignored

import csv
import json
import getpass
import urllib
import urllib2

def update_feature_service(data, service_url, token):
    failList = []
    successList = []
    
    upload = json.dumps(data['features'])
    addUrl = service_url + 'addFeatures'
    addValues = { 'f':'json','features': upload ,'token':token}
    addData = urllib.urlencode(addValues)
    addRequest = urllib2.Request(addUrl, addData)
    addResponse = urllib2.urlopen(addRequest)
    responseData = json.load(addResponse)

    for response in responseData["addResults"]:
        if response["success"] == True:
            successList.append(response["objectId"])
        else:
            failList.append(response["objectId"])
    
    print str(len(successList)), "features added,", str(len(failList)), "features failed to add."
    
    return (data, responseData)
    
def delete_features(service_url, token):

    fsFeatureIds = []
    delList = []
    failList = []
    successList = []

    print "Query service for object ids to delete"
    delUrl = service_url + "deleteFeatures"    
    crUrl = service_url + 'query'
    whereCL= "source='AMANDA'"
    crValues = {'f' : 'json',"where": whereCL , "outFields"  : '*','token' : token, "returnGeometry":False }  #query to fetch all feature data
    crData = urllib.urlencode(crValues)
    crRequest = urllib2.Request(crUrl, crData)
    crResponse = urllib2.urlopen(crRequest)
    crJson = json.load(crResponse)
    featureData = crJson['features']  #al features assigned to var featureData
    
    for feature in featureData:
        delList.append(feature["attributes"]["OBJECTID"])

    print str(len(delList)) + " deletion features found in AGOL service."
    print "Deleting features"
    if len(delList) > 0:
        for objectId in delList:
            delValues = { 'f':'json','objectIDs': objectId,'token':token}
            delData = urllib.urlencode(delValues)
            delRequest = urllib2.Request(delUrl, delData)
            delResponse = urllib2.urlopen(delRequest)
            responseDataD = json.load(delResponse)
            if "deleteResults" in responseDataD.keys():
                successList.append(str(responseDataD["deleteResults"]))
            else:
                failList.append(str(responseDataD["deleteResults"]))
            
    print str(len(successList)), "features deleted,", str(len(failList)), "features failed to delete."

def get_token():
    print "\ngenerate token"
    gtUrl = 'https://www.arcgis.com/sharing/rest/generateToken'
    gtValues = {'username' : username,'password' : password,'referer' : 'http://www.arcgis.com','f' : 'pjson' }
    gtData = urllib.urlencode(gtValues)
    gtRequest = urllib2.Request(gtUrl, gtData)
    gtResponse = urllib2.urlopen(gtRequest)
    gtJson = json.load(gtResponse)
    token = gtJson['token']
    return token

def build_arc_json(data):
    template_file = open("arc_json_template.json", "r")
    raw_json = template_file.read()
    template = json.loads(raw_json)
    objectid = 0
    for record in data:
        feature = {}    
        try:
            feature["geometry"] = {"x":float(data[record]["lon"]),"y":float(data[record]["lat"])}
        except ValueError:
            print "\nWARNING: " + data[record]["address"] + " does not have valid X/Y and will be ignored."
            continue
        objectid += 1
        feature["attributes"] = {}
        feature["attributes"]["OBJECTID"] = objectid
        feature["attributes"]["address"] = data[record]["address"]
        feature["attributes"]["rsns"] = data[record]["rsns"]
        feature["attributes"]["case_count"] = data[record]["case_count"]
        feature["attributes"]["propertyroll"] = data[record]["propertyroll"]
        feature["attributes"]["nov_sent"] = data[record]["nov_sent"]
        feature["attributes"]["cut_date"] = data[record]["cut_date"]
        feature["attributes"]["hs_exempt"] = data[record]["hs_exempt"]
        feature["attributes"]["source"] = data[record]["source"]
        feature["attributes"]["lon"] = data[record]["lon"]
        feature["attributes"]["lat"] = data[record]["lat"]
        template["features"].append(feature)
    template_file.close()
    return template

def get_homestead_status(data, tcad_database):
    record_count = 0
    tcad_dict = {}
    #  create dictionary of geo_ids as key with values as hs status
    with open(tcad_database, "r") as tcad_data:
        tcad_dictReader = csv.DictReader(tcad_data)
        for record in tcad_dictReader:
            geo_id = record["GEO_ID"]
            hs_status = record["HS_EXEMPT"]
            tcad_dict[geo_id] = hs_status
    
    #  iterate through PPM records and lookup hs value from tcad dict
    for record in data:
        record_count += 1
        geo_id = data[record]["propertyroll"]
        if geo_id in tcad_dict:
            data[record]["hs_exempt"] = tcad_dict[geo_id]
    print str(record_count) + " records processed."
    return data
    
def group_ppm_records(ppmInputFile):
    input_data = open(ppmInputFile, "r")
    data = csv.DictReader(open(ppmInputFile))
    addressList = []
    rsnList = []
    grouped_data = {}
    input_record_count = 0
    for record in data:
        input_record_count += 1
        address = record["FOLDERNAME"]
        rsn = record["FOLDERRSN"]
        if address not in addressList:
            addressList.append(address)
            rsnList.append(rsn)
            grouped_data[address] = {}
            grouped_data[address]["address"] = address
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
            if rsn not in rsnList:
                rsnList.append(rsn)
                grouped_data[address]["rsns"] = grouped_data[address]["rsns"] + " " + rsn
                grouped_data[address]["cut_date"] = grouped_data[address]["cut_date"] + " " + record["CUTDATE"]
    
    input_data.close()
    print str(input_record_count) + " records grouped to " + str(len(grouped_data)) + " unique cases."
    return grouped_data

def main(ppmInputFile):
    data = group_ppm_records(ppmInputFile)
    data = get_homestead_status(data, tcad_database)
    data = build_arc_json(data)
    token = get_token()
    delete_features(service_url, token)
    results = update_feature_service(data, service_url, token)
    return results

ppmInputFile = "PA_ROP_List.csv"
tcad_database = "TCAD_Homesteads_2015.csv"
service_url = "http://services.arcgis.com/0L95CJ0VTaxqcmED/arcgis/rest/services/ppm_features/FeatureServer/0/"
username = raw_input("Enter ArcGIS Online username: ")
password = getpass.getpass() #  this should prevent echo when run as a binary file
results = main(ppmInputFile)
