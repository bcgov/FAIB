# ---------------------------------------------------------------------------
# extractBCGW.py
#   Purpose: Extract features from BCGW clipped to managementUnitBoundary
#
#   Modifications:
#     2008-06-13 - Doug Layden - based on extractVRI
#     2008-06-16 - Doug Layden - defined usage , extractFeatures, logMessage and elapsedTime modules
#     2008-08-07 - Doug Layden - modified from MPB2008 -> extracts for single MU rather than MUs read from list file
#     2009-11-05 - Doug Layden - redesigned so that it runs from command line or tool box
#     2009-11-24 - Doug Layden - changed so it creates a scratch GDB feature class rather than a shape to keep long field names
#     2010-12-07 - Doug Layden - use "try" and log failures from clipping
#
#   Variable      Example values
#    layerCode    bgc
#    BCGWLayer    WHSE_FOREST_VEGETATION.BEC_BIOGEOCLIMATIC_POLY
#    outputName   BEC_BIOGEOCLIMATIC_POLY
# ---------------------------------------------------------------------------

# Import system modules
print "Importing arcpy..."
import arcpy
import sys, string, os, os.path, time, getpass
from arcpy import env

# ============================================================================
# hardcoded values -- used only when invoked from command line
# ============================================================================
parameterFileName = "projectParameters.txt"
parameters = {}
parametersNeeded = {}
parametersNeeded["databaseConnection"] = "BCGW database connection name"
parametersNeeded["managementUnitBoundary"] = "project boundary feature class"
parametersNeeded["workspaceWrk"] = "the GDB and dataset where the boundary is found"
parametersNeeded["workspaceSrc"] = "the GDB and dataset where the feature classes will be output"

