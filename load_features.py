import json
import getpass
import urllib
import urllib2

print "Updating feature service...."

addList = []
successList = []
failList = []

username = raw_input("Enter ArcGIS Online username: ")
password = getpass.getpass() #this should prevent echo when run as a binary file

#  dev
#  fsPath = "http://services.arcgis.com/yourDevFeatureService/FeatureServer/0/"

#  prod - !
fsPath = "http://services.arcgis.com/yourProdFeatureService/FeatureServer/0/"

print "generate token"

#  generate token
gtUrl = 'https://www.arcgis.com/sharing/rest/generateToken'
gtValues = {'username' : username,'password' : password,'referer' : 'http://www.arcgis.com','f' : 'pjson' }
gtData = urllib.urlencode(gtValues)
gtRequest = urllib2.Request(gtUrl, gtData)
gtResponse = urllib2.urlopen(gtRequest)
gtJson = json.load(gtResponse)
token = gtJson['token']

print "add new features"
new_data = open("new_data.json", "r") #access json file
new_json_data = json.load(new_data)

#add features
upload = json.dumps(new_json_data['features'])
addUrl = fsPath + 'addFeatures'
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

print 'Script complete.'

new_data.close()
