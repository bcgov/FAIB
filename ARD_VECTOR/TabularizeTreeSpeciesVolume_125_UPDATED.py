#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      imcdouga
#
# Created:     25/04/2018
# Copyright:   (c) imcdouga 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import sys, string, os, arcpy, logging, xlrd, string, gc
arcpy.env.overwriteOutput = True

def main():
    logFileName = "T:/srcToWrk.log"
    logFile = file(logFileName, "w")
    tsaNums = sys.argv[1]
    root  = sys.argv[2]
    year  = str(sys.argv[3])
    tsas = []
    fileListToArray(tsas,tsaNums)
    arcpy.env.overwriteOutput = True



    for tsa in tsas:
        managementUnitGDB = root  + "\\" + tsa + "\\" + tsa + "_" + year + ".gdb"
        managementUnitGDBtemp = "T:\\temp_ard_calcVriVol.gdb"
        managementUnitGDBtempWrk = managementUnitGDBtemp + "\\wrk"
        managementUnitGDBtempWrkVri = managementUnitGDBtemp + "\\wrk\\vri"
        tsaNum = string.replace(tsa,"tsa","")
        arcpy.Copy_management(managementUnitGDB, managementUnitGDBtemp)
        topoFullName = managementUnitGDBtempWrk +"\\"+"wrk_vri_topology"
        topoName = "wrk_vri_topology"
        fieldMapping = ''
        delFC(topoFullName)
        calcVolumeBySpecies(managementUnitGDBtempWrkVri)

        try:
            arcpy.Copy_management(managementUnitGDBtemp, managementUnitGDB)
        except:
            print  tsaNum + " FAILED Copy from T:\ drive to Archive drive"
            logMessage(logFile, tsaNum + " FAILED Copy from T:\ drive to Archive drive")
            e = sys.exc_info()[1]
            print(e.args[0])
            sys.exit()
        gc.collect()


