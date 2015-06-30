##Created by John Clary for the City of Austin Code Department
##
##Based on an input CSV this script reads the Amanda file system for new attachments 
##and uploads them to an AGOL feature service
##
#this should really query the feature service right off the bat to figure out which features to add/delete/update
#it would really be a miracle if this workspace
# check to make sure your attachment needs to be uploaded! :)...i.e. merge this with the rest of the script.
# check for successful upload
#update service urls to baseURL + request type
#clean up console printing: record count is confusing. need to capture cases
#no built-in gecoding, so make sure all properties have xy before you run this script
#retreives amanda case attachments and merges them to single pdfs
#assumes that amanda attachment IDs will never be the same as a folder rsn
#requires ms word, win32com, and pyPdf

print "Importing modules..."

import os, shutil, csv, pyPdf, glob, arcpy, datetime, time, urllib, urllib2, json, requests, datetime, sys, getpass
import win32com.client as win32

logfile = (open("logfile.txt", "w"))
ppmROPList = "PA_ROP_List.csv"
cleanPPMdataFile = "cleanPPM.tab"

username = raw_input("Enter ArcGIS Online username: ")
password = getpass.getpass() #this should prevent echo when run as a binary file

#===part 1: read list of PPM properties and create staging folders===#

sourcePathList = []  #a simple list of records by case number and attachment path
destPathList = [] #a list of attachments that will be copied and merged, based on the input csv and what directories already exist
allCaseList = [] #a list of all of the case numbers on the input csv--ie, the PA ROP list
newCaseList = [] #a list of cases and/or attachments that are new, i.e., they do not have directories created

basePath = "\\\\coacd.org\\dfs\\SWS\\Code Enforcement\\CC GIS Operations\\Projects\\PPM\\AMANDA_Attachments"
fsPath = "http://services.arcgis.com/0L95CJ0VTaxqcmED/arcgis/rest/services/ppmFeatures_v11/FeatureServer/0/"

#read case IDs and file paths to memory 
data = csv.DictReader(open(ppmROPList))

for record in data:
    pathPair = []
    pathPair.append(record["FOLDERRSN"])
    pathPair.append(record["DOSPATH"])
    sourcePathList.append(pathPair)

recordCount = str(len(sourcePathList))
count = 0

print "Generating copy list for  " + recordCount + " files to " + basePath

for record in sourcePathList:
    if record[0] not in allCaseList: #append case number to list of unique case numbers, used later to delete old attachments/directories
        allCaseList.append(record[0])
    count = count + 1
    caseID = record[0]
    caseSource = record[1]  #the entire path to the document in the original amanda send folder
    fileName = caseSource.split('\\')[9] #split the path and grab the last value to get filename
    fileName = fileName.replace(".DOC", ".pdf") #change the original filename variable to .pdf, so that we can check for existin pdf docs in the staging folder
    caseDest = basePath + "\\" + caseID
    if not os.path.exists(caseDest): #check for existing case folders and create them if needed
        os.makedirs(caseDest)
        logfile.writelines("Directory " + caseDest + " created.\n")
    if not os.path.isfile(caseDest + "\\" + fileName): #check for existing files and add to copy list if it doesn't exist
        if os.path.isfile(caseDest + "\\" + caseID + ".pdf"): #if a file for this exact document doesn't exist , we check to see if a master pdf for this case already exists
            os.remove(caseDest + "\\" + caseID + ".pdf") #we delete any existing pdf master file because we wil be generating a new one
        destPathList.append([caseSource, caseDest, fileName, caseID]) #append  path and filename and caseid to destination path list
    else:
        logfile.writelines(fileName + " exists and will not be copied.\n")
  
#====part 2: open word docs and save as pdf in new folders====#

recordCount = str(len(destPathList))
count = 0

print "Converting " + recordCount + " files to pdf..."

word = win32.gencache.EnsureDispatch('Word.Application')
word.Visible = False
for wordDoc in destPathList:
    count = count + 1
    in_path = wordDoc[0] #caseSource from above
    out_doc = wordDoc[2] #fileName from above
    out_path = os.path.join(wordDoc[1], out_doc)
    doc = word.Documents.Open(in_path)
    doc.SaveAs(out_path, FileFormat=17) #save as pdf
word.Quit() # releases Word object from memory


#====part 3: merge pdfs====#

#get list of unique case ids
for case in destPathList:
    if case[3] not in newCaseList:
        newCaseList.append(case[3])

print "Merging PDFs for " + str(len(newCaseList)) + " total cases."
count = 0;
for caseID in newCaseList:
    count = count + 1
    currentDir = basePath+ "\\" + caseID
    pdfList = glob.glob(currentDir + "//*.pdf") #get list of pdfs in current directory
    output = pyPdf.PdfFileWriter() #create pdf writer instance
    for item in pdfList:
        pdfDocument = os.path.join(currentDir,item) #point to pdf in directory
        input1 = pyPdf.PdfFileReader(file(pdfDocument, "rb")) #read pdf
        for page in range(input1.getNumPages()): #get page count
            output.addPage(input1.getPage(page))#add to output
    outputStream = file(currentDir + "\\" + caseID + ".pdf", "wb") #outFile name
    output.write(outputStream) #write merged pdf once all outputs have been added
    outputStream.close()

