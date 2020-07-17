#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      imcdouga
#
# Created:     23/04/2020
# Copyright:   (c) imcdouga 2020
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import arcpy
import arcpy, os
arcpy.env.overwriteOutput = False

def main():

    logFileName = "T:/createARDdir.log"
    logFile = file(logFileName, "w")
    tsaNums = sys.argv[1]
    root  = sys.argv[2]
    year  = str(sys.argv[3])
    tsas = []
    fileListToArray(tsas,tsaNums)
    arcpy.env.overwriteOutput = False
    for tsa in tsas:
        rootTSA = root  + "\\" + tsa
        rootTSAgdb = root  + "\\" + tsa + "\\" + tsa + "_" + year + ".gdb"
        gdbName =  tsa + "_" + year + ".gdb"
        gdbDir = root  + "\\" + tsa
        cmd = r"mkdir " + rootTSA # create folder for each tsa under units folder
        os.system(cmd)
        if not arcpy.Exists(rootTSAgdb):
          arcpy.AddMessage("Creating File GDB %s/%s..." % (gdbDir,gdbName))
          arcpy.CreateFileGDB_management(gdbDir, gdbName)

          arcpy.AddMessage("Creating feature datasets...")
          for dataset in ("src", "wrk", "fin"):
            sr = arcpy.SpatialReference(3005)
            arcpy.CreateFeatureDataset_management(rootTSAgdb, dataset, sr)
    logFile.close()
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
