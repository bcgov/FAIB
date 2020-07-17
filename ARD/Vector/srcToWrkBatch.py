#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      imcdouga
#
# Created:     03/09/2019
# Copyright:   (c) imcdouga 2019
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import sys, string, os, arcpy, logging, xlrd, string, gc
arcpy.env.overwriteOutput = True

def main():
    logFileName = "T:/srcToWrk.log"
    logFile = file(logFileName, "w")
    managementUnitGDB  = "PUT_PATH_HERE\\yourGdbName.gdb"
    year  = "2020"
    inDict = "PUT_DICTIONARY_PATH_HERE\\dataDictionary_AR2020.xlsx"
    tab = "vri2wrk"
    tsas = ["ALL_BC"]

    arcpy.env.overwriteOutput = True

    worksheet = openExcel(inDict,tab)
    print str(worksheet.nrows)
    nRows = worksheet.nrows

    for tsa in tsas:
        rootTSAgdbSrc = managementUnitGDB + "\\src"
        rootTSAgdbWrk = managementUnitGDB + "\\wrk"
        tsa_number = string.replace(tsa,"tsa","")

        managementUnitGDBtemp = "T:\\temp_ard_gdb_src_to_wrk.gdb"
        managementUnitGDBtempSrc = managementUnitGDBtemp + "\\src"
        managementUnitGDBtempWrk = managementUnitGDBtemp + "\\wrk"
        arcpy.Copy_management(managementUnitGDB, managementUnitGDBtemp)
        fieldMapping = ''
        row = 1
        for line in range(nRows -1):
            fieldMapCompl = False
            col = 1
            # next row
            srcFeatureClass = worksheet.cell_value(row,col); col=col+1
            print srcFeatureClass
            srcFieldName = worksheet.cell_value(row,col); col=col+1
            print srcFieldName
            wrkFeatureClass = worksheet.cell_value(row,col); col=col+1
            print wrkFeatureClass
            wrkFieldName = worksheet.cell_value(row,col); col=col+1
            print wrkFieldName
            wrkShortName = worksheet.cell_value(row,col); col=col+1
            print wrkShortName
            IsNullable = bool(worksheet.cell_value(row,col)); col=col+1
            print IsNullable
            Required = bool(worksheet.cell_value(row,col)); col=col+1
            print Required
            Editable = bool(worksheet.cell_value(row,col)); col=col+1
            print Editable
            Length = worksheet.cell_value(row,col); col=col+1
            print Length
            Type = worksheet.cell_value(row,col); col=col+1
            print Type
            Precision = worksheet.cell_value(row,col); col=col+1
            print Precision
            Scale = worksheet.cell_value(row,col)
            print Scale
            fieldMapping = setfieldMapping(fieldMapping,managementUnitGDBtempSrc,srcFeatureClass,wrkShortName,IsNullable,Required,Editable,Length,Type,Precision,Scale, srcFieldName)
            if row + 1 < nRows:
                print "row number" + str(row + 1) + "  vs  total row number " + str(nRows)
                if worksheet.cell_value(row + 1,1) != srcFeatureClass:
                    fieldMapCompl = True
            elif row + 1 == nRows:
                fieldMapCompl = True
            if fieldMapCompl:
                inFC = managementUnitGDBtempSrc+ "\\" + srcFeatureClass
                tempFC = managementUnitGDBtempWrk+ "\\tempFC"
                tempFCname ="tempFC"
                wrkOutName = managementUnitGDBtempWrk + "\\" + wrkFeatureClass
                fid = wrkFeatureClass + "_fid"
                topoName = "wrk_%s_topology" % (wrkFeatureClass)
                fullTopoName = managementUnitGDBtempWrk + "\\" + topoName

                if arcpy.Exists(wrkOutName):
                    arcpy.Delete_management(fullTopoName)
                    arcpy.Delete_management(wrkOutName)



                print "creating temporary feature class with field mapping "
                try:
                    arcpy.FeatureClassToFeatureClass_conversion(inFC, managementUnitGDBtempWrk, tempFCname,"", fieldMapping)
                except:
                    print " FAILED creating temporary feature class with field mapping"
                    logging.warning(srcFeatureClass + " " + tsa_number + " failed to create temporary dataset with field mapping")

                print "Converting multipart to single part (%s)..." % (tempFC)
                try:
                    arcpy.MultipartToSinglepart_management (tempFC, wrkOutName)

                except:
                    print srcFeatureClass + " " + tsa_number + " FAILED mulitpart to single part"
                    logging.error(srcFeatureClass + " " + tsa_number + " FAILED mulitpart to single part")
                    e = sys.exc_info()[1]
                    print(e.args[0])



                try:
                    arcpy.AddMessage("Adding %s..." % (fid))
                    arcpy.AddField_management(wrkOutName, fid, "LONG")
                    arcpy.CalculateField_management(wrkOutName, fid, "!OBJECTID!","PYTHON_9.3")
                except:
                    print srcFeatureClass + " " + tsa_number + " FAILED to add fid"
                    logging.warning(srcFeatureClass + " " + tsa_number + " FAILED to add fid")

                print "Creating %s..." % (topoName)
                try:
    ##                arcpy.env.workspace = managementUnitGDBtempWrk
                    arcpy.CreateTopology_management(managementUnitGDBtempWrk,  topoName)
                    arcpy.AddFeatureClassToTopology_management(fullTopoName,wrkOutName)
                    arcpy.AddRuleToTopology_management(fullTopoName,"Must Not Overlap (Area)",wrkOutName)
                    arcpy.ValidateTopology_management(fullTopoName)
                except:
                    print srcFeatureClass + " " + tsa_number + " FAILED topology"
                    logging.warning(srcFeatureClass + " " + tsa_number + " FAILED topology")

                print "Deleting Temp FC"
                arcpy.Delete_management(tempFC)
                print "Elapsed time: %d seconds" % (time.clock())
                row = row + 1
                print fieldMapping
                fieldMapping = ''
                gc.collect()
            else:
                row = row + 1