#===part 4: delete folders and attachments if cases are no longer on list===#
folderList = os.listdir(basePath)

for folder in folderList:
	if folder not in allCaseList:
		shutil.rmtree(basePath + "\\" + folder)
		logfile.writelines("Directory >" + folder + "< is not on the PPM list and has been deleted from " + basePath + "\n")



#------------------------------------------------------
# Variables and Lists
#------------------------------------------------------
ppmList = []
uniqueList = []
ppmCount = 0
failCount = 0
#------------------------------------------------------
# Function for  converting xy decimals to integers
#------------------------------------------------------
def num(s, r):
	global failCount
	try:
		return int(float((s)))
	except ValueError:
			logfile.writelines("Attachment for case " + r + " missing XY data.\n")
			failCount += 1
			return 0
#------------------------------------------------------
# Get AMANDA export and remove decimals
#------------------------------------------------------
data = csv.DictReader(open(ppmROPList))

print str(ppmCount) + " attachments found, " + str(failCount/2) + " attachments were missing/invalid XY and will not be mapped."

#create output file
cleanPPMdata = open(cleanPPMdataFile, "w") #this file can cause problems....try changing name here and in the 'data' reference in part 2

#write header
cleanPPMdata.writelines("FOLDERRSN\tFOLDERNAME\tLON\tLAT\tPROPERTYROLL\tNOV_SENT\tDOSPATH\tSOURCE\n")

#IM WORKING HERe!!!!!!!!!!!!!!!!!!!

ppmCount = 0
for record in data: #write data to file
	folderRSN = record["FOLDERRSN"]
	dosPath = record['DOSPATH']
	lon = record['LONGITUDE']
	lat = record['LATITUDE']
	address = record['FOLDERNAME']
	novSent = record['NOV_SENT']
	propertyRoll = record["PROPERTYROLL"]
	
	continueCheck = True
	if folderRSN not in uniqueList: #check for duplicates (because the list has multiple rows for the same case, because each case can have multiple attachments)
		uniqueList.append(folderRSN)
		currentTime = time.time()
		try:
			creationTime = os.path.getctime(basePath + "\\" + folderRSN + "\\" + folderRSN + ".pdf") #get creation date of pdf (if it exists)
			if (creationTime + 86400) < currentTime: #if the attachment pdf is older than 24 hours....
				logfile.writelines(record[0] + ".pdf already exists and does not need to be added to feature service.\n")
				continueCheck = False #then this feature has already been created and it can be excluded from the output
		except:
			continueCheck = True
			continue
		if continueCheck == True:
			ppmCount += 1
			cleanPPMdata.writelines(folderRSN + "\t" + address  + "\t" + lon  + "\t" + lat  + "\t" + propertyRoll  + "\t" + novSent  + "\t" + dosPath  + "\t" + "AMANDA\n")

print str(ppmCount) + " cases totalling " + str(len(ppmList)) + " attachements written to file."

cleanPPMdata.close()

#1: turn this into json data
#2: get list of existing features. anything on the ppm upload list should be deleted from the FC (if it exists) because there is a new file. 
#3. anything in the FC that is not in the unique list needs to be deleted from the FC

#------------------------------------------------------
# CREATE FEATURES
#------------------------------------------------------
print "Creating features..."
arcpy.env.overwriteOutput = True # will overwrite existing files in workspace
workspace = "G:\\Code Enforcement\\CC GIS Operations\\Projects\\PPM\\Scripting\\PPM.gdb"
arcpy.env.workspace = workspace
mxd = arcpy.mapping.MapDocument("G:\\Code Enforcement\\CC GIS Operations\\Projects\\PPM\\Scripting\\PPM.mxd")
df = arcpy.mapping.ListDataFrames(mxd)[0] # assign data frame
spatialReference = arcpy.SpatialReference("G:\\Code Enforcement\\CC GIS Operations\\Projects\\PPM\\Scripting\\WGS 1984.prj")

data = cleanPPMdataFile
outputLayer = "ppmFeatureLayer"
outputFeatureClass = "ppmFeatures"
input_features = outputFeatureClass

xField = "LON" 
yField = "LAT"

# "Creating xy layer..."
arcpy.MakeXYEventLayer_management(data, xField, yField, outputLayer, spatialReference)

# "Exporting XY layer as feature class..."
arcpy.CopyFeatures_management(outputLayer, outputFeatureClass)

#reset workspace outside of gdb for json conversion
workspace = 'G:\\Code Enforcement\\CC GIS Operations\\Projects\\PPM\\Scripting'
arcpy.env.workspace = workspace

# "Exporting features to JSON..."
inFeatures = os.path.join("PPM.gdb","ppmFeatures")
arcpy.MakeFeatureLayer_management(inFeatures, "lyr") 
outFeatures = "ppmFeatures.json"
arcpy.FeaturesToJSON_conversion("lyr", outFeatures)

