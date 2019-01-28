# ================================================================================
# NAME:
#    mkResultants.py
#
# FUNCTION:
#   - open a spreadsheet containing database of wrk feature classes and fields
#     and "overlay" the feature class Postgres tables
#
# HISTORY:
#   20160314 Doug Layden -- original coding from mkSrc2WrkScripts10.py
#   201609   Doug Layden -- converted to psycopg execution of sql statements
#   20170810 Doug Layden -- re-designed to included rasterizization of FCs
#                           and loading of Postgres tables
#   20180201 Doug Layden -- sys args to enter starting res and ending res name
#
# ================================================================================

import sys

# get ready to import local modules
# define the path to the modules and append it to the system path
module_path = '//spatialfiles2.bcgov/work/FOR/VIC/HTS/ANA/Workarea/TOOLS/python/PythonLib/Production'
sys.path.append(module_path)

# continue importing modules
import FAIB_Tools as faib
import string, os, time
import struct, psycopg2, cStringIO
from osgeo import gdal, ogr
from win32com.client import Dispatch

# usage
if len(sys.argv) < 3:
  print "Usage: mkresultants.py [starting_res_table] [ending_res_table]"
  print "\nCAUTION: will overwrite [ending_res_table]"
  sys.exit(0)
  
# system arguments
res_start = sys.argv[1]
res_end = sys.argv[2]
	
# ============================================================================
# hardcoded values
# ============================================================================
parameterFileName = "projectParameters.txt"
parameters = {}
parametersNeeded = {}
parametersNeeded["DEBUG"] = "DEBUG = True or False"
parametersNeeded["dataDictionary"] = "project data dictionary"
parametersNeeded["managementUnit"] = "Management Unit/project prefix"
parametersNeeded["managementUnitBoundary"] = "project boundary layer in GDB"
parametersNeeded["pixel_size"] = "raster pixel_size inmetres"
parametersNeeded["resTab"] = "resTab in data dictionary"
parametersNeeded["tiffPath"] = "path to folder where TIFF files are stored"
parametersNeeded["workspace"] = "GDB workspace"
faib.getProjectParameters(parameterFileName, parameters, parametersNeeded)

# --------------------------------------------------------------------------------
# local variables
# --------------------------------------------------------------------------------
workspace = parameters["workspace"]
workspaceWrk = parameters["workspaceWrk"]
managementUnit = parameters["managementUnit"]
pixel_size = int(parameters["pixel_size"])
tiffPath = parameters["tiffPath"]
dataDictionary = parameters["dataDictionary"]
worksheetName = parameters["resTab"]
refLayer = parameters["managementUnitBoundary"] # for calculating extents
if (parameters["DEBUG"] == 'False'):
  DEBUG = False
else:
  DEBUG = True
res_start = managementUnit + '_' + res_start
res_end= managementUnit + '_' + res_end
logFileName = managementUnit+'_mkResultants.log'
logFile = file(logFileName, "w")
row_origin = 1
col_origin = 1

# --------------------------------------------------------------------------------
def readRow(row,col_origin):
  wrkFeatureClass = worksheet.Cells(row,col_origin + 3).Value	
  wrkShortName = worksheet.Cells(row,col_origin + 5).Value
  return wrkFeatureClass,wrkShortName

