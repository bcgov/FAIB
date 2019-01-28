# Load tiff data structure (array) to postgresql
# Create a table with 2 columns, column 1 being the ogc_fid, the second being [layer]_fid

import sys

# get ready to import local modules
# define the path to the modules and append it to the system path
module_path = '//spatialfiles2.bcgov/work/FOR/VIC/HTS/ANA/Workarea/TOOLS/python/PythonLib/Production'
# module_path = 'C:/Data/training_201806/python/lib'
sys.path.append(module_path)

# continue importing modules
import FAIB_Tools as faib
import time
import struct, psycopg2, cStringIO
from osgeo import gdal

gdal.AllRegister()

# usage
if len(sys.argv) < 2:
  print "Usage: load_tiff2postgres.py [tiff_name]"
  sys.exit(0)

# system arguments
layer = sys.argv[1]

# FAIB parameters
parameterFileName = "projectParameters.txt"
parameters = {}
parametersNeeded = {}
parametersNeeded["managementUnit"] = "management unit"
parametersNeeded["tiffPath"] = "path to folder where TIFF files are stored"
# parametersNeeded["DEBUG"] = "DEBUG = True or False"
faib.getProjectParameters(parameterFileName, parameters, parametersNeeded)

# local variables	
managementUnit = parameters["managementUnit"]
tiffPath = parameters["tiffPath"]
if (parameters["DEBUG"] == 'False'):
  DEBUG = False
else:
  DEBUG = True
tiff_file = tiffPath + "/" + managementUnit + "_" + layer + ".tif"
pg_table = managementUnit + "_" + layer
logFileName = managementUnit+'_load_tiff2postgis_'+layer+'.log'
logFile = file(logFileName, "w")

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
  if (DEBUG):
    faib.logMessage(logFile, "number of rows to convert to FLO %d" %len(structToConvert))
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

# ======================================================================
if __name__ == '__main__':

  print 'start  ', time.ctime(), logFileName

  if DEBUG:
    faib.logMessage(logFile, time.ctime())
    faib.logMessage(logFile, "Reading values from %s..." % (tiff_file))
  values = readRasterValues(tiff_file)

  if DEBUG:
    faib.logMessage(logFile, 'Converting values to FileLikeObject...')
  FLO_values = convertToFileLikeObject(values)

  if DEBUG:
    faib.logMessage(logFile, 'Loading values to PostgreSQL...')
  connection = psycopg2.connect("dbname=postgres user=postgres")
  cursor = connection.cursor()
  createPsqlTable(pg_table,layer,connection)
  copyToPsqlTable(FLO_values,pg_table,connection)

  if DEBUG:
    faib.logMessage(logFile, time.ctime())

  print 'finish ', time.ctime(), logFileName