#------------------------------------------------------
#===update feature service===#
#------------------------------------------------------
print "Updating feature service...."

fsFeatureIds = []
delList = []
addList = []
failList = []
successList = []

### Generate Token ###
gtUrl = 'https://www.arcgis.com/sharing/rest/generateToken'
gtValues = {'username' : username,'password' : password,'referer' : 'http://www.arcgis.com','f' : 'pjson' }
gtData = urllib.urlencode(gtValues)
gtRequest = urllib2.Request(gtUrl, gtData)
gtResponse = urllib2.urlopen(gtRequest)
gtJson = json.load(gtResponse)
token = gtJson['token']

#get query PPM features from AGOL
crUrl = fsPath + 'query'
whereCL= "SOURCE='AMANDA'" #there are CCTRACK features in this class that will have to be manually deleted as time passes
crValues = {'f' : 'json',"where": whereCL , "outFields"  : '*','token' : token, "returnGeometry":False }  #query to fetch all feature data
crData = urllib.urlencode(crValues)
crRequest = urllib2.Request(crUrl, crData)
crResponse = urllib2.urlopen(crRequest)
crJson = json.load(crResponse)
featureData = crJson['features']  #al features assigned to var featureData

rawJson_data = open("ppmFeatures.json", "r") #access json file (output from arcpy script)
json_data = json.load(rawJson_data) #read in json as json

#identify features (by objId and caseId) that will be deleted. First, we find any case number not on the original input csv
for feature in featureData:
	if str(feature['attributes']['FOLDERRSN']) not in allCaseList:
		tempList = []
		tempList.append(feature['attributes']['FOLDERRSN'])
		tempList.append(feature['attributes']['OBJECTID'])
		delList.append(tempList)

#identify features that will be added (will need to delete existing features first). note were not using the newCaseList from above because any case missing xy would have dropped off before creating the json feature layer
for feature in json_data['features']:
	tempList = []
	tempList.append(feature['attributes']['FOLDERRSN'])
	tempList.append(feature['attributes']['OBJECTID'])
	addList.append(tempList)
	
#check existing features for any add feature. any match is added to the delete list
for feature in addList: #for all of our new features
	for record in featureData: #for all of the existing features
		if record['attributes']['FOLDERRSN'] == feature[0]: #if the existing feature has the same folderRSN as the new feature, add it to the delete list
			tempList = []
			tempList.append(record['attributes']['FOLDERRSN'])
			tempList.append(record['attributes']['OBJECTID'])
			delList.append(tempList)

#DELETE FEATURES (delete any feature not in the input CSV, and any feature that needs to be updated
print "Deleting existing features..."
delUrl = fsPath + "deleteFeatures"

objectIds = []
count = 0

for delFeature in delList:
    objectId = delFeature[1]
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

addSuccessList = []
addFailList = []

#add features
upload = json.dumps(json_data['features']) #assign json features as upload data 
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
		logfile.write(str(response["objectId"]) + "\tfailed to add.\n")
		addFailList.append(response["objectId"])
		

print str(len(addSuccessList)), "features added,", str(len(addFailList)), "features failed to add."

print "Uploading attachments..."
# ============================================================================== ##
starttime = time.clock()
successList = []
failList = []
responseList = []

#send the FS query again now that the service has been updated
crData = urllib.urlencode(crValues)
crRequest = urllib2.Request(crUrl, crData)
crResponse = urllib2.urlopen(crRequest)
crJson = json.load(crResponse)
featureData = crJson['features']

featureCount = len(featureData)
count = 0


for feature in  featureData: 
     count = count + 1
     caseId = feature['attributes']['FOLDERRSN']
     oid = feature['attributes']['OBJECTID']
     file_path = basePath + "\\" + str(caseId) + "\\" + str(caseId) + ".pdf"
     test = os.path.isfile(file_path)
     if test == True:
        fileSize = os.path.getsize(file_path)
        print "Uploading file #" + str(count) + " of " + str(featureCount) + ": FOLDERRSN: " + str(caseId) + " size: " + str(fileSize/1000000) + "mb"
        if (fileSize/1000000) > 20:
            print "WARNING: Folder " + str(caseId) + " is larger than 20mb and will not be attached" # the app still upload file, but the attempt wil fail
        attachUrl = fsPath + "%s/addAttachment" %oid 
        files = {'attachment': (os.path.basename(file_path), open(file_path, 'rb'), 'application/pdf')}
        params = { "token": token, "f": "pjson"}
        r = requests.post(attachUrl, params, files=files)
        response = json.loads(r.text)
        if 'error' in response:
            logfile.write(str(oid) + " failed to add. with message: " + str(response['error']['details']) + "\n")
            print "\t!!! FAILURE !!!\tcheck logfile."
     else:
        print file_path, " is not a directory"

endtime= time.clock()
elapsedtime = endtime - starttime
logfile.writelines(str(elapsedtime/60) + '  minutes\n')
logfile.close()

print 'Script complete.'
