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
  print "Usage: rasterize_gdb2tiff.py [GDB_layer] [column_name]"
  sys.exit(0)

# system arguments
gdbLayer = sys.argv[1]
col_name = sys.argv[2]

# FAIB parameters
parameterFileName = "projectParameters.txt"
parameters = {}
parametersNeeded = {}
parametersNeeded["managementUnit"] = "Management Unit/project prefix"
parametersNeeded["workspace"] = "GDB workspace"
parametersNeeded["managementUnitBoundary"] = "project boundary layer in GDB"
parametersNeeded["pixel_size"] = "raster pixel_size in metres"
parametersNeeded["tiffPath"] = "path to folder where TIFF files are stored"
# parametersNeeded["DEBUG"] = "DEBUG = True or False"
faib.getProjectParameters(parameterFileName, parameters, parametersNeeded)

# Set the data source
managementUnit = parameters["managementUnit"]
workspace = parameters["workspace"]
pixel_size = int(parameters["pixel_size"])
tiffPath = parameters["tiffPath"]
if (parameters["DEBUG"] == 'False'):
  DEBUG = False
else:
  DEBUG = True
logFileName = managementUnit+'_rasterize_gdb2tiff_'+gdbLayer+'.log'
logFile = file(logFileName, "w")
dstFile =  tiffPath + "/" + managementUnit + "_" + col_name + ".tif" # Filename of the raster Tiff that will be created
refLayer = parameters["managementUnitBoundary"] # for calculating extents
       
# ==============================================================================
if __name__ == '__main__':

  message = 'start  %s %s' % (time.ctime(), logFileName)
  faib.logMessage(logFile, message,DEBUG)
  if not DEBUG:
    print message

  # create TIFF folder if necessary
  if not os.path.exists(tiffPath):
    os.makedirs(tiffPath)

  # delete output TIFF file if necessary
  if os.path.exists(dstFile):
    os.remove(dstFile)

  faib.logMessage(logFile, "Creating %s..." % (dstFile),DEBUG)
  faib.rasterizeGBDlayer2TIFF(workspace,gdbLayer,refLayer,col_name,dstFile,pixel_size,logFile)

  message = 'finish %s %s' % (time.ctime(), logFileName)
  faib.logMessage(logFile, message,DEBUG)
  if not DEBUG:
    print message
