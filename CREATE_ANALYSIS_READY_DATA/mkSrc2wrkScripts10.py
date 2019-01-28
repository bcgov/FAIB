# ================================================================================
# NAME:
#    mksrc2wrkscripts.py
#
# FUNCTION:
#   - open a spreadsheet containing database of src and wrk feature classes and fields
#     and create a src2wrk script for each feature class
#
# HISTORY:
#   20090806 Doug Layden -- original coding
#   201002   Doug Layden -- removed dissolve; jumbles multi-layered polygons
#                        -- added eliminate if number of polygons is > 100000
#                        -- added simplify polygons
#   20100224 Doug Layden -- made simplify polygons options -- hangs on some feature classes
#                        -- added RepairGeometry as final step
#   20110518 Doug Layden -- replaced simplifyPolygons flag with weedTolerance value
#                           Works the same except weedTolerance read from parameter file
#                           rather than being not hard coded in this script
#   20160309 Doug Layden -- removed eliminated and simplify polygons options
#
# ================================================================================

import string, sys, os, time, arcpy
from win32com.client import Dispatch

# ============================================================================
# hardcoded values
# ============================================================================
mpsFactor = 10.0    #  factor to adjust project minPolySize for intermediate processing
                    #  (e.g., mpsFactor = 10 => mps 1/10 ha for src2wrk process)
parameterFileName = "projectParameters.txt"
parameters = {}
parametersNeeded = {}
parametersNeeded["workspaceSrc"] = "src dataset location"
parametersNeeded["workspaceWrk"] = "wrk dataset location"
parametersNeeded["dataDictionary"] = "project data dictionary"
parametersNeeded["src2wrkTab"] = "src2wrkTab in data dictionary"
parametersNeeded["src2wrkPath"] = "location of src2wrk scripts"
parametersNeeded["minPolySize"] = "minimum polygons size for eliminate"
parametersNeeded["weedTolerance"] = "Weed tolerance for simplify (0=no simplify)"

# ----------------------------------------------------------------------------
def getProjectParameters(parameterFileName, parameters, parametersNeeded):

  # check if parameter file exists
  if not os.path.isfile(parameterFileName):
    print "  Project parameter file '"+parameterFileName+"' not found in current directory"
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

  missingParameters = {}
  for key in parametersNeeded:
    if not parameters.has_key(key):
      missingParameters[key] = 0
  if len(missingParameters.keys()) > 0:
    print "Error: parameter(s) not found in %s" % (parameterFileName)
    for key in sorted(missingParameters.keys()):
      print "  %-30s  %s" % (key, parametersNeeded[key])
    sys.exit()

# --------------------------------------------------------------------------------
# start the script
# --------------------------------------------------------------------------------

def startScript(scriptName,scriptFile,srcFeatureClass,wrkFeatureClass):
  scriptFile.write('# %s.py\n' % (wrkFeatureClass))
  scriptFile.write('#   Purpose: convert srcFC %s to wrkFC %s\n' % (srcFeatureClass,wrkFeatureClass))
  scriptFile.write('# ---------------------------------------------------------------------------\n')
  scriptFile.write('\n')

  scriptFile.write('# Import system modules\n')
  scriptFile.write('import sys, string, os, time\n')
  scriptFile.write('startTime = time.clock()\n')
  scriptFile.write('print time.asctime(time.localtime())\n')
  scriptFile.write('\n')

  scriptFile.write('print "Importing arcpy..."\n')
  scriptFile.write('import arcpy\n')
  scriptFile.write('\n')

  scriptFile.write('# ----------------------------------------------------------------------------\n')
  scriptFile.write('def delFC(featureClass):\n')
  scriptFile.write('  if gp.Exists(featureClass):\n')
  scriptFile.write('    gp.AddMessage("Deleting %s..." % (featureClass))\n')
  scriptFile.write('    gp.Delete_management(featureClass)\n')
  scriptFile.write('\n')

  scriptFile.write('# ----------------------------------------------------------------------------\n')
  scriptFile.write('# MAIN\n')
  scriptFile.write('# ----------------------------------------------------------------------------\n')
  scriptFile.write('\n')

  scriptFile.write('# Local variables...\n')
  scriptFile.write('workspaceSrc = r"%s"\n' % (workspaceSrc))
  scriptFile.write('workspaceWrk = r"%s"\n' % (workspaceWrk))
  scriptFile.write('minPolySize = %s\n' % (minPolySize))
  scriptFile.write('weedTolerance = %s\n' % (weedTolerance))
  scriptFile.write('src = workspaceSrc+"\\\\%s"\n' % (srcFeatureClass))
  scriptFile.write('wrk = workspaceWrk+"\\\\%s"\n' % (wrkFeatureClass))
  scriptFile.write('scratch00001 = \"xx00001\"\n')
  scriptFile.write('layer = \"xx00002_layer\"\n')
  scriptFile.write('topoName = "wrk_%s_topology"\n' % (wrkFeatureClass))
  scriptFile.write('\n')

  scriptFile.write('gp = arcpy\n')
  scriptFile.write('gp.env.workspace = workspaceWrk\n')
  scriptFile.write('gp.env.OverwriteOutput = "TRUE"\n')
  scriptFile.write('\n')

  scriptFile.write('if not gp.Exists(src):\n')
  scriptFile.write('  gp.AddMessage("Input feature class "+src+" does not exist")\n')
  scriptFile.write('  sys.exit(0)\n')
  scriptFile.write('\n')

  scriptFile.write('delFC(scratch00001)\n')
  scriptFile.write('delFC(topoName)\n')
  scriptFile.write('delFC(wrk)\n')
  scriptFile.write('\n')


