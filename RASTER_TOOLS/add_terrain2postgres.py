import sys

# get ready to import local modules
# define the path to the modules and append it to the system path
module_path = '//spatialfiles2.bcgov/work/FOR/VIC/HTS/ANA/Workarea/TOOLS/python/PythonLib/Production'
# module_path = 'C:/Data/training_201806/python/lib'
sys.path.append(module_path)

# continue importing modules
import FAIB_Tools as faib
import os, time, struct
import psycopg2, cStringIO
from osgeo import gdal, ogr, osr

# usage
usage = "Usage: add_terrain2postgres.py [slope|elevation]"
if len(sys.argv) < 2:
  print usage
  sys.exit(0)

# system arguments
terrain_type = sys.argv[1]
if (terrain_type != 'slope' and terrain_type != 'elevation'):
  print 'Terrain type %s not valid' % (terrain_type)
  print usage
  sys.exit(0)


# FAIB parameters
parameterFileName = "projectParameters.txt"
parameters = {}
parametersNeeded = {}
parametersNeeded["workspace"] = "GDB workspace"
parametersNeeded["managementUnit"] = "Management Unit/project prefix"
parametersNeeded["managementUnitBoundary"] = "project boundary layer in GDB"
parametersNeeded["pixel_size"] = "raster pixel size in metres"
parametersNeeded["tiffPath"] = "path to folder where TIFF files are stored"
parametersNeeded["DEBUG"] = "DEBUG = True or False"
faib.getProjectParameters(parameterFileName, parameters, parametersNeeded)

# local variables
managementUnit = parameters["managementUnit"]
workspace = parameters["workspace"]
refLayer = parameters["managementUnitBoundary"] # for calculating extents
pixel_size = float(parameters["pixel_size"])
tiffPath = parameters["tiffPath"]
if (parameters["DEBUG"] == 'False'):
  DEBUG = False
else:
  DEBUG = True
logFileName = managementUnit+'_add_terrain2postgres_' + terrain_type + '.log'
logFile = file(logFileName, "w")
clippedTIFF = tiffPath + "/" + managementUnit + "_clip_" + terrain_type + ".tif"
tableName = managementUnit + '_' + terrain_type
dst_fieldname = terrain_type
maskband = None

# choose terrain TIFF to clip from
if pixel_size == 100:
  srcDataset = "//spatialfiles2.bcgov/archive/FOR/VIC\HTS/ANA/workarea/PROVINCIAL/topography." + terrain_type + ".tif"
elif pixel_size == 400:
  srcDataset = "//spatialfiles2.bcgov/archive/FOR/VIC\HTS/ANA/workarea/PROVINCIAL/bc_16ha_" + terrain_type + ".tif"
else:
  message = 'Error provincial terrain not available for pixel size %d' % int(pixel_size)
  faib.logMessage(logFile, message,DEBUG)
  print message
  sys.exit(1)

# ----------------------------------------------------------------------------
def readRasterValues(tiffFileName):
    
  dataset = gdal.Open(tiffFileName)
  band = dataset.GetRasterBand(1)

  #Reading the raster properties
  xsize = band.XSize
  ysize = band.YSize
  datatype = band.DataType
  if DEBUG:
    faib.logMessage(logFile, "raster properties %d %d %d %d" % (xsize, ysize, xsize*ysize, datatype))

  #Read the raster values as packed binary
  rasterData = band.ReadRaster( 0, 0, xsize, ysize, xsize, ysize, datatype )

  #Conversion between GDAL types and python pack types (Can't use complex integer or float!!)
  data_types ={'Byte':'B','UInt16':'H','Int16':'h','UInt32':'I','Int32':'i','Float32':'f','Float64':'d'}
  rasterData = struct.unpack(data_types[gdal.GetDataTypeName(band.DataType)]*xsize*ysize,rasterData)

  return rasterData

# ======================================================================
def convertToFileLikeObject(structToConvert):

  output = cStringIO.StringIO()
  faib.logMessage(logFile, "number of rows to convert to FLO %d" %len(structToConvert),DEBUG)
  for row in range(len(structToConvert)):
    output.write("%s\t%s\n" % (row + 1, structToConvert[row]))
        
  # rewind
  output.seek(0)

  return output

# ======================================================================
def createPsqlTable(table,layer,conn):
    
  if conn:
    cur = conn.cursor()
    stmt = "drop table if exists %s" % (table)
    cur.execute(stmt)

    stmt = "create table " + table + "(ogc_fid serial," + layer + " integer);"
    cur.execute(stmt)

    conn.commit()
    cur.close()

# ======================================================================
def copyToPsqlTable(data,table,conn):
  cursor = conn.cursor()
  cursor.copy_from(data,table)

  conn.commit()
  cursor.close()

# ================================================================================
# main
# ================================================================================

message = 'start  %s %s' % (time.ctime(), logFileName)
faib.logMessage(logFile, message,DEBUG)
print message

# log some of the input parameters
faib.logMessage(logFile, 'reference_GDB_layer: %s' % refLayer,DEBUG)
faib.logMessage(logFile, 'pixel_size: %d' % int(pixel_size),DEBUG)
faib.logMessage(logFile, 'source terrain TIFF: %s' % srcDataset,DEBUG)

# --------------------------------------------------------------------------------
# clip provincial terrain to management unit boundary
# --------------------------------------------------------------------------------

message = "%s creating table %s..." % (time.ctime(),tableName)
faib.logMessage(logFile, message,DEBUG)

# Open the data source
sourceData = ogr.Open(workspace)
sourceLayer = sourceData.GetLayer(refLayer)
	
# get raw extents
x_min, x_max, y_min, y_max = sourceLayer.GetExtent()
faib.logMessage(logFile, 'raw: x_min %f  x_max %f  y_min %f  y_max %f' % (x_min, x_max, y_min, y_max),DEBUG)
rast_x_min, rast_y_min, rast_x_max, rast_y_max = faib.calcRasterExtents(x_min, y_min, x_max, y_max,pixel_size,logFile)

# gdal_tranlate uses ulx, uly ,lrx,lry
# as opposed to xmin,ymin,xmax,ymax
cmd = "gdal_translate.exe -quiet -projwin %.1f %.1f %.1f %.1f -of GTiff %s %s" % (rast_x_min,rast_y_max,rast_x_max,rast_y_min,srcDataset,clippedTIFF)
faib.logMessage(logFile,cmd,DEBUG)
os.system(cmd)

# --------------------------------------------------------------------------------
# mask clipped terrain to management unit boundary
# --------------------------------------------------------------------------------

faib.logMessage(logFile, 'Converting values to FileLikeObject...',DEBUG)
values = readRasterValues(clippedTIFF)
FLO_values = convertToFileLikeObject(values)

# check if table exists
try:
  dst_layer = dst_ds.GetLayerByName(tableName)
except:
  dst_layer = None

# create postgres connection
connection = psycopg2.connect("dbname=postgres user=postgres")
cursor = connection.cursor()

# if table doesn't exist, create it
if dst_layer is None:
  createPsqlTable(tableName,dst_fieldname,connection)
  copyToPsqlTable(FLO_values,tableName,connection)
else :
  # delete
  dst_ds.DeleteLayer(tableName)
  # create
  createPsqlTable(tableName,dst_fieldname,connection)
  copyToPsqlTable(FLO_values,tableName,connection)

# --------------------------------------------------------------------------------
# done
# --------------------------------------------------------------------------------

message = 'finish %s %s' % (time.ctime(), logFileName)
faib.logMessage(logFile, message,DEBUG)
print message
