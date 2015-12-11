#  delete_all_features.py
#  deletes all features from the ArcGIS Online feature service you rpvide
#  created by John Clary for the Austin Code Department, Nov 2015

import json
import requests
import getpass
import urllib
import urllib2

fsFeatureIds = []
delList = []
addList = []
failList = []
successList = []
addSuccessList = []
addFailList = []

answer = ""
while answer != "yes":
        answer = raw_input("This will delete all features in the servivce - type 'yes' to continue.")
                   
username = raw_input("Enter ArcGIS Online username: ")
password = getpass.getpass() #this should prevent echo when run as a binary file

fsPath = "http://services.arcgis.com/YOUR_FEATURE_SERVICE_NAME/0/" 

delUrl = fsPath + "deleteFeatures"

print "generate token"

#  generate token
gtUrl = 'https://www.arcgis.com/sharing/rest/generateToken'
gtValues = {'username' : username,'password' : password,'referer' : 'http://www.arcgis.com','f' : 'pjson' }
gtData = urllib.urlencode(gtValues)
gtRequest = urllib2.Request(gtUrl, gtData)
gtResponse = urllib2.urlopen(gtRequest)
gtJson = json.load(gtResponse)
token = gtJson['token']

print "query service for object ids to delete"

#  query service 
crUrl = fsPath + 'query'
whereCL= "OBJECTID>0"
crValues = {'f' : 'json',"where": whereCL , "outFields"  : '*','token' : token, "returnGeometry":False }  #query to fetch all feature data
crData = urllib.urlencode(crValues)
crRequest = urllib2.Request(crUrl, crData)
crResponse = urllib2.urlopen(crRequest)
crJson = json.load(crResponse)
featureData = crJson['features']

print "delete features"

#  delete features
for feature in featureData:
	delList.append(feature["attributes"]["OBJECTID"]) 

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

print 'Script complete.'