# --------------------------------------------------------------------------------
# finish the script
# --------------------------------------------------------------------------------

def finishScript(scriptFile,fieldMapping,wrkFeatureClass):
  scriptFile.write('gp.AddMessage("Converting %s to wrk specifications (%s)..." % (src,scratch00001))\n')
  scriptFile.write('gp.FeatureClassToFeatureClass_conversion(src, workspaceWrk, scratch00001, "", "%s")\n' % (fieldMapping))
  scriptFile.write('\n')

  scriptFile.write('gp.AddMessage("Converting multipart to single part (%s)..." % (wrk))\n')
  scriptFile.write('gp.MultipartToSinglepart_management (scratch00001, wrk)\n')
  scriptFile.write('\n')

  scriptFile.write('fid = "%s_fid"\n' % (wrkFeatureClass))
  scriptFile.write('gp.AddMessage("Adding %s..." % (fid))\n')
  scriptFile.write('gp.AddField_management(wrk, fid, "LONG")\n')
  scriptFile.write('gp.CalculateField_management(wrk, fid, "!OBJECTID!","PYTHON_9.3")\n')
  scriptFile.write('\n')

  scriptFile.write('gp.AddMessage("Creating %s..." % (topoName))\n')
  scriptFile.write('gp.CreateTopology_management(workspaceWrk,  topoName)\n')
  scriptFile.write('gp.AddFeatureClassToTopology_management(topoName,wrk)\n')
  scriptFile.write('gp.AddRuleToTopology_management(topoName,"Must Not Overlap (Area)",wrk)\n')
  scriptFile.write('gp.ValidateTopology_management(topoName)\n')
  scriptFile.write('\n')

  scriptFile.write('delFC(scratch00001)\n')
  scriptFile.write('\n')
  scriptFile.write('print "Elapsed time: %d seconds" % (time.clock())\n')
  return

# --------------------------------------------------------------------------------
# add to field mapping variable
# --------------------------------------------------------------------------------
def setfieldMapping(fieldMapping,workspaceSrc,srcFeatureClass,wrkShortName,IsNullable,Editable,Required,Length,Type,Precision,Scale):

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

# ============================================================================
# MAIN
# ============================================================================

# check if the script was invoked from the command line or toolbox
#   command line    no arguments
#   toolbox         seven arguments
if len(sys.argv) < 6:
  fromCommandLine = 1
else:
  fromCommandLine = 0

# --------------------------------------------------------------------------
# initialization differs if invoked from command line or tool box
# --------------------------------------------------------------------------

if fromCommandLine:

  # --------------------------------------------------------------------------------
  # local variables
  # --------------------------------------------------------------------------------
  getProjectParameters(parameterFileName, parameters, parametersNeeded)
  workspaceWrk = parameters["workspaceWrk"]
  workspaceSrc = parameters["workspaceSrc"]
  dataDictionary = parameters["dataDictionary"]
  worksheetName = parameters["src2wrkTab"]
  src2wrk = parameters["src2wrkPath"]
  minPolySize = parameters["minPolySize"]
  weedTolerance = parameters["weedTolerance"]
else:

  # --------------------------------------------------------------------------
  # called from toolbox
  # --------------------------------------------------------------------------

  # Get script arguments (Required vs Optional and defaults are set as dialog properties)
  workspaceSrc   = sys.argv[1]     # Input feature classes workspace
  workspaceWrk   = sys.argv[2]     # Output Feature classes workspace
  dataDictionary = sys.argv[3]     # Excel speadsheet with the conversion definitions
  worksheetName  = sys.argv[4]     # Tab in the Excel spreadsheet with the conversion definitions
  src2wrk        = sys.argv[5]     # Script output folder
  minPolySize    = sys.argv[6]     # minimum polygons size for eliminate
  weedTolerance  = sys.argv[7]     # WeedTolerance for simplify (0 = no simplify)