# Setup options for available BCGW layers
BCGWLayer = {}
BCGWLayer['aoa'] = 'WHSE_ARCHAEOLOGY.RAAD_AOA_PROVINCIAL'
BCGWLayer['aoa_sites'] = 'WHSE_ARCHAEOLOGY.RAAD_ARCHAEOLOGY_SITES_SVW'
BCGWLayer['bgc'] = 'WHSE_FOREST_VEGETATION.BEC_BIOGEOCLIMATIC_POLY'
BCGWLayer['borden'] = 'WHSE_ARCHAEOLOGY.RAAD_BORDENGRID'
BCGWLayer['cities'] = 'WHSE_BASEMAPPING.DBM_7H_MIL_POPULATION_POINT'
BCGWLayer['crwn_ten'] = 'WHSE_TANTALIS.TA_CROWN_TENURES_SVW'
BCGWLayer['cws'] = 'WHSE_WATER_MANAGEMENT.WLS_COMMUNITY_WS_PUB_SVW'
BCGWLayer['desig_area'] = 'WHSE_ADMIN_BOUNDARIES.FADM_DESIGNATED_AREAS'
BCGWLayer['dra'] = 'WHSE_BASEMAPPING.DRA_DIGITAL_ROAD_ATLAS_LINE_SP'
BCGWLayer['fire_current'] = 'WHSE_LAND_AND_NATURAL_RESOURCE.PROT_CURRENT_FIRE_POLYS_SP'
BCGWLayer['fire_history'] = 'WHSE_LAND_AND_NATURAL_RESOURCE.PROT_HISTORICAL_FIRE_POLYS_SP'
BCGWLayer['fnirs'] = 'WHSE_HUMAN_CULTURAL_ECONOMIC.FNIRS_AGREEMENT_BOUNDARY_SVW'
BCGWLayer['fnta'] = 'WHSE_LEGAL_ADMIN_BOUNDARIES.FNT_TREATY_AREA_SP'
BCGWLayer['fntl'] = 'WHSE_LEGAL_ADMIN_BOUNDARIES.FNT_TREATY_LAND_SP'
BCGWLayer['fsws'] = 'WHSE_WILDLIFE_MANAGEMENT.WCP_FISH_SENSITIVE_WS_POLY'
BCGWLayer['ften_rd'] = 'WHSE_FOREST_TENURE.FTEN_ROAD_LINES'
BCGWLayer['fwa_aws'] = 'WHSE_BASEMAPPING.FWA_ASSESSMENT_WATERSHEDS_POLY'
BCGWLayer['fwa_streams']          = 'WHSE_BASEMAPPING.FWA_STREAM_NETWORKS_SP'
BCGWLayer['fwa_wetlands']          = 'WHSE_BASEMAPPING.FWA_WETLANDS_POLY'
BCGWLayer['gry'] = 'WHSE_FOREST_VEGETATION.GRY_PSP_STATUS_ACTIVE'
BCGWLayer['ir'] = 'WHSE_ADMIN_BOUNDARIES.CLAB_INDIAN_RESERVES'
BCGWLayer['lakes'] = 'WHSE_BASEMAPPING.TRIM_EBM_WATERBODIES'
BCGWLayer['lu'] = 'WHSE_LAND_USE_PLANNING.RMP_LANDSCAPE_UNIT_SVW'
BCGWLayer['mineral_reserve'] = 'WHSE_MINERAL_TENURE.MTA_SITE_SP'
BCGWLayer['ml'] = 'WHSE_FOREST_TENURE.FTEN_MANAGED_LICENCE_POLY_SVW'
BCGWLayer['nrd'] = 'WHSE_ADMIN_BOUNDARIES.ADM_NR_DISTRICTS_SP'
BCGWLayer['nrr'] = 'WHSE_ADMIN_BOUNDARIES.ADM_NR_REGIONS_SP'
BCGWLayer['ogma'] = 'WHSE_LAND_USE_PLANNING.RMP_OGMA_LEGAL_CURRENT_SVW'
BCGWLayer['ogma_nonlegal'] = 'WHSE_LAND_USE_PLANNING.RMP_OGMA_NON_LEGAL_CURRENT_SVW'
BCGWLayer['own'] = 'WHSE_FOREST_VEGETATION.F_OWN'
BCGWLayer['park_conservancy'] = 'WHSE_TANTALIS.TA_CONSERVANCY_AREAS_SVW'
BCGWLayer['park_national'] = 'WHSE_ADMIN_BOUNDARIES.CLAB_NATIONAL_PARKS'
BCGWLayer['park_ecores'] = 'WHSE_TANTALIS.TA_PARK_ECORES_PA_SVW'
BCGWLayer['pvt_cnsrv_lands'] = 'WHSE_LEGAL_ADMIN_BOUNDARIES.WCL_CONSERVATION_LANDS_SP'
BCGWLayer['rec'] = 'WHSE_FOREST_TENURE.FTEN_RECREATION_POLY_SVW'
BCGWLayer['rectrails'] = 'WHSE_FOREST_TENURE.FTEN_RECREATION_LINES_SVW'
BCGWLayer['resproj'] = 'WHSE_FOREST_VEGETATION.RESPROJ_RSRCH_INSTN_GVT_SVW'
BCGWLayer['rfi'] = 'WHSE_FOREST_VEGETATION.REC_FEATURES_INVENTORY'
BCGWLayer['rivers'] = 'WHSE_BASEMAPPING.TRIM_EBM_WATERCOURSES'
BCGWLayer['rmp_legal'] = 'WHSE_LAND_USE_PLANNING.RMP_PLAN_LEGAL_POLY_SVW'
BCGWLayer['rmp_nonlegal'] = 'WHSE_LAND_USE_PLANNING.RMP_PLAN_NON_LEGAL_POLY_SVW'
BCGWLayer['slrp'] = 'WHSE_LAND_USE_PLANNING.RMP_STRGC_LAND_RSRCE_PLAN_SVW'
BCGWLayer['srlp_line'] = 'WHSE_LAND_USE_PLANNING.RMP_PLAN_LEGAL_LINE_SVW'
BCGWLayer['srlp_pnt'] = 'WHSE_LAND_USE_PLANNING.RMP_PLAN_LEGAL_POINT_SVW'
BCGWLayer['ten_rd'] = 'WHSE_FOREST_TENURE.TEN_ROAD'
BCGWLayer['tfl'] = 'WHSE_ADMIN_BOUNDARIES.FADM_TFL'
BCGWLayer['tfl_add'] = 'WHSE_ADMIN_BOUNDARIES.FADM_TFL_ADDITION'
BCGWLayer['tfl_del'] = 'WHSE_ADMIN_BOUNDARIES.FADM_TFL_DELETION'
BCGWLayer['tl'] = 'WHSE_FOREST_TENURE.FTEN_TIMBER_LICENCE_POLY_SVW'
BCGWLayer['trim_trans'] = 'WHSE_BASEMAPPING.TRIM_TRANSPORTATION_LINES'
BCGWLayer['tsp'] = 'WHSE_TERRESTRIAL_ECOLOGY.STE_TER_STABILITY_POLYS_SVW'
BCGWLayer['tsa'] = 'WHSE_ADMIN_BOUNDARIES.FADM_TSA'
BCGWLayer['uwr'] = 'WHSE_WILDLIFE_MANAGEMENT.WCP_UNGULATE_WINTER_RANGE_SP'
BCGWLayer['van_gvrd_ws'] = 'REG_LAND_AND_NATURAL_RESOURCE.WATERSHEDS_GVRD_POLY'
BCGWLayer['vli'] = 'WHSE_FOREST_VEGETATION.REC_VISUAL_LANDSCAPE_INVENTORY'
BCGWLayer['vri'] = 'WHSE_FOREST_VEGETATION.VEG_COMP_LYR_R1_POLY'
BCGWLayer['wetlands'] = 'WHSE_BASEMAPPING.TRIM_EBM_WETLANDS'
BCGWLayer['wha'] = 'WHSE_WILDLIFE_MANAGEMENT.WCP_WILDLIFE_HABITAT_AREA_POLY'
BCGWLayer['wma'] = 'WHSE_TANTALIS.TA_WILDLIFE_MGMT_AREAS_SVW'
BCGWLayer['wtr'] = 'WHSE_FOREST_VEGETATION.RSLT_FOREST_COVER_RESERVE_SVW'