##            if row == 12:
##                break
        try:
            arcpy.Copy_management(managementUnitGDBtemp, managementUnitGDB)
        except:
            print  tsa_number + " FAILED Copy from T:\ drive to Archive drive"
            logging.error(tsa_number + " FAILED Copy from T:\ drive to Archive drive")
            e = sys.exc_info()[1]
            print(e.args[0])
            sys.exit()
        gc.collect()

    print "all done"

def createTmpConnection(work, tempConnect):

# -------------------------------------------------------------
  # connection parameters
  usr = "imcdouga"               # oracle user name
  pw = "supMego8612"            # oracle password (enter correct password for user before running
  # pw = getpass.getpass()
  database_platform = "ORACLE"
  instance = "bcgw.bcgov/idwprod1.bcgov"
  authentication = "DATABASE_AUTH"

  # create a temporary connection file
  print work + os.sep + tempConnect
  if arcpy.Exists(work + tempConnect + ".sde"):
    arcpy.AddMessage("Temp BCGW connection already exists: ignore create")
  else:
    print usr, pw, database_platform, instance, authentication
    arcpy.AddMessage("Creating connection...")
    arcpy.CreateDatabaseConnection_management (  # revised connection method 2017
      work,               # folder to create the connection
      tempConnect,        # name of connection
      database_platform,  # database_platform (Oracle)
      instance,           # instance
      authentication,     # authentication
      usr,                # username
      pw                  # password
      )



# --------------------------------------------------------------------------------
# add to field mapping variable
# --------------------------------------------------------------------------------
def setfieldMapping(fieldMapping,workspaceSrc,srcFeatureClass,wrkShortName,IsNullable,Editable,Required,Length,Type,Precision,Scale,srcFieldName):

  src = string.replace(workspaceSrc,"\\","\\\\")+"\\\\"+srcFeatureClass

  if fieldMapping:
    fieldMapping = '%s;%s' % (fieldMapping,wrkShortName)
  else:
    fieldMapping = '%s' % (wrkShortName)
  fieldMapping = '%s %s' % (fieldMapping,wrkShortName)
  fieldMapping = '%s %s' % (fieldMapping,IsNullable)
  fieldMapping = '%s %s' % (fieldMapping,Editable)
  fieldMapping = '%s %s' % (fieldMapping,Required)
  fieldMapping = '%s %d' % (fieldMapping,Length)
  fieldMapping = '%s %s' % (fieldMapping,Type)
  fieldMapping = '%s %d' % (fieldMapping,Precision)
  fieldMapping = '%s %d' % (fieldMapping,Scale)
  fieldMapping = '%s ,First,#,%s,%s,-1,-1' % (fieldMapping,src,srcFieldName)

  return fieldMapping

def openExcel(dataDictionary, worksheetName):
    # validate
    if not os.path.isfile(dataDictionary):
      print "Data dictionary '" + dataDictionary + "' not found."
      logging.warning("Data dictionary '" + dataDictionary + "' not found.")
      sys.exit(1)

    # --------------------------------------------------------------------------------
    # Open the database spreadsheet
    # --------------------------------------------------------------------------------
    ##xl.Visible = 0   # set to 1 to make the process visible
    workbook = xlrd.open_workbook(dataDictionary)
    try:
      worksheet = workbook.sheet_by_name(worksheetName)
    except:
      print "ERROR: Worksheet %s not found in %s." % (worksheetName,dataDictionary)
      logging.warning("ERROR: Worksheet %s not found in %s." % (worksheetName,dataDictionary))
      sys.exit(1)
    return worksheet

# ----------------------------------------------------------------------------
def getProjectParameters(parameterFileName, parameters, parametersNeeded):

  # check if parameter file exists
  if not os.path.isfile(parameterFileName):
    print "  Project parameter file '"+parameterFileName+"' not found in current directory"
    sys.exit()

  # get the parameters
  parameterFile = open(parameterFileName,"r")
  parameterRecord = parameterFile.readline()
  while parameterRecord:

    # parse parameter record
    parameterRecord = parameterRecord.replace("\n","")
    parameterRecord = parameterRecord.replace(" ","")

    # set parameter
    parameter = parameterRecord.split("=")[0]
    value = parameterRecord.split("=")[1]
    parameters[parameter] = value

    # get next record
    parameterRecord = parameterFile.readline()

  missingParameters = {}
  for key in parametersNeeded:
    if not parameters.has_key(key):
      missingParameters[key] = 0
  if len(missingParameters.keys()) > 0:
    print "Error: parameter(s) not found in %s" % (parameterFileName)
    for key in sorted(missingParameters.keys()):
      print "  %-30s  %s" % (key, parametersNeeded[key])
    sys.exit()


def fileListToArray(inArray, inFile):
    inFile =  open( inFile, "r")
    for line in inFile:
        if not line.strip():
            break
        dataset = line.strip()
        inArray.append(dataset)
    inFile.close()


if __name__ == '__main__':
    main()
