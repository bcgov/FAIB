import sys

# get ready to import local modules
# define the path to the modules and append it to the system path
module_path = '//spatialfiles2.bcgov/work/FOR/VIC/HTS/ANA/Workarea/TOOLS/python/PythonLib/Production'
sys.path.append(module_path)

# continue importing modules
import FAIB_Tools as faib
import os, time, struct, cStringIO, psycopg2
from osgeo import gdal, ogr, osr

# usage
if len(sys.argv) < 3:
  print "Usage: add_vri2skey.py [vri_input_layer] [starting_res_table]"
  print "\nCAUTION: will overwrite [starting_res_table]"
  sys.exit(0)
  
# system arguments
vriLayer = sys.argv[1]
res_0 = sys.argv[2]

# FAIB parameters
parameterFileName = "projectParameters.txt"
parameters = {}
parametersNeeded = {}
parametersNeeded["managementUnit"] = "Management Unit/project prefix"
parametersNeeded["managementUnitBoundary"] = "project boundary layer in GDB"
parametersNeeded["workspace"] = "GDB workspace"
parametersNeeded["pixel_size"] = "raster pixel_size"
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
logFileName = managementUnit+'_add_vri2skey.log'
logFile = file(logFileName, "w")
res_0 = managementUnit + '_' + res_0
vriColumn = vriLayer + '_fid'
vriTIFF = tiffPath + "/" + managementUnit+'_'+vriLayer+'.tif'
vri_table_tiff_tmp = managementUnit+'_'+vriLayer+'_tiff_tmp'
vri_table_attr_tmp = managementUnit+'_'+vriLayer+'_attr_tmp'
tmp = managementUnit + "_tmp"
skey = managementUnit + "_skey"

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

    stmt = "create table " + table + "(ogc_fid serial, " + layer + "_fid integer);"
    cur.execute(stmt)
    conn.commit()

    cur.close()

# ======================================================================
def copyToPsqlTable(data,table,conn):
  cur = conn.cursor()
  cur.copy_from(data,table)
  conn.commit()

  stmt = "alter table " + table + " alter column ogc_fid drop default;"
  cur.execute(stmt)
  conn.commit()

  stmt = "alter sequence " + table + "_ogc_fid_seq owned by none;"
  cur.execute(stmt)
  conn.commit()

  stmt = "drop sequence " + table + "_ogc_fid_seq;"
  cur.execute(stmt)
  conn.commit()

  cur.close()

# ------------------------------------------------------------------------------
def load_gdb2postgis_attr_tmp(managementUnit,workspace,gdbLayer,DEBUG):

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
  connection.commit()

  stmt = "alter table %s rename to %s_%s_attr_tmp;" % (gdbLayer,managementUnit,gdbLayer)
  faib.logMessage(logFile, stmt,DEBUG)
  cursor.execute(stmt)

  stmt = "alter table %s_%s_attr_tmp drop column wkb_geometry;" % (managementUnit,gdbLayer)
  faib.logMessage(logFile, stmt,DEBUG)
  cursor.execute(stmt)

  stmt = "alter table %s_%s_attr_tmp drop column if exists objectid;" % (managementUnit,gdbLayer)
  faib.logMessage(logFile, stmt,DEBUG)
  cursor.execute(stmt)

  stmt = "alter table %s_%s_attr_tmp drop column if exists ogc_fid;" % (managementUnit,gdbLayer)
  faib.logMessage(logFile, stmt,DEBUG)
  cursor.execute(stmt)

  stmt = "drop sequence if exists %s_objectid_seq cascade;" % (gdbLayer)
  faib.logMessage(logFile, stmt,DEBUG)
  cursor.execute(stmt)

  connection.commit()

  cursor.close()
  connection.close()

# ------------------------------------------------------------------------------
def join_vri_tiff_to_attr(vriLayer,vri_tiff, vri_attr, tmp, DEBUG):
  connection = psycopg2.connect("dbname=postgres user=postgres")
  cursor = connection.cursor()
  if connection:
    stmt = "drop table if exists %s;" % (tmp)
    faib.logMessage(logFile, stmt,DEBUG)
    cursor.execute(stmt)

    stmt = "alter table %s drop column if exists wkb_geometry;" % (vri_attr)
    faib.logMessage(logFile, stmt,DEBUG)
    cursor.execute(stmt)
    connection.commit()

    faib.logMessage(logFile, 'Indexing...',DEBUG)
    stmt = "drop index if exists idx1;"
    cursor.execute(stmt)

    stmt = "drop index if exists idx2;"
    cursor.execute(stmt)

    stmt = "create index idx1 on %s(%s_fid);" % (vri_tiff,vriLayer)
    cursor.execute(stmt)

    stmt = "create index idx2 on %s(%s_fid);" % (vri_attr,vriLayer)
    cursor.execute(stmt)
    connection.commit()

    stmt = "create table " + tmp + " as" + \
           " select a.ogc_fid, b.*" + \
           " from " + vri_tiff + " a" + \
           " left join " + vri_attr + " b using("+vriLayer+"_fid);"
    faib.logMessage(logFile, stmt,DEBUG)
    cursor.execute(stmt)
    connection.commit()

    stmt = "drop index if exists idx1;"
    cursor.execute(stmt)

    stmt = "drop index if exists idx2;"
    cursor.execute(stmt)
    connection.commit()

    stmt = "drop table if exists %s;" % (vri_attr)
    faib.logMessage(logFile, stmt,DEBUG)
    cursor.execute(stmt)

    stmt = "drop table if exists %s;" % (vri_tiff)
    faib.logMessage(logFile, stmt,DEBUG)
    cursor.execute(stmt)

