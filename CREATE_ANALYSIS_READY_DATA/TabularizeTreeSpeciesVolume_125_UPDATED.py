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
# Import system modules
import sys, string, os, time
startTime = time.clock()
print time.asctime(time.localtime())
import arcpy

# ============================================================================
# project parameters
# ============================================================================
parameterFileName = "projectParameters.txt"
parameters = {}


# ----------------------------------------------------------------------------
def getProjectParameters(parameterFileName, parameters):

  # check if parameter file exists
  if not os.path.isfile(parameterFileName):
    print "  Project parameter file "+parameterFileName+" not found."
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


# ----------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------

### Local variables...
getProjectParameters(parameterFileName, parameters)
workspaceSrc = parameters["workspaceSrc"]
workspaceWrk = parameters["workspaceWrk"]
inputVRI = workspaceWrk+"/"+"vri"
topoFullName = workspaceWrk+"/"+"wrk_vri_topology"
topoName = "wrk_vri_topology"

def main():
    delFC(topoFullName)
    calcVolumeBySpecies(inputVRI)
    createTopology(workspaceWrk,inputVRI,topoName,topoFullName)

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
                    "lvltotsp1","lvltotsp2","lvltotsp3","lvltotsp4","lvltotsp5","lvltotsp6", #8 - 13
                    "SPEC_CD_1","SPEC_CD_2","SPEC_CD_3","SPEC_CD_4","SPEC_CD_5","SPEC_CD_6", #14 - 19
                    "ac_vph125","at_vph125","b_vph125","cw_vph125","dr_vph125","ep_vph125","fd_vph125","h_vph125","la_vph125","mb_vph125","pl_vph125","po_vph125","py_vph125","s_vph125","yc_vph125", #20 - 34
                    "CtWood","Aspen","Balsam","Cedar","RedAlder", "Birch","Fir","Hemlock", "Larch","Maple","Lodgepole","WhitePine","YellowPine","Spruce","Cypress", #35 - 49
                    "lvltot_125","vph125","Unknown","m3_125", #50 - 53
                    "CedarCypress","FirLarch","HemBal","Pine","SpruceAll","Decid"] #54 - 59

    #Fields to be created
    newFields = ["lvltotsp1","lvltotsp2","lvltotsp3","lvltotsp4","lvltotsp5","lvltotsp6", #0-5
                "ac_vph125","at_vph125","b_vph125","cw_vph125","dr_vph125","ep_vph125","fd_vph125","h_vph125","la_vph125","mb_vph125","pl_vph125","po_vph125","py_vph125","s_vph125","yc_vph125","vph125",
                "Aspen","Balsam","Birch","Cedar","CtWood","Cypress","Fir","Hemlock", "Larch","Maple","Lodgepole","WhitePine","YellowPine","RedAlder","Spruce","Unknown","Hectares","m3_125",
                "CedarCypress","FirLarch","HemBal","Pine","SpruceAll","Decid"]

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


##    edit = arcpy.da.Editor(workspace)
##    edit.startEditing(False, True)
##    edit.startOperation()

    #Calculate the volume for each species group
    print "Updating Species Volumes"
    with arcpy.da.UpdateCursor(inData,updateFields) as cursor2:
        for row in cursor2:
            for i in range (2,8):
                if row[i] is None:
                    row[i] = 0
                row[i+6] = row[i] * (row[0])

            for i in range (20,50):
                row[i] = 0
            for i in range(8,14):
                if row[i+6] is None:
                    pass
                elif row[i+6].lower().startswith('ac'):  #Cottonwood
                    row[20] = row[20] + (row[i]/row[0])
                    row[35] = row[35] + row[i]
                elif row[i+6].lower().startswith('at'):  #Aspen
                    row[21] = row[21] + (row[i]/row[0])
                    row[36] = row[36] + row[i]
                elif row[i+6].lower().startswith('b'):  #balsam
                    row[22] = row[22] + (row[i]/row[0])
                    row[37] = row[37] + row[i]
                elif row[i+6].lower().startswith('c'):  #cedar
                    row[23] = row[23] + (row[i]/row[0])
                    row[38] = row[38] + row[i]
                elif row[i+6].lower().startswith('d'):  #red alder
                    row[24] = row[24] + (row[i]/row[0])
                    row[39] = row[39] + row[i]
                elif row[i+6].lower().startswith('e'):  #birch
                    row[25] = row[25] + (row[i]/row[0])
                    row[40] = row[40] + row[i]
                elif row[i+6].lower().startswith('f'):  #Fir
                    row[26] = row[26] + (row[i]/row[0])
                    row[41] = row[41] + row[i]
                elif row[i+6].lower().startswith('h'):  #hemlock
                    row[27] = row[27] + (row[i]/row[0])
                    row[42] = row[42] + row[i]
                elif row[i+6].lower().startswith('l'):  #larch
                    row[28] = row[28] + (row[i]/row[0])
                    row[43] = row[43] + row[i]
                elif row[i+6].lower().startswith('m'):  #maple
                    row[29] = row[29] + (row[i]/row[0])
                    row[44] = row[44] + row[i]
                elif row[i+6].lower() in ('p','pl','pli','plc', 'pj'): #lodgepole pine
                    row[30] = row[30] + (row[i]/row[0])
                    row[45] = row[45] + row[i]
                elif row[i+6].lower() in ('pa','pw','pf'): #pine other
                    row[31] = row[31] + (row[i]/row[0])
                    row[46] = row[46] + row[i]
                elif row[i+6].lower() in ('py'): # ponderosa pine (yellow)
                    row[32] = row[32] + (row[i]/row[0])
                    row[47] = row[47] + row[i]
                elif row[i+6].lower().startswith('s'): # Spruce
                    row[33] = row[33] + (row[i]/row[0])
                    row[48] = row[48] + row[i]
                elif row[i+6].lower().startswith('y'): # Cypress
                    row[34] = row[34] + (row[i]/row[0])
                    row[49] = row[49] + row[i]

                #Calculate Total Stand Volume
                if row [50] is None:
                    row[50] = 0
                row[51] = row[50]
                row[53] = row[50] * row[0]
                row[52] = row[53] - (row[35] + row[36] + row[37] + row[38] + row[39] + row[40] + row[41] + row[42] + row[43] + row[44] + row[45] + row[46] + row[47] + row[48] + row[49])
                row[54] = row[38] + row[49] #Cedar + Cypress
                row[55] = row[41] + row[43] #Fir + Larch
                row[56] = row[42] + row[37] #Hemlock   + Balsam
                row[57] = row[45] + row[46] + row[47]#Lodgepole + WhitePine + YellowPine
                row[58] = row[48] #Spruce
                row[59] = row[36] + row[40] + row[35] + row[44] + row[39] #Aspen + Birch + CtWood + Maple + RedAlder
            cursor2.updateRow(row)
    arcpy.AddMessage("Created total for sepecies rank live volume fields")

    del row
    del cursor2

##    edit.stopOperation()
##    edit.stopEditing(True)

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

if __name__ == '__main__':
    main()