# ------------------------------------------------------------------------------
def rasterizeGBD2TIFF(gdbFile,gdbLayer,refLayer,col_name,dstFile,pixel_size,noDataValue=-99):

	# Open the data source
	sourceData = ogr.Open(gdbFile)
	if sourceData == None:
		print "Failed to open %s" % (gdbFile)
		sys.exit()
	sourceLayer = sourceData.GetLayer(str(gdbLayer))
	if sourceLayer == None:
		print "Layer %s not found in %s" % (gdbLayer,gdbFile)
		sys.exit()
	sourceSrs = sourceLayer.GetSpatialRef()

	referenceLayer = sourceData.GetLayer(refLayer)
	if referenceLayer == None:
		faib.logMessage(logFile, "Layer %s not found in %s" % (refLayer,gdbFile))
		sys.exit()

	#define extent
	x_min, x_max, y_min, y_max = referenceLayer.GetExtent()
	raster_x_min, raster_y_min, raster_x_max, raster_y_max = faib.calcRasterExtents(x_min, y_min, x_max, y_max, pixel_size,logFile)
	x_res = int((raster_x_max - raster_x_min) / float(pixel_size))
	y_res = int((raster_y_max - raster_y_min) / float(pixel_size))

	faib.logMessage(logFile, "pixel size %d "% pixel_size,DEBUG)
	faib.logMessage(logFile, "pixels %d %d %d" % (x_res, y_res, x_res*y_res),DEBUG)
	faib.logMessage(logFile, "x_min   x_max   y_min   y_max",DEBUG)
	faib.logMessage(logFile, '%f %f %f %f' % (x_min, x_max, y_min, y_max),DEBUG)
	faib.logMessage(logFile, '%.1f %.1f %.1f %.1f' % (raster_x_min, raster_x_max, raster_y_min, raster_y_max),DEBUG)


	# Create the destination data source
	numLayers = 1
	target_ds = gdal.GetDriverByName('GTiff').Create(dstFile, x_res, y_res, numLayers, gdal.GDT_Int32)
	
	# geotransform defines the relation between the raster coordinates x, y and the geographic coordinates
	rotation = 0
	target_ds.SetGeoTransform((raster_x_min, pixel_size, rotation, raster_y_max, rotation, -pixel_size))
	
	# set projection
	target_ds.SetProjection(sourceSrs.ExportToWkt())
	
	# set no data value
  # actually will set to no data not the value -99
	band = target_ds.GetRasterBand(1)
	band.SetNoDataValue(noDataValue)
	band.Fill(noDataValue)

	# define sequence of bands to use
	bandList = [1]  # note that this is a sequence type in python 
	
	# Rasterize by specified attribute
	option = 'ATTRIBUTE=' + col_name
	faib.logMessage(logFile, "Processing %s: %s" % (gdbLayer,option),DEBUG)

	err = gdal.RasterizeLayer(target_ds, bandList , sourceLayer, options=[option])
		
	if err != 0:
		raise Exception("error rasterizing layer: %s" % err)
        
# ----------------------------------------------------------------------------
def readRasterValues(tiffFileName):
    
  dataset = gdal.Open(tiffFileName)
  band = dataset.GetRasterBand(1)

  #Reading the raster properties
  xsize = band.XSize
  ysize = band.YSize
  datatype = band.DataType
  faib.logMessage(logFile, "raster properties %d %d %d %d" % (xsize, ysize, xsize*ysize, datatype),DEBUG)

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

    stmt = "create table " + table + "(ogc_fid serial," + layer + "_fid integer);"
    cur.execute(stmt)

    conn.commit()
    cur.close()

# ======================================================================
def copyToPsqlTable(data,table,conn):
  cursor = conn.cursor()
  cursor.copy_from(data,table)

  conn.commit()
  cursor.close()



# ------------------------------------------------------------------------------
def load_gdb2postgis_attr_tmp(managementUnit,workspace,gdbLayer):

  connection = psycopg2.connect("dbname=postgres user=postgres")
  cursor = connection.cursor()

  if DEBUG:
    cmd = 'ogr2ogr -lco SPATIAL_INDEX=NO -f "PostgreSQL" PG:"dbname=postgres user=postgres" %s %s -overwrite -progress' % (workspace,gdbLayer)
  else:
    cmd = 'ogr2ogr -lco SPATIAL_INDEX=NO -f "PostgreSQL" PG:"dbname=postgres user=postgres" %s %s -overwrite' % (workspace,gdbLayer)
  faib.logMessage(logFile, cmd,DEBUG)
  os.system(cmd)

  stmt = 'alter table %s drop constraint if exists %s_pkey;' % (gdbLayer,gdbLayer)
  faib.logMessage(logFile, stmt,DEBUG)
  cursor.execute(stmt)
  connection.commit()

  # stmt = 'alter table %s alter column objectid drop NOT NULL;' % (gdbLayer)
  # faib.logMessage(logFile, stmt,DEBUG)
  # cursor.execute(stmt)
  # connection.commit()

  stmt = "drop table if exists %s_%s_attr_tmp;" % (managementUnit,gdbLayer)
  faib.logMessage(logFile, stmt,DEBUG)
  cursor.execute(stmt)

  stmt = "alter table %s rename to %s_%s_attr_tmp;" % (gdbLayer,managementUnit,gdbLayer)
  faib.logMessage(logFile, stmt,DEBUG)
  cursor.execute(stmt)

  stmt = "alter table %s_%s_attr_tmp drop column if exists wkb_geometry;" % (managementUnit,gdbLayer)
  faib.logMessage(logFile, stmt,DEBUG)
  cursor.execute(stmt)

  stmt = "drop sequence if exists %s_objectid_seq cascade;" % (gdbLayer)
  faib.logMessage(logFile, stmt,DEBUG)
  cursor.execute(stmt)

  connection.commit()

  cursor.close()
  connection.close()

