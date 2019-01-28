import sys

# get ready to import local modules
# define the path to the modules and append it to the system path
module_path = '//spatialfiles2.bcgov/work/FOR/VIC/HTS/ANA/Workarea/TOOLS/python/PythonLib/Production'
# module_path = 'C:/Data/training_201806/python/lib'
sys.path.append(module_path)

# continue importing modules
import FAIB_Tools as faib
import os,time
from osgeo import gdal, ogr

# usage
if len(sys.argv) < 3:
  print "Usage: python rasterize_postgres2tiff.py [res_table] [attribute_name|attribute_name_number]"
  sys.exit(0)

# commandline argument
resName = sys.argv[1]
attr = sys.argv[2]

# FAIB parameters
parameterFileName = "projectParameters.txt"
parameters = {}
parametersNeeded = {}
parametersNeeded["managementUnit"] = "Management Unit/project prefix"
parametersNeeded["workspace"] = "GDB workspace"
parametersNeeded["managementUnitBoundary"] = "project boundary layer in GDB"
parametersNeeded["pixel_size"] = "raster pixel_size in metres"
parametersNeeded["tiffPath"] = "path to folder where TIFF files are stored"
parametersNeeded["DEBUG"] = "DEBUG = True or False"
faib.getProjectParameters(parameterFileName, parameters, parametersNeeded)

# local variables
managementUnit = parameters["managementUnit"]
workspace = parameters["workspace"]
pixel_size = int(parameters["pixel_size"])
tiffPath = parameters["tiffPath"]
if (parameters["DEBUG"] == 'False'):
  DEBUG = False
else:
  DEBUG = True
logFileName = managementUnit+'_rasterize_postgres2tiff_'+attr+'.log'
logFile = file(logFileName, "w")
dstFile =  tiffPath + "/" + managementUnit + "_" + attr + ".tif" # Filename of the raster Tiff that will be created
managementUnitBoundary = parameters["managementUnitBoundary"] # for calculating extents
res = "%s_%s" % (managementUnit,resName)

# ==============================================================================
# main
# ==============================================================================

message = 'start  %s %s' % (time.ctime(), logFileName)
faib.logMessage(logFile, message,DEBUG)
if not DEBUG:
  print message

# Open the managementUnitBoundary
referenceData = ogr.Open(workspace)
if referenceData == None:
	print "ERROR rasterize_postgres2tiff: failed to open %s" % (workspace)
	sys.exit()
referenceLayer = referenceData.GetLayer(managementUnitBoundary)
if referenceLayer == None:
	print "ERROR rasterize_postgres2tiff: layer %s not found in %s" % (managementUnitBoundary,workspace)
	sys.exit()

# get refLayer extent
referenceSrs = referenceLayer.GetSpatialRef()
x_min, x_max, y_min, y_max = referenceLayer.GetExtent()

raster_x_min, raster_y_min, raster_x_max, raster_y_max = faib.calcRasterExtents(x_min, y_min, x_max, y_max, pixel_size,logFile)

if not os.path.exists(tiffPath):
  os.makedirs(tiffPath)
if os.path.exists(dstFile):
  os.remove(dstFile)
  faib.logMessage(logFile, 'remove TIFF file',DEBUG)
cmd = "gdal_rasterize PG:\"dbname=\'postgres\' user=\'postgres\'\" -l " + res + " -a " + attr + " -ot Int32 -te " \
      + str(raster_x_min) + " " + str(raster_y_min) + " " + str(raster_x_max) + " " + str(raster_y_max) + \
      " -tr " + str(pixel_size) + " " + str(pixel_size) + " -a_srs epsg:3005 " + dstFile
faib.logMessage(logFile, cmd,DEBUG)
try:
  os.system(cmd)
except:
	message = 'ERROR rasterize_postgres2tiff: does the postgres table have geometry? See join_geometry2resultants.sql'
	faib.logMessage(logFile, cmd,message)
	if not DEBUG:
		print message

message = 'finish %s %s' % (time.ctime(), logFileName)
faib.logMessage(logFile, message,DEBUG)
if not DEBUG:
  print message

