#Created by John Clary for the City of Austin Code Department
#Largely borrowed from stackoverflow, github, and a world full of generous and helpful developers
#also, John Schulz, Austin Water Utility
#
# reads AGOL feature service and creates an ok report.
#

import os, urllib, urllib2, datetime, json, time, csv

 #file-name friendly time string
currentTime = time.strftime('%d%b%Y_%Hh%Mm')

#skeleton for master dictionary
masterDict = {"RESPONDING":{},"STATUS":{}, "INCIDENT_TYPE":{}, "ACTION":{}}

#function to add unique dictionary keys for domain codes 
def checkForKeys(theKey, theValue):
	if theValue not in masterDict[theKey]: #if feature value is not a key for that reporting item. e.g., if STATUS code '1' already exists amongst the 'STATUS' keys
		masterDict[theKey][theValue] = dict.fromkeys(timeIntervalNames) #create a dict key for that feature value, and the value for that featureValue key is a dict of time intervals

#function to lookup domain code names
def returnDomainCodeName(theKey, theCode):
	for item in domainDict[theKey]:
		if item["code"] == theCode:
			return item["name"]

#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
#$$$$$$$$ GENERATE TOKEN $$$$$$$$$$$$$$$$$$
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

print "Generating token...\n"
# Generate Token #   You will need a token for REST ENDPOINT request fill in your username and password -- it will need to be an amdmin level account.
gtUrl = 'https://www.arcgis.com/sharing/rest/generateToken'
gtValues = {'username' : [REDACTED], 'password' : [REDACTED], 'referer' : 'http://www.arcgis.com', 'f' : 'pjson' }
gtData = urllib.urlencode(gtValues)
gtRequest = urllib2.Request(gtUrl, gtData)
gtResponse = urllib2.urlopen(gtRequest)
gtJson = json.load(gtResponse)
token = gtJson['token']

#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
#$$$$$$$$ DOWNLOAD FEATURES $$$$$$$$$$$$$$
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

print "Downloading features...\n"
# create replica
crUrl = 'http://services.arcgis.com/0L95CJ0VTaxqcmED/arcgis/rest/services/SX15_DispatchTracking/FeatureServer/createReplica'


crValues = { 'f':'json','replicaName': 'Export_' + currentTime,'transportType': 'esriTransportTypeEmbedded','layers' : 0,'token':token}
crData = urllib.urlencode(crValues)
crRequest = urllib2.Request(crUrl, crData)
crResponse = urllib2.urlopen(crRequest) #pull all features in layer id 0
responseData = json.load(crResponse) #load replica into memory as json
replicaID = responseData["replicaID"]
replicaName = responseData["replicaName"]

#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
#$$$$$$$$ REMOVE REPLICA $$$$$$$$$$$$$$$$$$
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

print "Removing replica....\n"

#unregister the replica--this is important to reduce cloud storage!
repUrl = 'http://services.arcgis.com/0L95CJ0VTaxqcmED/arcgis/rest/services/SX15_DispatchTracking/FeatureServer/unRegisterReplica'
repValues = {'f': 'json','replicaID': replicaID,'token':token}
repData = urllib.urlencode(repValues)
repRequest = urllib2.Request(repUrl,repData)
repResponse = urllib2.urlopen(repRequest)
repResponse = json.load(repResponse)

#alert if ungregister attempt fails
if repResponse["success"] != True:
        print "Warning: Replica not unregistered."

#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
#$$$$$$$$ FETCH DOMAIN DATA $$$$$$$$$$$$$$$
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

fldUrl = 'http://services.arcgis.com/0L95CJ0VTaxqcmED/arcgis/rest/services/SX15_DispatchTracking/FeatureServer/0'
fldValues = { 'f':'json','layers' : 0,'token':token}
fldData = urllib.urlencode(fldValues)
fldRequest = urllib2.Request(fldUrl, fldData)
fldResponse = urllib2.urlopen(fldRequest) #download layer info
fldData = json.load(fldResponse) #assign layer data to variable 
fldData = fldData["fields"] #grab only field data

#skeleton for domain data
domainDict = {}

for field in fldData: #for every field in the service layer
	for reportKey in masterDict: #for every attribute we're measuring
		if field["name"] == reportKey: #if the field matches the attribute of concern
			domainDict[reportKey] = field["domain"]["codedValues"] #copy the domain data to the domainDict

#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
#$$$$$$$$ TABLUATE INCIDENTS $$$$$$$$$$$$$$$
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

print "Generating report...\n"