# ------------------------------------------------------------------------------
def createTmpOverlay(managementUnit,wrkFeatureClass,step1,res_start):
  connection = psycopg2.connect("dbname=postgres user=postgres")
  cursor = connection.cursor()

  sql_statement = 'drop table if exists %s_tmp;' % (managementUnit)
  faib.logMessage(logFile, sql_statement,DEBUG)
  cursor.execute(sql_statement)

  faib.logMessage(logFile, 'Indexing...',DEBUG)
  sql_statement = 'drop index if exists indx1;'
  cursor.execute(sql_statement)

  sql_statement = 'drop index if exists indx2;'
  cursor.execute(sql_statement)

  if (step1 == 0):
    sql_statement = 'create index indx1 on %s(ogc_fid);' % (res_start)
    cursor.execute(sql_statement)
  else:
    sql_statement = 'create index indx1 on %s_res_%d(ogc_fid);' % (managementUnit,step1)
    cursor.execute(sql_statement)

  sql_statement = 'create index indx2 on %s_%s_tiff_tmp(ogc_fid);' % (managementUnit,wrkFeatureClass)
  cursor.execute(sql_statement)

  connection.commit()

  faib.logMessage(logFile, time.ctime(),DEBUG)

  if (step1 == 0):
    sql_statement = 'create table %s_tmp as' % (managementUnit)
    sql_statement = sql_statement + ' select a.*, b.%s_fid' % (wrkFeatureClass)
    sql_statement = sql_statement + ' from %s a' % (res_start)
    sql_statement = sql_statement + ' left join %s_%s_tiff_tmp b using(ogc_fid);' % (managementUnit,wrkFeatureClass)
    faib.logMessage(logFile, sql_statement,DEBUG)
    cursor.execute(sql_statement)
    connection.commit()
  else:
    sql_statement = 'create table %s_tmp as' % (managementUnit)
    sql_statement = sql_statement + ' select a.*, b.%s_fid' % (wrkFeatureClass)
    sql_statement = sql_statement + ' from %s_res_%d a' % (managementUnit,step1)
    sql_statement = sql_statement + ' left join %s_%s_tiff_tmp b using(ogc_fid);' % (managementUnit,wrkFeatureClass)
    faib.logMessage(logFile, sql_statement,DEBUG)
    cursor.execute(sql_statement)
    connection.commit()

  sql_statement = 'drop index if exists indx1;'
  cursor.execute(sql_statement)

  sql_statement = 'drop index if exists indx2;'
  cursor.execute(sql_statement)

  connection.commit()

  cursor.close()
  connection.close()

  return

# ------------------------------------------------------------------------------
def resultantsOverlay(managementUnit,wrkFeatureClass,fieldMapping,step2):

  connection = psycopg2.connect("dbname=postgres user=postgres")
  cursor = connection.cursor()

  sql_statement = 'drop table if exists %s_res_%d;' % (managementUnit,step2)
  faib.logMessage(logFile, sql_statement,DEBUG)
  cursor.execute(sql_statement)

  sql_statement = 'alter table %s_%s_attr_tmp drop column if exists wkb_geometry;' % (managementUnit,wrkFeatureClass)
  faib.logMessage(logFile, sql_statement,DEBUG)
  cursor.execute(sql_statement)
  connection.commit()

  connection.commit()

  faib.logMessage(logFile, 'Indexing...',DEBUG)
  sql_statement = 'drop index if exists indx3;'
  cursor.execute(sql_statement)

  sql_statement = 'drop index if exists indx4;'
  cursor.execute(sql_statement)

  sql_statement = 'create index indx3 on %s_tmp(%s_fid);' % (managementUnit,wrkFeatureClass)
  cursor.execute(sql_statement)

  sql_statement = 'create index indx4 on %s_%s_attr_tmp(%s_fid);' % (managementUnit,wrkFeatureClass,wrkFeatureClass)
  cursor.execute(sql_statement)

  connection.commit()

  faib.logMessage(logFile, time.ctime(),DEBUG)

  sql_statement = 'explain'
  sql_statement = sql_statement + ' select a.*,%s from %s_tmp a left join %s_%s_attr_tmp b using(%s_fid);' % (fieldMapping,managementUnit,managementUnit,wrkFeatureClass,wrkFeatureClass)
  faib.logMessage(logFile, sql_statement,DEBUG)
  # cursor.execute(sql_statement)
  # explain_results = cursor.fetchall()
  # for line in explain_results:
  #   print line[0]
  # connection.commit()

  sql_statement = 'create table %s_res_%d as' % (managementUnit,step2)
  sql_statement = sql_statement + ' select a.*,%s from %s_tmp a left join %s_%s_attr_tmp b using(%s_fid);' % (fieldMapping,managementUnit,managementUnit,wrkFeatureClass,wrkFeatureClass)
  faib.logMessage(logFile, sql_statement,DEBUG)
  cursor.execute(sql_statement)
  connection.commit()

  sql_statement = 'drop index if exists indx3;'
  cursor.execute(sql_statement)

  sql_statement = 'drop index if exists indx4;'
  cursor.execute(sql_statement)

  connection.commit()

  step = step2-1
  if step > 0:
    sql_statement = 'drop table if exists %s_res_%d;' % (managementUnit,step)
    faib.logMessage(logFile, sql_statement,DEBUG)
    cursor.execute(sql_statement)
  connection.commit()

  cursor.close()
  connection.close()

  return

