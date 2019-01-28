# GetCutblocks2018.py
#   Purpose:
# ---------------------------------------------------------------------------

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
def delFC(featureClass):
  if gp.Exists(featureClass):
    gp.AddMessage("Deleting %s..." % (featureClass))
    gp.Delete_management(featureClass)

# ----------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------

# Local variables...
getProjectParameters(parameterFileName, parameters)
workspaceSrc = parameters["workspaceSrc"]
workspaceWrk = parameters["workspaceWrk"]
src = "S:/FOR/VIC/HTS/FAIB_DATA_FOR_DISTRIBUTION/Cutblocks/Consolidated_Cutblocks.gdb/Cut_Block_All_BC"
out = workspaceWrk+"/"+"cutblocks2018"
bnd = workspaceWrk+"/"+"bnd"
cutblocks2018 = "cutblocks2018"

print "Creating the geoprocessor object..."
gp = arcpy

if not gp.Exists(src):
  gp.AddMessage("Input feature class "+src+" does not exist")
  sys.exit(0)

delFC(out)
gp.AddMessage("Clipping...")
gp.Clip_analysis(src,bnd,out)
gp.AddMessage("Clipping using %s..." % (bnd))
gp.AddMessage("Clipping to %s..." % (out))

gp.AddMessage("Populating cutblocks2018_fid in "+workspaceWrk+"/"+cutblocks2018+"...")
gp.AddField_management(workspaceWrk+"/"+cutblocks2018, "cutblocks2018_fid", "LONG")
rows = gp.UpdateCursor(workspaceWrk+"/"+cutblocks2018)
row = rows.next()
n = 1
while row:
  row.cutblocks2018_fid = n
  rows.updateRow(row)
  row = rows.next()
  n = n + 1

print "Elapsed time: %d seconds" % (time.clock())