def calcVolumeBySpecies(inData):
    """Calculates the total volume for each species class in the input vri dataset
    input: 1. VRI feature class
    returns: 1. Summary table of to the total voumes by species grouping"""

    sumSpeciesTable = "sum_cutblock_species"
    sumAllTable = "sum_All_cutblock_species"

    #Create Hectares field
    areaField = "Hectares"
    print "Adding and calculating AREA_HA Field..."
    fieldList = []
    fields = arcpy.ListFields(inData)
    for fld in fields:
        fieldList.append(fld.name)
    if areaField not in fieldList:
        arcpy.AddField_management(inData,areaField, "DOUBLE")

    #Get shape field name
    shapeName = getShapeFieldName(inData)
    # Calculate area field in Hectares
    arcpy.CalculateField_management(inData, areaField, "!" + shapeName + ".area@hectares!", "PYTHON", "")

    #Input fields for arcpy.UpdateCursor
    updateFields = [ "Hectares","feature_id", #0-1
                    "lvlsp1_125","lvlsp2_125","lvlsp3_125","lvlsp4_125","lvlsp5_125", "lvlsp6_125", #2 - 7
                    "SPEC_CD_1","SPEC_CD_2","SPEC_CD_3","SPEC_CD_4","SPEC_CD_5","SPEC_CD_6", #8 - 13
                    "ac_vph125","at_vph125","b_vph125","cw_vph125","dr_vph125","ep_vph125","fd_vph125","h_vph125","la_vph125","mb_vph125","pl_vph125","po_vph125","py_vph125","s_vph125","yc_vph125", #14 to 28
                    "lvlsp1_175","lvlsp2_175","lvlsp3_175","lvlsp4_175","lvlsp5_175", "lvlsp6_175", #29 - 34
                    "ac_vph175","at_vph175","b_vph175","cw_vph175","dr_vph175","ep_vph175","fd_vph175","h_vph175","la_vph175","mb_vph175","pl_vph175","po_vph175","py_vph175","s_vph175","yc_vph175"] # 35 to 49

    #Fields to be created
    newFields = ["ac_vph125","at_vph125","b_vph125","cw_vph125","dr_vph125","ep_vph125","fd_vph125","h_vph125","la_vph125","mb_vph125","pl_vph125","po_vph125","py_vph125","s_vph125","yc_vph125",
                "ac_vph175","at_vph175","b_vph175","cw_vph175","dr_vph175","ep_vph175","fd_vph175","h_vph175","la_vph175","mb_vph175","pl_vph175","po_vph175","py_vph175","s_vph175","yc_vph175"]

    #Create new fields from newFields list
    print "Creating fields"
    fldNames = []
    fields = arcpy.ListFields(inData)

    for fld in fields:
        fldNames.append(fld.name)

    for newFld in newFields:
        if newFld not in fldNames:
            print "creating field " + newFld
            arcpy.AddField_management(inData, newFld, "DOUBLE")


    workspace = os.path.dirname(inData)


    #Calculate the volume for each species group
    print "Updating Species Volumes"
    with arcpy.da.UpdateCursor(inData,updateFields) as cursor2:
        for row in cursor2:
            for i in range (14,29):
                row[i] = 0
            for x in range (35,50):
                row[x] = 0
            for i in range (2,8):
                print row[i+6]
                if row[i+6] is None:
                    pass
                elif row[i+6].lower().startswith('ac'):  #Cottonwood
                    if row[i] is None or row[i] == 0:
                        row[i] = 0
                        row[i + 27] = 0
                    row[14] = row[14] + (row[i])
                    row[35] = row[35] + row[i + 27]
                elif row[i+6].lower().startswith('at'):  #Aspen
                    if row[i] is None or row[i] == 0:
                        row[i] = 0
                        row[i + 27] = 0
                    row[15] = row[15] + (row[i])
                    row[36] = row[36] + row[i + 27]
                elif row[i+6].lower().startswith('b'):  #balsam
                    if row[i] is None or row[i] == 0:
                        row[i] = 0
                        row[i + 27] = 0
                    row[16] = row[16] + (row[i])
                    row[37] = row[37] + row[i + 27]
                elif row[i+6].lower().startswith('c'):  #cedar
                    if row[i] is None or row[i] == 0:
                        row[i] = 0
                        row[i + 27] = 0
                    row[17] = row[17] + (row[i])
                    row[38] = row[38] + row[i + 27]
                elif row[i+6].lower().startswith('d'):  #red alder
                    if row[i] is None or row[i] == 0:
                        row[i] = 0
                        row[i + 27] = 0
                    row[18] = row[18] + (row[i])
                    row[39] = row[39] + row[i + 27]
                elif row[i+6].lower().startswith('e'):  #birch
                    if row[i] is None or row[i] == 0:
                        row[i] = 0
                        row[i + 27] = 0
                    row[19] = row[19] + (row[i])
                    row[40] = row[40] + row[i + 27]
                elif row[i+6].lower().startswith('f'):  #Fir
                    if row[i] is None or row[i] == 0:
                        row[i] = 0
                        row[i + 27] = 0
                    row[20] = row[20] + (row[i])
                    row[41] = row[41] + row[i + 27]
                elif row[i+6].lower().startswith('h'):  #hemlock
                    if row[i] is None or row[i] == 0:
                        row[i] = 0
                        row[i + 27] = 0
                    row[21] = row[21] + (row[i])
                    row[42] = row[42] + row[i + 27]
                elif row[i+6].lower().startswith('l'):  #larch
                    if row[i] is None or row[i] == 0:
                        row[i] = 0
                        row[i + 27] = 0
                    row[22] = row[22] + (row[i])
                    row[43] = row[43] + row[i + 27]
                elif row[i+6].lower().startswith('m'):  #maple
                    if row[i] is None or row[i] == 0:
                        row[i] = 0
                        row[i + 27] = 0
                    row[23] = row[23] + (row[i])
                    row[44] = row[44] + row[i + 27]
                elif row[i+6].lower() in ('p','pl','pli','plc', 'pj'): #lodgepole pine
                    if row[i] is None or row[i] == 0:
                        row[i] = 0
                        row[i + 27] = 0
                    row[24] = row[24] + (row[i])
                    row[45] = row[45] + row[i + 27]
                elif row[i+6].lower() in ('pa','pw','pf'): #pine other
                    if row[i] is None or row[i] == 0:
                        row[i] = 0
                        row[i + 27] = 0
                    row[25] = row[25] + (row[i])
                    row[46] = row[46] + row[i + 27]
                elif row[i+6].lower() in ('py'): # ponderosa pine (yellow)
                    if row[i] is None or row[i] == 0:
                        row[i] = 0
                        row[i + 27] = 0
                    row[26] = row[26] + (row[i])
                    row[47] = row[47] + row[i + 27]
                elif row[i+6].lower().startswith('s'): # Spruce
                    if row[i] is None or row[i] == 0:
                        row[i] = 0
                        row[i + 27] = 0
                    row[27] = row[27] + (row[i])
                    row[48] = row[48] + row[i + 27]
                elif row[i+6].lower().startswith('y'): # Cypress
                    if row[i] is None or row[i] == 0:
                        row[i] = 0
                        row[i + 27] = 0
                    row[28] = row[28] + (row[i])
                    row[49] = row[49] + row[i + 27]
            cursor2.updateRow(row)
    arcpy.AddMessage("Created total for sepecies rank live volume fields")

    del row
    del cursor2



def getShapeFieldName(inFC):
    """Gets the name of the Geometry area field in a feature class"""
    fieldNames = []
    fields = arcpy.ListFields(inFC)
    for fld in fields:
        fieldNames.append(fld.name.upper())
    if "SHAPE_AREA" in fieldNames:
        return "SHAPE"
    elif "GEOMETRY_AREA" in fieldNames:
        return "GEOMETRY"

def delFC(featureClass):
  if arcpy.Exists(featureClass):
    arcpy.AddMessage("Deleting %s..." % (featureClass))
    arcpy.Delete_management(featureClass)

def createTopology(workspaceWrk,inputVRI,topoName, topoFullName):
    arcpy.AddMessage("Creating %s..." % (topoName))
    arcpy.CreateTopology_management(workspaceWrk,  topoName)
    arcpy.AddFeatureClassToTopology_management(topoFullName,inputVRI)
    arcpy.AddRuleToTopology_management(topoFullName,"Must Not Overlap (Area)",inputVRI)
    arcpy.ValidateTopology_management(topoFullName)


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
