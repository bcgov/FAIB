#   Purpose: copy boundary feature class from PROVINCIAL to local GDB
# ---------------------------------------------------------------------------

# Import system modules
import sys, string, os.path, time
import arcpy
from arcpy import env
startTime = time.clock()

# ============================================================================
# project parameters
# ============================================================================
parameterFileName = "projectParameters.txt"
parameters = {}

# hardcoded parameters
PROV_TSA = r"W:\FOR\VIC\HTS\ANA\Workarea\PROVINCIAL\provincial.gdb\wrk\tsa_boundaries_2018"

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
  if gp.Exists(featureClass):
    gp.AddMessage("Deleting %s..." % (featureClass))
    gp.Delete_management(featureClass)

# ----------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------

# usage
if len(sys.argv) < 2:
  print "Usage: getBnd [tsa]"
  sys.exit(0)

# System arguments
tsa = sys.argv[1]
tsa_number = string.replace(tsa,"tsa","")

# Local variables...
getProjectParameters(parameterFileName, parameters)
workspaceWrk = parameters["workspaceWrk"]
bnd = "bnd"
scratch00001 = workspaceWrk+"/xx00001"
scratch00002 = workspaceWrk+"/xx00002"
layer = "xx00001_layer"

print time.asctime(time.localtime())
print "Creating the Geoprocessor object..."
gp = arcpy
# gp.env.scratchWorkspace = workspaceWrk

# pre-cleanup
delFC(scratch00001)
delFC(scratch00002)
delFC(workspaceWrk+"/"+bnd)

gp.AddMessage("Making feature layer from %s..." % PROV_TSA)
gp.MakeFeatureLayer_management(PROV_TSA, layer, "\"TSA_NUMBER\" = '"+tsa_number+"'", "", "TSA_NUMBER TSA_NUMBER VISIBLE")

gp.AddMessage("Coping features to %s..." % (scratch00001))
gp.CopyFeatures_management(layer, scratch00001)

gp.AddMessage("Dissolving on TSA_NUMBER...")
gp.Dissolve_management(scratch00001, scratch00002, "TSA_NUMBER;included", "", "SINGLE_PART")

gp.AddMessage("Converting to %s/%s..." % (workspaceWrk,bnd))
fieldMapping = "tsa_number tsa_number True True False 3 String 0 0 ,First,#,"+workspaceWrk+"/"+scratch00002+",TSA_NUMBER,-1,-1"
gp.FeatureClassToFeatureClass_conversion(scratch00002, workspaceWrk, bnd, "", fieldMapping)

gp.AddMessage("Populating bnd_fid in "+workspaceWrk+"/"+bnd+"...")
gp.AddField_management(workspaceWrk+"/"+bnd, "bnd_fid", "LONG")
rows = gp.UpdateCursor(workspaceWrk+"/"+bnd)
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
