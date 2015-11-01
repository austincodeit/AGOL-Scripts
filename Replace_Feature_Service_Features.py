import json
import requests
import getpass
import urllib
import urllib2


print "Updating feature service...."

fsFeatureIds = []
delList = []
addList = []
failList = []
successList = []
addSuccessList = []
addFailList = []

username = raw_input("Enter ArcGIS Online username: ")
password = getpass.getpass() #this should prevent echo when run as a binary file
fsPath = "http://YOUR_SERVICE_HERE/0/"
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

print "load data and add new features"
new_data = open("new_data.json", "r") #access json file (output from arcpy script)
new_json_data = json.load(new_data) #read in json as json

#add features
upload = json.dumps(new_json_data['features']) #assign json features as upload data 
addUrl = fsPath + 'addFeatures'
addValues = { 'f':'json','features': upload ,'token':token}
addData = urllib.urlencode(addValues)
addRequest = urllib2.Request(addUrl, addData)
addResponse = urllib2.urlopen(addRequest)
responseData = json.load(addResponse)

for response in responseData["addResults"]:
	if response["success"] == True:
		addSuccessList.append(response["objectId"])
	else:
		addFailList.append(response["objectId"])
		

print str(len(addSuccessList)), "features added,", str(len(addFailList)), "features failed to add."

print 'Script complete.'

new_data.close()
