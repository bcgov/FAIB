import arcpy, os
arcpy.env.overwriteOutput = True

def main():

    logFileName = "T:/getBnd.log"
    logFile = file(logFileName, "w")
    tsaNums = sys.argv[1]
    root  = sys.argv[2]
    year  = str(sys.argv[3])
    bnds = sys.argv[4]
    tsas = []
    fileListToArray(tsas,tsaNums)
    arcpy.env.overwriteOutput = True

    bnd = "bnd"
    layer = "xx00001_layer"

    for tsa in tsas:
        tsaNum = tsa.split("tsa")[-1]
        rootTSAgdb = root  + "\\" + tsa + "\\" + tsa + "_" + year + ".gdb"
        rootTSAgdbWrk = rootTSAgdb + "\\wrk"
        rootTSAgdbBnd = rootTSAgdbWrk + "\\bnd"
        scratch00001 = rootTSAgdb + "\\wrk\\xx00001"
        scratch00002 = rootTSAgdb + "\\wrk\\xx00002"
        delFC(scratch00001)
        delFC(scratch00002)
        delFC(rootTSAgdbBnd)

        arcpy.AddMessage("Making feature layer from %s..." % bnds)
        arcpy.MakeFeatureLayer_management(bnds, layer, "\"TSA_NUMBER\" = '"+tsaNum+"'", "", "TSA_NUMBER TSA_NUMBER VISIBLE")

        arcpy.AddMessage("Coping features to %s..." % (scratch00001))
        arcpy.CopyFeatures_management(layer, scratch00001)

        arcpy.AddMessage("Dissolving on TSA_NUMBER...")
        arcpy.Dissolve_management(scratch00001, scratch00002, "TSA_NUMBER;included", "", "SINGLE_PART")

        arcpy.AddMessage("Converting to %s/%s..." % (rootTSAgdbWrk,bnd))
        fieldMapping = "tsa_number tsa_number True True False 3 String 0 0 ,First,#,"+rootTSAgdbWrk+"/"+scratch00002+",TSA_NUMBER,-1,-1"
        arcpy.FeatureClassToFeatureClass_conversion(scratch00002, rootTSAgdbWrk, bnd, "", fieldMapping)

        arcpy.AddMessage("Populating bnd_fid in "+rootTSAgdbWrk +"/"+bnd+"...")
        arcpy.AddField_management(rootTSAgdbBnd, "bnd_fid", "LONG")
        rows = arcpy.UpdateCursor(rootTSAgdbBnd)
        row = rows.next()
        n = 1
        while row:
            row.bnd_fid = n
            rows.updateRow(row)
            row = rows.next()
            n = n + 1
            print n - 1

        # cleanup
        delFC(scratch00001)
        delFC(scratch00002)

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