# time interval variables
oneAgo = (datetime.datetime.now() - datetime.timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
fiveAgo = (datetime.datetime.now() - datetime.timedelta(hours=5)).strftime('%Y-%m-%d %H:%M:%S')
eightAgo = (datetime.datetime.now() - datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
twelveAgo = (datetime.datetime.now() - datetime.timedelta(hours=12)).strftime('%Y-%m-%d %H:%M:%S')
dayAgo = (datetime.datetime.now() - datetime.timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
allTime = (datetime.datetime.now() - datetime.timedelta(hours=1000000)).strftime('%Y-%m-%d %H:%M:%S') 

timeIntervals = [oneAgo, fiveAgo, eightAgo, twelveAgo, dayAgo, allTime] #the interval values
timeIntervalNames = ["< 1hr","< 5hr","< 8hr","< 12hr","< 24hr","All Time"] #the interval names
timeDict = dict(zip(timeIntervalNames, timeIntervals)) #associate interval values with interval names
timeList = [] #used only for counting total # of incidents within a time interval

#for counting total# of incidents
oneCount = 0
fiveCount = 0
eightCount = 0
twelveCount = 0
dayCount = 0

#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
#$$$$ COMPILE FEATURE TO MASTER DICTIONARY $$$$$
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

#Create master dictionary organized by attribute and broken into time intervals
for feature in responseData["layers"][0]["features"]: #for every feature in the response data
	#get uinque values and build dictionary
	for reportKey in masterDict: #for every attribute (report key) we're concerned with
		featureValue = feature["attributes"][reportKey] #get the value from the data for the attribute that matches the report key
		checkForKeys(reportKey, featureValue) #check the values for each report code and add to master dictionary if unique
	# convert timestamp
	creationTime = feature["attributes"]["CREATED_DATE"] # 
	creationTime = str(creationTime) #convert time to string
	creationTime = datetime.datetime.fromtimestamp(int(creationTime)/1000).strftime('%Y-%m-%d %H:%M:%S') #convert from unix
	timeList.append(creationTime) #for counting total # of incidents
	# add values to dictionary based on timestamp
	for reportKey in masterDict: #for every attribute (report key) we're concerned with
		featureValue = feature["attributes"][reportKey] #get the value from the data for the attribute that matches the report key
		for intervalName, timeInterval in timeDict.iteritems(): #for every time interval in our time dictionary
			if creationTime > timeInterval: #if the edit date is more recent than the interval time
				if masterDict[reportKey][featureValue][intervalName] != None: #if the feature value is not none
					masterDict[reportKey][featureValue][intervalName] += 1 #add one to that value for that interval
				else:
					masterDict[reportKey][featureValue][intervalName] = 1 #the first value for that interval = 1

for creationTime in timeList:
	if creationTime > oneAgo:
		oneCount += 1
	if creationTime > fiveAgo:
			fiveCount += 1
	if creationTime > eightAgo:
			eightCount += 1
	if creationTime > twelveAgo:
			twelveCount += 1
	if creationTime > dayAgo:
			dayCount += 1

#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
#$$$$ WRITE REPORT $$$$$$$$$$$$$$$$$$$$$$$$$$$$$
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

outReport = open("SXSW2015_Report_"+ currentTime + ".csv", "w")
outReport.write("SXSW 2015 Incident Report\n")
outReport.write("Incident Summary as of ")
outReport.write(time.strftime('%d %b %Y %I:%M %p') + " CDT\n\n")

outReport.write("Total Incidents:," + str(len(timeList)) + "\n")
outReport.write("Incidents created in past hour:," + str(oneCount) + "\n")
outReport.write("Incidents created in past 5 hours:," + str(fiveCount) + "\n")
outReport.write("Incidents created in past 8 hours:," + str(eightCount) + "\n")
outReport.write("Incidents created in past 12 hours:," + str(twelveCount) + "\n")
outReport.write("Incidents created in past 24 hours:," + str(dayCount) + "\n\n")

outReport.write("-- Incident Details --\n")
#write incident details
for reportKey in masterDict: #for every report attribute
	outReport.write("***" + reportKey + "***") #write the attribute name
	outReport.write(",")
	for interval in timeIntervalNames: #write the time intervals
		outReport.write(interval)
		outReport.write(",")
	outReport.write("\n") #end header
	for domainValue in masterDict[reportKey]: #for every attribute code value
		domainCodeName = returnDomainCodeName(reportKey, domainValue) #fetch attribute value name from domain dictionary
		outReport.write(str(domainCodeName)) #write the attribute value name
		outReport.write(",")
		position = 1
		for interval in timeIntervalNames: #write the corresponding total for each interval
			if masterDict[reportKey][domainValue][interval] == None:
				outReport.write("0")
			else:
				outReport.write(str(masterDict[reportKey][domainValue][interval]))
			if position < len(timeIntervalNames):
				outReport.write(",")
			if position == len(timeIntervalNames):
				outReport.write("\n")
			position = position + 1
	outReport.write("\n")

outReport.close()

print "Script complete!"