# ------------------------------------------------------------------------------
def trailer(managementUnit,step2,res_end,DEBUG):
  connection = psycopg2.connect("dbname=postgres user=postgres")
  cursor = connection.cursor()

  sql_statement = 'drop table if exists %s_tmp;' % (managementUnit)
  faib.logMessage(logFile, sql_statement,DEBUG)
  cursor.execute(sql_statement)

  sql_statement = 'drop table if exists %s;' % (res_end)
  faib.logMessage(logFile, sql_statement,DEBUG)
  cursor.execute(sql_statement)

  sql_statement = 'alter table %s_res_%d rename to %s;' % (managementUnit,step2,res_end)
  faib.logMessage(logFile, sql_statement,DEBUG)
  cursor.execute(sql_statement)

  connection.commit()

  cursor.close()
  connection.close()

  return

# --------------------------------------------------------------------------------
def dropTables(managementUnit,wrkFeatureClass,logFile):
  connection = psycopg2.connect("dbname=postgres user=postgres")
  cursor = connection.cursor()

  sql_statement = 'drop table if exists %s_%s_tiff_tmp;' % (managementUnit,wrkFeatureClass)
  faib.logMessage(logFile, sql_statement,DEBUG)
  cursor.execute(sql_statement)

  sql_statement = 'drop table if exists %s_%s_attr_tmp;' % (managementUnit,wrkFeatureClass)
  faib.logMessage(logFile, sql_statement,DEBUG)
  cursor.execute(sql_statement)

  connection.commit()

  cursor.close()
  connection.close()

# --------------------------------------------------------------------------------
# add to field mapping variable
# --------------------------------------------------------------------------------
def setfieldMapping(fieldMapping,wrkShortName):

  if fieldMapping:
    fieldMapping = '%s, b.%s' % (fieldMapping,wrkShortName)
  else:
    fieldMapping = 'b.%s' % (wrkShortName)

  return fieldMapping

# ----------------------------------------------------------------------------
def validateLayersError(managementUnit,worksheet):
  connection = psycopg2.connect("dbname=postgres user=postgres")
  cursor = connection.cursor()

  overlayCount = 0

  # first row
  row = row_origin + 1   # skip header row
  wrkFeatureClass,wrkShortName = readRow(row,col_origin)
  cursor.execute("select exists(select * from information_schema.tables where table_name=%s_%s_attr_tmp)" % (managementUnit,wrkFeatureClass))

  err = 0
  while wrkFeatureClass:
    overlayCount = overlayCount + 1
    row = row + 1
    wrkFeatureClass,wrkShortName = readRow(row,col_origin)
    cursor.execute("select exists(select * from information_schema.tables where table_name=%s_%s_attr_tmp)" % (managementUnit,wrkFeatureClass))

  return err

# ============================================================================
# MAIN
# ============================================================================

message = 'start  %s %s' % (time.ctime(), logFileName)
faib.logMessage(logFile, message,DEBUG)
if not DEBUG:
  print message

# --------------------------------------------------------------------------------
# Check if arguments valid
# --------------------------------------------------------------------------------

# validate dataDictionary
if not os.path.isfile(dataDictionary):
  faib.logMessage(logFile, "Data dictionary %s not found" % dataDictionary)
  sys.exit(1)	

# --------------------------------------------------------------------------------
# Open the database spreadsheet
# --------------------------------------------------------------------------------
xl = Dispatch("Excel.Application")
xl.Visible = 0   # set to 1 to make the process visible
workbook = xl.Workbooks.Open(dataDictionary)
try:
  worksheet = workbook.Sheets(worksheetName)
