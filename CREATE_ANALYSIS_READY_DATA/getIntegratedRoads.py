# get_F_OWN_2017.py
#   Purpose:
# ---------------------------------------------------------------------------

# Import system modules
import sys, string, os, time
startTime = time.clock()
print time.asctime(time.localtime())
import arcpy
arcpy.env.overwriteOutput = True

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
def delFC(featureClass):
  if arcpy.Exists(featureClass):
    arcpy.AddMessage("Deleting %s..." % (featureClass))
    arcpy.Delete_management(featureClass)

# ----------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------

# Local variables...

getProjectParameters(parameterFileName, parameters)
workspaceSrc = parameters["workspaceSrc"]
workspaceWrk = parameters["workspaceWrk"]
srcGDB = "S:\\FOR\\VIC\\HTS\\ANA\\workarea\\AR2018\\BC_CE_IntegratedRoads_2017_v1_20170214.gdb"
datasrc = "S:\\FOR\\VIC\\HTS\\ANA\\workarea\\AR2018\\BC_CE_IntegratedRoads_2017_v1_20170214.gdb\\integratedRoadsBuffers_2017"
tempGDB = "t:\\tempRDS12345.gdb"
tempRDS = "t:\\tempRDS12345.gdb\\tempRDs"
src = tempGDB + "\\integratedRoadsBuffers_2017"
srcLyr = "srcLyr"
wrk = workspaceSrc+"\\"+"IntegratedRoadsBuffers"
bnd = workspaceWrk+"\\"+"bnd"


if not arcpy.Exists(datasrc):
  arcpy.AddMessage("Input feature class "+datasrc+" does not exist")
  sys.exit(0)

# Deleting existing FC
delFC(wrk)


# Copy file geodatabase to T drive
if not arcpy.Exists(tempGDB):
    arcpy.Copy_management(srcGDB,tempGDB)

#Select the by location using the bnd fc and create a temp FC in the T:\
arcpy.MakeFeatureLayer_management(src,srcLyr)
arcpy.SelectLayerByLocation_management(srcLyr,"INTERSECT",bnd)
arcpy.CopyFeatures_management(srcLyr, tempRDS)
arcpy.RepairGeometry_management(tempRDS)

#Clip and copy fc to Units directory
arcpy.AddMessage("Clipping...")
arcpy.Clip_analysis(tempRDS,bnd,wrk)
arcpy.Delete_management(tempRDS)
arcpy.Delete_management(srcLyr)
##os.remove(tempGDB)
##del (tempGDB)
##del (tempRDS)
##del(srcLyr)
##arcpy.Delete_management(tempGDB)

print "Elapsed time: %d seconds" % (time.clock())