# ------------------------------------------------------------------------------
def join_skey_to_vri(skey, tmp, res_0,DEBUG):

  connection = psycopg2.connect("dbname=postgres user=postgres")
  cursor = connection.cursor()
  if connection:
    stmt = "drop table if exists %s;" % (res_0)
    faib.logMessage(logFile, stmt,DEBUG)
    cursor.execute(stmt)
    connection.commit()

    stmt = "drop index if exists idx1;"
    faib.logMessage(logFile, stmt,DEBUG)
    cursor.execute(stmt)

    faib.logMessage(logFile, 'Indexing...',DEBUG)
    stmt = "drop index if exists idx2;"
    cursor.execute(stmt)

    stmt = "create index idx1 on %s(ogc_fid);" % (skey)
    cursor.execute(stmt)
    connection.commit()

    stmt = "create index idx2 on %s(ogc_fid);" % (tmp)
    cursor.execute(stmt)

    stmt = "create table " + res_0 + " as" + \
           " select a.gr_skey, b.*" + \
           " from " + skey + " a" + \
           " left join " + tmp + " b using(ogc_fid);"
    faib.logMessage(logFile, stmt,DEBUG)
    cursor.execute(stmt)
    connection.commit()

    stmt = "drop index if exists idx1;"
    cursor.execute(stmt)

    stmt = "drop index if exists idx2;"
    cursor.execute(stmt)

    stmt = "drop table if exists %s;" % (tmp)
    faib.logMessage(logFile, stmt,DEBUG)
    cursor.execute(stmt)

    connection.commit()

# ------------------------------------------------------------------------------
def cleanup(vri_attr,vri_tiff,DEBUG):

  connection = psycopg2.connect("dbname=postgres user=postgres")
  cursor = connection.cursor()
  if connection:
    stmt = "drop table if exists %s;" % (vri_attr)
    faib.logMessage(logFile, stmt,DEBUG)
    cursor.execute(stmt)

    stmt = "drop table if exists %s;" % (vri_tiff)
    faib.logMessage(logFile, stmt,DEBUG)
    cursor.execute(stmt)

    connection.commit()

# --------------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------------

message = 'start  %s %s' % (time.ctime(), logFileName)
faib.logMessage(logFile, message,DEBUG)
print message

# log some of the input parameters
faib.logMessage(logFile, 'reference_GDB_layer: %s' % refLayer,DEBUG)
faib.logMessage(logFile, 'pixel_size: %d' % int(pixel_size),DEBUG)
faib.logMessage(logFile, 'VRI layer: %s' % vriLayer,DEBUG)
faib.logMessage(logFile, 'output table: %s' % res_0,DEBUG)

# --------------------------------------------------------------------------------
# rasterize the VRI GDB layer to a TIFF on vri_fid
# --------------------------------------------------------------------------------
message = "%s creating %s..." % (time.ctime(),vriTIFF)
faib.logMessage(logFile, message,DEBUG)
faib.rasterizeGBDlayer2TIFF(workspace,vriLayer,refLayer,vriColumn,vriTIFF,pixel_size,logFile)

# --------------------------------------------------------------------------------
# load the VRI TIFF to POSTGIS
# --------------------------------------------------------------------------------

message = "%s creating Postgres table %s..." % (time.ctime(),vri_table_tiff_tmp)
faib.logMessage(logFile, message,DEBUG)

faib.logMessage(logFile, "Reading values from %s..." % (vriTIFF),DEBUG)
values = readRasterValues(vriTIFF)

faib.logMessage(logFile, 'Converting values to FileLikeObject...',DEBUG)
FLO_values = convertToFileLikeObject(values)

faib.logMessage(logFile, 'Loading values to Postgres...',DEBUG)
connection = psycopg2.connect("dbname=postgres user=postgres")
cursor = connection.cursor()
createPsqlTable(vri_table_tiff_tmp,vriLayer,connection)
copyToPsqlTable(FLO_values,vri_table_tiff_tmp,connection)

# --------------------------------------------------------------------------------
# load the VRI attributes (ATTR) to POSTGIS
# --------------------------------------------------------------------------------

message = "%s creating Postgres table %s..." % (time.ctime(),vri_table_attr_tmp)
faib.logMessage(logFile, message,DEBUG)

load_gdb2postgis_attr_tmp(managementUnit,workspace,vriLayer,DEBUG)

# --------------------------------------------------------------------------------
# 
# --------------------------------------------------------------------------------

message = "%s creating Postgres table %s..." % (time.ctime(),res_0)
faib.logMessage(logFile, message,DEBUG)

message = '%s joining VRI TIFF to attributes' % time.ctime()
faib.logMessage(logFile, message,DEBUG)
join_vri_tiff_to_attr(vriLayer,vri_table_tiff_tmp, vri_table_attr_tmp, tmp, DEBUG)

message = '%s joining skey to VRI attributes' % time.ctime()
faib.logMessage(logFile, message,DEBUG)
join_skey_to_vri(skey, tmp, res_0,DEBUG)

cleanup(vri_table_tiff_tmp,vri_table_attr_tmp,DEBUG)

# --------------------------------------------------------------------------------
# done
# --------------------------------------------------------------------------------

message = 'finish %s %s' % (time.ctime(), logFileName)
faib.logMessage(logFile, message,DEBUG)
print message
	