except:
  message = "ERROR: Worksheet %s not found in %s." % (worksheetName,dataDictionary)
  print message
  faib.logMessage(logFile, message)
  xl.ActiveWorkbook.Close(SaveChanges=0)
  worksheet = None
  workbook = None
  xl.Quit()
  xl = None
  sys.exit(1)


# ----------------------------------------------------------------------------
# validate layers in spreadsheet
# ----------------------------------------------------------------------------
# if validateLayersError(managementUnit,worksheet):
#   sys.exit(0)

# ----------------------------------------------------------------------------
# doit
# ----------------------------------------------------------------------------
message = 'Looping through feature classes found in spreadsheet %s worksheet %s...' % (dataDictionary,worksheetName)
faib.logMessage(logFile, message,DEBUG)

# first row
step1 = 0
row = row_origin + 1   # skip header row
fieldMapping = ''
wrkFeatureClass,wrkShortName = readRow(row,col_origin)

if wrkFeatureClass:  #  first row
  # setup so first row will not be treated as a new wrkFeatureClass
  prev_wrkFeatureClass = wrkFeatureClass


# ----------------------------------------------------------------------
# for each GDB feature class/layer
# ----------------------------------------------------------------------

while wrkFeatureClass:

  wrkFeatureClass,wrkShortName = readRow(row,col_origin)

  if wrkFeatureClass != prev_wrkFeatureClass:

    faib.logMessage(logFile, managementUnit+' '+prev_wrkFeatureClass,DEBUG)
    if not DEBUG:
      print time.ctime(),managementUnit,prev_wrkFeatureClass
    step2 = step1 + 1

    # ----------------------------------------------------------------------
    # rasterize the GDB layer to a TIFF
    # ----------------------------------------------------------------------
    dstTiffFile =  tiffPath + "/" + managementUnit + "_" + prev_wrkFeatureClass + ".tif"
    columnName = prev_wrkFeatureClass+'_fid'
    rasterizeGBD2TIFF(workspace,prev_wrkFeatureClass,refLayer,columnName,dstTiffFile,pixel_size)
    
    
    # ----------------------------------------------------------------------
    # load the TIFF to POSTGIS
    # ----------------------------------------------------------------------

    pg_table = managementUnit + "_" + prev_wrkFeatureClass + "_tiff_tmp"

    faib.logMessage(logFile, "%s reading values from %s..." % (time.ctime(),dstTiffFile),DEBUG)
    values = readRasterValues(dstTiffFile)

    faib.logMessage(logFile, 'Converting values to FileLikeObject...',DEBUG)
    FLO_values = convertToFileLikeObject(values)

    faib.logMessage(logFile, 'Loading values to PostgreSQL...',DEBUG)
    connection = psycopg2.connect("dbname=postgres user=postgres")
    cursor = connection.cursor()
    createPsqlTable(pg_table,prev_wrkFeatureClass,connection)
    copyToPsqlTable(FLO_values,pg_table,connection)

    # ----------------------------------------------------------------------
    # load the GDB attributes to a POSTGIS tmp table
    # ----------------------------------------------------------------------

    load_gdb2postgis_attr_tmp(managementUnit,workspace,prev_wrkFeatureClass)

    # ----------------------------------------------------------------------
    # createTmpOverlay
    # ----------------------------------------------------------------------

    createTmpOverlay(managementUnit,prev_wrkFeatureClass,step1,res_start)

    # ----------------------------------------------------------------------
    # resultantsOverlay
    # ----------------------------------------------------------------------

    resultantsOverlay(managementUnit,prev_wrkFeatureClass,fieldMapping,step2)

    # ----------------------------------------------------------------------
    # drop the tmp TIFF and attribute tables
    # ----------------------------------------------------------------------
    dropTables(managementUnit,prev_wrkFeatureClass,logFile)

    step1 = step1 + 1
    fieldMapping = ''
    prev_wrkFeatureClass = wrkFeatureClass

  fieldMapping = setfieldMapping(fieldMapping,wrkShortName)

  # next row
  row = row + 1

# ----------------------------------------------------------------------
# finish the process
# ----------------------------------------------------------------------
trailer(managementUnit,step2,res_end,DEBUG)

# --------------------------------------------------------------------------------
faib.logMessage(logFile, 'close the spreadsheet',DEBUG)
# --------------------------------------------------------------------------------
xl.ActiveWorkbook.Close(SaveChanges=0)
worksheet = None
workbook = None
xl.Quit()
xl = None

message = 'finish %s %s' % (time.ctime(), logFileName)
faib.logMessage(logFile, message,DEBUG)
if not DEBUG:
  print message