# setup geoprocessing
print "Creating geoprocessing object..."
gp = arcpy

# --------------------------------------------------------------------------------
# Check if arguments valid (only those used by the mkSrc2Wrk script
# not those used by the output scripts
# --------------------------------------------------------------------------------

# validate
if not os.path.isfile(dataDictionary):
  gp.AddMessage("Data dictionary '" + dataDictionary + "' not found.")
  sys.exit(1)

# --------------------------------------------------------------------------------
# local variables in common
# --------------------------------------------------------------------------------
row_origin = 1
col_origin = 2

# --------------------------------------------------------------------------------
# Open the database spreadsheet
# --------------------------------------------------------------------------------
xl = Dispatch("Excel.Application")
##xl.Visible = 0   # set to 1 to make the process visible
workbook = xl.Workbooks.Open(dataDictionary)
try:
  worksheet = workbook.Sheets(worksheetName)
except:
  gp.AddMessage("ERROR: Worksheet %s not found in %s." % (worksheetName,dataDictionary))
  sys.exit(1)

# --------------------------------------------------------------------------------
# gp.AddMessage("Looping through feature classes...")
# --------------------------------------------------------------------------------

# first row
row = row_origin + 1   # skip header row
col = col_origin
srcFeatureClass = worksheet.Cells(row,col).Value; col=col+1
srcFieldName = worksheet.Cells(row,col).Value; col=col+1
wrkFeatureClass = worksheet.Cells(row,col).Value; col=col+1
wrkFieldName = worksheet.Cells(row,col).Value; col=col+1
wrkShortName = worksheet.Cells(row,col).Value; col=col+1
IsNullable = worksheet.Cells(row,col).Value; col=col+1
Required = worksheet.Cells(row,col).Value; col=col+1
Editable = worksheet.Cells(row,col).Value; col=col+1
Length = worksheet.Cells(row,col).Value; col=col+1
Type = worksheet.Cells(row,col).Value; col=col+1
Precision = worksheet.Cells(row,col).Value; col=col+1
Scale = worksheet.Cells(row,col).Value
Scale = worksheet.Cells(row,col).Value
fieldMapping = ''

if srcFeatureClass:

  # start the script
  scriptName = src2wrk+"\\"+wrkFeatureClass+".py"
  print "Creating %s..." % (scriptName)
  scriptFile =  open(scriptName,"w")
  startScript(scriptName,scriptFile,srcFeatureClass,wrkFeatureClass)

  # setup so first row will not be treated as a new srcFeatureClass
  prev_srcFeatureClass = srcFeatureClass
  prev_wrkFeatureClass = wrkFeatureClass

while srcFeatureClass:

  if srcFeatureClass != prev_srcFeatureClass:

    # finish script for previous feature class
    finishScript(scriptFile,fieldMapping,prev_wrkFeatureClass)
    scriptFile.close()
    fieldMapping = ''

    # start script for current feature class
    scriptName = src2wrk+"\\"+wrkFeatureClass+".py"
    print "Creating %s..." % (scriptName)
    scriptFile =  open(scriptName,"w")
    startScript(scriptName,scriptFile,srcFeatureClass,wrkFeatureClass)
    prev_srcFeatureClass = srcFeatureClass
    prev_wrkFeatureClass = wrkFeatureClass

  fieldMapping = setfieldMapping(fieldMapping,workspaceSrc,srcFeatureClass,wrkShortName,IsNullable,Required,Editable,Length,Type,Precision,Scale)

  # next row
  row = row + 1
  col = col_origin
  srcFeatureClass = worksheet.Cells(row,col).Value; col=col+1
  srcFieldName = worksheet.Cells(row,col).Value; col=col+1
  wrkFeatureClass = worksheet.Cells(row,col).Value; col=col+1
  wrkFieldName = worksheet.Cells(row,col).Value; col=col+1
  wrkShortName = worksheet.Cells(row,col).Value; col=col+1
  IsNullable = worksheet.Cells(row,col).Value; col=col+1
  Required = worksheet.Cells(row,col).Value; col=col+1
  Editable = worksheet.Cells(row,col).Value; col=col+1
  Length = worksheet.Cells(row,col).Value; col=col+1
  Type = worksheet.Cells(row,col).Value; col=col+1
  Precision = worksheet.Cells(row,col).Value; col=col+1
  Scale = worksheet.Cells(row,col).Value

# finish the final script
finishScript(scriptFile,fieldMapping,prev_wrkFeatureClass)
scriptFile.close()

# --------------------------------------------------------------------------------
# close the spreadsheet
# --------------------------------------------------------------------------------
xl.ActiveWorkbook.Close(SaveChanges=1)
worksheet = None
workbook = None
xl.Quit()
xl = None
