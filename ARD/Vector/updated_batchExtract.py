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
import arcpy, os
arcpy.env.overwriteOutput = True

def main():
    tsaNums = sys.argv[1]
    root = sys.argv[2]
    year = sys.argv[3]
    datasets = sys.argv[4]
    overwrite = sys.argv[5]

    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    print dname
    os.chdir(dname)

    dsLst = []
    tsaLst =[]
    fileListToArray(dsLst, datasets)
    fileListToArray(tsaLst,tsaNums)

    databaseConnection = "tempConnectARD"
    logFileName = "T:/extractFromBCGW.log"
    logFile = file(logFileName, "w")

    # Create temp connection
    createTmpConnection("T:\\", databaseConnection)


    scratchGDB = "tmp_extractFromBCGW_ARD.gdb"
    if not arcpy.Exists("t:\\" + scratchGDB):
        arcpy.CreateFileGDB_management("T:\\", scratchGDB)

    for dataset in dsLst:
        print "dataset " + dataset
        inFC = "T:\\"+ databaseConnection +".sde\\" + dataset
        scratchFC = "T:"+"\\"+scratchGDB+"\\tempFC"
        scratchFClyr = "scratchFClyr"
        arcpy.CopyFeatures_management(inFC,scratchFC)
        arcpy.MakeFeatureLayer_management(scratchFC, scratchFClyr)

        for tsa in tsaLst:
            print "tsa number " + tsa
            managementUnitBoundary = root  + "\\" + tsa + "\\" + tsa + "_" + year + ".gdb" + "\\wrk\\bnd"
            workspaceWrk =  root  + "\\" + tsa + "\\" + tsa + "_" + year + ".gdb" + "\\wrk"
            workspaceSrc =  root  + "\\" + tsa + "\\" + tsa + "_" + year + ".gdb" + "\\src"
            scratchFC_sel =  "T:\\"+scratchGDB+"\\tempFC_sel"
            finalOut = workspaceSrc + "\\" + dataset.split(".")[-1]


            if not arcpy.Exists(finalOut):
                print managementUnitBoundary
                print workspaceWrk
                print workspaceSrc
                print finalOut
                print "Selecting by location"
                arcpy.SelectLayerByLocation_management(scratchFClyr,"INTERSECT",managementUnitBoundary)
                print "Copying Features"
                arcpy.CopyFeatures_management(scratchFClyr, scratchFC_sel)
                print "Clipping"
                try:
                    arcpy.Clip_analysis(scratchFC_sel,managementUnitBoundary,finalOut )
                except:
                    try:
                        print "repairing " + dataset + " for " + tsa
                        arcpy.RepairGeometry_management(scratchFC_sel)
                        arcpy.Clip_analysis(scratchFC_sel,managementUnitBoundary,finalOut, 1)
                    except:
                        print "Cant process " + dataset + " for " + tsa
                        logMessage(logFile, "Cant process " + dataset + " for " + tsa)


                print "onto next"

            else:
                print finalOut + " already exists"
                if overwrite == 'Y':
                    print managementUnitBoundary
                    print workspaceWrk
                    print workspaceSrc
                    print finalOut
                    print "Selecting by location"
                    arcpy.Delete_management(finalOut)
                    arcpy.SelectLayerByLocation_management(scratchFClyr,"INTERSECT",managementUnitBoundary)
                    print "Copying Features"
                    arcpy.CopyFeatures_management(scratchFClyr, scratchFC_sel)
                    print "Clipping"
                    try:
                        arcpy.Clip_analysis(scratchFC_sel,managementUnitBoundary,finalOut )
                    except:
                        try:
                            print "repairing " + dataset + " for " + tsa
                            arcpy.RepairGeometry_management(scratchFC_sel)
                            arcpy.Clip_analysis(scratchFC_sel,managementUnitBoundary,finalOut, 1)
                        except:
                            print "Cant process " + dataset + " for " + tsa
                            logMessage(logFile, "Cant process " + dataset + " for " + tsa)
                    print "onto next"
                else:
                    print 'Not overwriting'
        arcpy.Delete_management(scratchFClyr)


    logFile.close()


def createTmpConnection(work, tempConnect):

# -------------------------------------------------------------
  # connection parameters
  usr = "imcdouga"               # oracle user name
  pw = "supMego8615"            # oracle password (enter correct password for user before running
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



def logMessage(logFile, message):
  logFile.write(message+"\n")

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
