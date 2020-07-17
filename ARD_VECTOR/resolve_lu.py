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

    logFileName = "T:/resolve_lu.log"
    logFile = file(logFileName, "w")
    tsaNums = sys.argv[1]
    root = sys.argv[2]
    year = sys.argv[3]
    tsas = []
    fileListToArray(tsas,tsaNums)
    arcpy.env.overwriteOutput = True

    for tsa in tsas:
        rootTSAgdb = root  + "\\" + tsa + "\\" + tsa + "_" + year + ".gdb"
        fc = rootTSAgdb + "\\src\\RMP_LANDSCAPE_UNIT_SVW"
        whereClause = "BIODIVERSITY_EMPHASIS_OPTION <>  'Multiple'"
        workspaceSrc =  rootTSAgdb + "\\src"
        workspaceWrk =  rootTSAgdb + "\\wrk"
        finalOutName = "RMP_LANDSCAPE_UNIT_SVW_NO_MULTIPLES"
        finalOutFull = workspaceSrc  + "\\" + finalOutName
        deleteFC = workspaceWrk  + "\\" + finalOutName
        try:
            if arcpy.Exists("deleteFC"):
                arcpy.Delete_management(deleteFC)
            arcpy.FeatureClassToFeatureClass_conversion(fc,workspaceSrc, finalOutName, whereClause)

        except:
            e = sys.exc_info()[1]
            print(e.args[0])
            print 'Could not create RMP_LANDSCAPE_UNIT_SVW_NO_MULTIPLES for ' + tsa
            logMessage(logFile, 'Could not create RMP_LANDSCAPE_UNIT_SVW_NO_MULTIPLES for ' + tsa + e.args[0])
            print "onto next"
        print "onto next"
    logFile.close()



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