# ============================================================================
# DEFINE FUNCTIONS
# ============================================================================

# ----------------------------------------------------------------------------
def usage():
  print "Usage: extractBCGW [BCGW layer code]\n"

# ----------------------------------------------------------------------------
def help(parametersNeeded, BCGWLayer):
  print "Purpose: extract features from the BCGW clipped to a boundary and output as a GDB feature class\n"
  print "Looks in projectParameters.txt for:"
  for key in sorted(parametersNeeded.keys()):
    print "  %-30s  %s" % (key, parametersNeeded[key])
  print "\n"
  print "Enter one of the following BCGW layer codes as command line argument:"
  print " %-20s   %s" % ("Code","BCGW layer")  
  for key in sorted(BCGWLayer.keys()):
    print " %-20s   %s" % (key, BCGWLayer[key])  

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

# -------------------------------------------------------------
def createTmpConnection(work, tempConnect):

# -------------------------------------------------------------
  # connection parameters
  usr = "dlayden"               # oracle user name
  pw = "Dragon.1808"            # oracle password (enter correct password for user before running
  # pw = getpass.getpass()
  database_platform = "ORACLE"
  instance = "bcgw.bcgov/idwprod1.bcgov"
  authentication = "DATABASE_AUTH"

  # create a temporary connection file
  print work + os.sep + tempConnect
  if arcpy.Exists(work + os.sep + tempConnect):
    arcpy.AddMessage("Temp BCGW connection already exists: ignore create")
  else:
    print usr, pw, database_platform, instance, authentication
    arcpy.AddMessage("Creating connection...")
    arcpy.CreateDatabaseConnection_management (  # revised connection method 2017
      work,               # folder to create the connection
      tempConnect,        # name of connection
      database_platform,  # database_platform (Oracle)
      instance,           # instance
      authentication,     # authentication
      usr,                # username
      pw                  # password
      )

# ----------------------------------------------------------------------------
def extractFeatures(WhseConnection, clipBnd, outFeatureClass, logFile):

  # Process: Make Feature Layer
  gp.AddMessage("Making feature layer for select from %s..." % WhseConnection)
  BCGWObject = "BCGWObject"
  clipLayer = "clipLayer"
  gp.MakeFeatureLayer_management(WhseConnection, BCGWObject)
 
  # Select Layer By Location...
  logMessage(logFile, "Selecting features that intersect with clip boundary...")
  try:
    gp.SelectLayerByLocation_management(BCGWObject, "intersect", clipBnd)
  except:
    logMessage(logFile, gp.GetMessage(2))
    sys.exit(0)

  # create tmp feature class-- otherwise fails for large BCGW layers
  logMessage(logFile, "Creating temporary feature class...")
  scratchGDB = "tmp_extractFromBCGW.gdb"
  if gp.Exists(scratchGDB):
    gp.Delete_management("T:/"+scratchGDB)
  gp.CreateFileGDB_management("T:", scratchGDB)
  scratchFC = "T:"+"/"+scratchGDB+"/tmpFC"
  gp.CopyFeatures_management(BCGWObject,scratchFC)

  # Clip
  logMessage(logFile, "Clipping polygons...")
  try:
    gp.Clip_analysis(scratchFC, clipBnd, outFeatureClass)
  except:
    logMessage(logFile, gp.GetMessage(2))

  # gp.Delete_management("T:/"+scratchGDB)

  gp.env.overwriteOutput = False

# ----------------------------------------------------------------------------
def gpSetup():
  print "Creating the geoprocessor object..."
  gp = arcpy
  # gp.SetProduct("ArcInfo")
  gp.env.overwriteOutput = True
  
  return gp

# ----------------------------------------------------------------------------
def logMessage(logFile, message):
  gp.AddMessage(message)
  logFile.write(message+"\n")

# ----------------------------------------------------------------------------
def elapsedTime(startTime, currentTime):
  elapsed = currentTime - startTime
  hr = int(elapsed/3600)
  min = int((elapsed - hr*3600)/60)
  sec = int(elapsed - hr*3600 - min*60)
  if hr == 0:
    message = "0"
  else:
    message = "%d" % (hr)
  if min > 9:
    message = "%s:%d" % (message,min)
  else:
    message = "%s:0%d" % (message,min)
  if sec > 9:
    message = "%s:%d" % (message,sec)
  else:
    message = "%s:0%d" % (message,sec)
  return message

