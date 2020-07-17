import arcpy, os
arcpy.env.overwriteOutput = True

def main():

    logFileName = "T:/getIntRds.log"
    logFile = file(logFileName, "w")
    tsaNums = sys.argv[1]
    root  = sys.argv[2]
    year  = str(sys.argv[3])
    inRds = sys.argv[4]
    tsas = []
    fileListToArray(tsas,tsaNums)
    arcpy.env.overwriteOutput = True

    # get path of input FC
    list= inRds.split("\\")[0:-1]
    delim = "\\"
    rdsGDB = delim.join(list)

    tempGDB = "t:\\tempRDS12345.gdb"
    gdbName = "tempRDS12345.gdb"
    tempRDS = "t:\\tempRDS12345.gdb\\tempRDs"
    src = tempGDB + "\\" + inRds.split("\\")[-1]
    srcLyr = "srcLyr"

    if arcpy.Exists(tempGDB):
        arcpy.Delete_management(tempGDB)

    # Copy file geodatabase to T drive
    if not arcpy.Exists(tempGDB):
        arcpy.Copy_management(rdsGDB,tempGDB)

    arcpy.MakeFeatureLayer_management(src,srcLyr)

    for tsa in tsas:
        rootTSAgdb = root  + "\\" + tsa + "\\" + tsaNum + "_" + year + ".gdb"
        rootTSAgdbRds = rootTSAgdb + "\\src\\IntegratedRoadsBuffers"
        bnd = rootTSAgdb + "\\wrk\\bnd"

        # Deleting existing FC
        delFC(rootTSAgdbRds)


        arcpy.SelectLayerByLocation_management(srcLyr,"INTERSECT",bnd)
        arcpy.CopyFeatures_management(srcLyr, tempRDS)
        arcpy.RepairGeometry_management(tempRDS)

        #Clip and copy fc to Units directory
        arcpy.AddMessage("Clipping...")
        print"output is " + wrk
        arcpy.Clip_analysis(tempRDS,bnd,rootTSAgdbRds)


    print "Elapsed time: %d seconds" % (time.clock())
    logFile.close()

# ----------------------------------------------------------------------------
def delFC(featureClass):
  if arcpy.Exists(featureClass):
    arcpy.AddMessage("Deleting %s..." % (featureClass))
    arcpy.Delete_management(featureClass)

# ----------------------------------------------------------------------------

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