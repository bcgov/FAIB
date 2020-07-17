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

    logFileName = "T:/resolve_uwr.log"
    logFile = file(logFileName, "w")
    tsaNums = sys.argv[1]
    root = sys.argv[2]
    year = sys.argv[3]
    tsas = []
    fileListToArray(tsas,tsaNums)
    arcpy.env.overwriteOutput = True

    for tsa in tsas:
        rootTSAgdb = root  + "\\" + tsa + "\\" + tsa + "_" + year + ".gdb"
        fc = rootTSAgdb + "\\src\\WCP_UNGULATE_WINTER_RANGE_SP"
        whereClauseCond = "TIMBER_HARVEST_CODE = 'CONDITIONAL HARVEST ZONE'"
        whereClauseNoHarv = "TIMBER_HARVEST_CODE in ( 'No Harvest Zone' , 'NO HARVEST ZONE' )"
        workspaceSrc =  rootTSAgdb + "\\src"
        workspaceWrk =  rootTSAgdb + "\\wrk"
        finalOutNameCond = "WCP_UNGULATE_WINTER_RANGE_SP_CONDITIONAL_HARVEST"
        finalOutFullCond = workspaceSrc  + "\\" + finalOutNameCond
        finalOutNameNoHarv = "WCP_UNGULATE_WINTER_RANGE_SP_NO_HARVEST"
        finalOutFullNoHarv = workspaceSrc  + "\\" + finalOutNameNoHarv
        try:
            arcpy.FeatureClassToFeatureClass_conversion(fc,workspaceSrc, finalOutNameCond, whereClauseCond)
        except:
            print 'Could not create WCP_UNGULATE_WINTER_RANGE_SP_CONDITIONAL_HARVEST for ' + tsa
            logMessage(logFile, 'Could not create WCP_UNGULATE_WINTER_RANGE_SP_CONDITIONAL_HARVEST for ' + tsa)
            print "onto next"
        try:
            arcpy.FeatureClassToFeatureClass_conversion(fc,workspaceSrc, finalOutNameNoHarv, whereClauseNoHarv)
        except:
            print 'Could not create WCP_UNGULATE_WINTER_RANGE_SP_NO_HARVEST for ' + tsa
            logMessage(logFile, 'Could not create WCP_UNGULATE_WINTER_RANGE_SP_NO_HARVEST for ' + tsa)
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