# ----------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------

# check if the script was invoked from the command line or toolbox
#   command line    two arguments, the rest are read from parameterFileName
#   toolbox         four arguments
if len(sys.argv) < 4:
  fromCommandLine = 1
else:
  fromCommandLine = 0

# --------------------------------------------------------------------------
# initialization differs if invoked from command line or tool box
# --------------------------------------------------------------------------

if fromCommandLine:

  fromCommandLine = 1

  # --------------------------------------------------------------------------
  # called from command line
  #
  # startup checking and initialization
  #  1. usage
  #  2. help
  #  3. set BCGW layer code from system argument (only 1 argument)
  #  4. get defaults from parameter file
  #  5. set local variables
  # --------------------------------------------------------------------------

  # usage
  if len(sys.argv) < 2:
    usage()
    print  "Enter extractFromBCGW --h for help"
    sys.exit(0)
  
  # help
  if string.lower(sys.argv[1]) == "--h":
    usage()
    help(parametersNeeded, BCGWLayer)
    sys.exit()

  # system arguments
  layerCode = sys.argv[1]
  
  # validate option
  foundLayer = 0
  for key in BCGWLayer.keys():
    if layerCode == key:
      foundLayer = 1
  if foundLayer == 0:
    print "ERROR: option %s is not valid\n" % (layerCode)
    usage()
    help(parametersNeeded, BCGWLayer)
    sys.exit(0)

  # get project parameters from file
  getProjectParameters(parameterFileName, parameters, parametersNeeded)
  databaseConnection = parameters["databaseConnection"]
  managementUnitBoundary = parameters["managementUnitBoundary"]
  workspaceWrk = parameters["workspaceWrk"]
  workspaceSrc = parameters["workspaceSrc"]

  # local variables
  BCGWLayerName = BCGWLayer[layerCode]
  outName = BCGWLayerName.split(".")[1]
  clipBnd = workspaceWrk+"/"+managementUnitBoundary
  outFeatureClass = workspaceSrc+"/"+outName
  WhseConnection = "T:/"+databaseConnection+".sde/" + BCGWLayerName

else:

  # --------------------------------------------------------------------------
  # called from toolbox
  #
  # initialization
  #  1. set local variables using system arguments
  #  2. check/set default output feature class name
  # --------------------------------------------------------------------------

  # Get script arguments (Required vs Optional and defaults are set as dialog properties)
  WhseConnection = sys.argv[1]     # database connection to selected BCGW feature layer
  clipBnd = sys.argv[2]     # Clipping layer
  outWorkspace = sys.argv[3]     # Output dataset
  outName = sys.argv[4]     # Output feature class (Default: Default)

  # check if default outName
  #   if default parse WhseConnection to get BCGWObject
  #   otherwise use sys.argv

  BCGWLayerName = WhseConnection[string.find(WhseConnection,"WHSE"):len(WhseConnection)]
  if outName == "Default (only from BCGW)":
    outName = BCGWLayerName.split(".")[1]

  # other local variables
  outFeatureClass = outWorkspace+"/"+outName

# ------------------------------------------------------------------------
# finished initialization
# ------------------------------------------------------------------------

# local variables
logFileName = "T:/extractFromBCGW.log"
logFile = file(logFileName, "w")

# doit
gp = gpSetup()
print 'gp created...'

if fromCommandLine:                                                                                        
  print databaseConnection
  createTmpConnection("T:", databaseConnection)

# note input and output layers
logMessage(logFile, "======================================================================")
logMessage(logFile, "Connection %s" % WhseConnection)
logMessage(logFile, "Extracting %s" % BCGWLayerName)
logMessage(logFile, "Clipped to %s" % clipBnd)
logMessage(logFile, "To create  %s" % outFeatureClass)
logMessage(logFile, "Logfile    %s" % logFileName)
logMessage(logFile, "======================================================================")
logMessage(logFile, time.asctime(time.localtime()))

# passed all startup checks
startTime = time.time()

if gp.Exists(outFeatureClass):
  gp.AddMessage("WARNING: feature class %s already exists...skipping" % (outFeatureClass))
  sys.exit(0)
extractFeatures(WhseConnection, clipBnd, outFeatureClass,logFile)

# ------------------------------------------------------------------------
# finished
# ------------------------------------------------------------------------
logMessage(logFile, "Elapsed time %s" % (elapsedTime(startTime, time.time())))
logMessage(logFile, time.asctime(time.localtime()))
del logFile
