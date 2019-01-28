import sys

# get ready to import local modules
# define the path to the modules and append it to the system path
module_path = '//spatialfiles2.bcgov/work/FOR/VIC/HTS/ANA/Workarea/TOOLS/python/PythonLib/Production'
sys.path.append(module_path)

# continue importing modules
import FAIB_Tools as faib
import os, time, struct
from osgeo import gdal, ogr, osr

# FAIB parameters
parameterFileName = "projectParameters.txt"
parameters = {}
parametersNeeded = {}
parametersNeeded["workspace"] = "Management Unit/project prefix"
parametersNeeded["managementUnit"] = "GDB workspace"
parametersNeeded["managementUnitBoundary"] = "project boundary layer in GDB"
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
logFileName = managementUnit+'_create_skey.log'
logFile = file(logFileName, "w")
includedTIFF = tiffPath + "/" + managementUnit + "_included.tif"
clippedTIFF = tiffPath + "/" + managementUnit + "_clip_gr_skey.tif"
skey_outfile = tiffPath + '/'  + managementUnit + '_skey.tif'
tableName = managementUnit + '_skey'
dst_fieldname = "gr_skey"
maskband = None

# choose gr_skey TIFF to clip from
if pixel_size == 100:
  srcDataset = "//spatialfiles2.bcgov/archive/FOR/VIC\HTS/ANA/workarea/PROVINCIAL/bc_01ha_gr_skey.tif"
elif pixel_size == 200:
  srcDataset = "//spatialfiles2.bcgov/archive/FOR/VIC\HTS/ANA/workarea/PROVINCIAL/bc_04ha_gr_skey.tif"
elif pixel_size == 400:
  srcDataset = "//spatialfiles2.bcgov/archive/FOR/VIC\HTS/ANA/workarea/PROVINCIAL/bc_16ha_gr_skey.tif"
else:
  message = 'Error clip_provincial_gr_skey.py: not setup for pixel size %d' % int(pixel_size)
  faib.logMessage(logFile, message,DEBUG)
  print message
  sys.exit(1)

#===============================================================================
def readRasterValues(tiffFileName):
    
  src = gdal.Open(tiffFileName)
  band = src.GetRasterBand(1)

  # Read the raster properties
  # get the data type from the Tiff and use to unpack 
  prj = src.GetProjection()
  geotrans = src.GetGeoTransform()
  xsize = band.XSize
  ysize = band.YSize
  faib.logMessage(logFile, "TIFF %s x&y size %d %d %d" % (tiffFileName, xsize, ysize, xsize*ysize),DEBUG)
  datatype = band.DataType

  # Read the raster values as packed binary
  v_packed = band.ReadRaster( 0, 0, xsize, ysize, xsize, ysize, datatype )

  #Conversion between GDAL types and python pack types (Can't use complex integer or float!!)
  data_types ={'Byte':'B','UInt16':'H','Int16':'h','UInt32':'I','Int32':'i','Float32':'f','Float64':'d'}
  values = struct.unpack(data_types[gdal.GetDataTypeName(band.DataType)]*xsize*ysize,v_packed)
  
  return values

#===============================================================================
def tupleToList(inTuple):
  outList = []
  for item in inTuple:
    outList.append(item)

  return outList

#===============================================================================
def rasterMultiplyNegativeSequence(clipList,bndList):
  tmpData = []
  
  # multiple the arrays (using index)
  # generate negative sequence where <= 0
  # negative required so that gdal_polygonize doesn't dissolve the noData rasters
  
  negativeIndex = -1
  for i in range(len(clipList)):
    try:
      if clipList[i] > 0 and bndList[i] > 0:
        tmpData.append(clipList[i])
      else:
        tmpData.append(negativeIndex)
        negativeIndex = negativeIndex - 1
    except:
    	message = 'Error in convert_clip2skey.py/readRasterValues: clip array length %d bnd array length %d index %d' % (len(clipList),len(bndList),i)
    	faib.logMessage(logFile, message, DEBUG)
    	print message
    	sys.exit(1)
  return tmpData	

#===============================================================================
def createTiffCopy(copyFrom,copyTo):
  # create a copy of one of the input files
  driver = gdal.GetDriverByName("GTiff");
  src = gdal.Open(copyFrom)
  
  # create a copy of one of the tiffs so that 
  #SRS,projection, noDataValue and data_type are set
  dst = driver.CreateCopy(copyTo, src)

#===============================================================================
def writeRaster(outFile,arrayData):
  # open tiff for update
  driver = gdal.GetDriverByName("GTiff");
  dst = gdal.Open(outFile,gdal.GA_Update)
  
  xsize = dst.RasterXSize
  ysize = dst.RasterYSize
  faib.logMessage(logFile, "Writing the data into a packed byte array...",DEBUG)
  outArray = bytes()
  outArray = struct.pack('%sl' % len(arrayData), *arrayData)
  
  # select the raster band to work with
  outBand = dst.GetRasterBand(1) 

  faib.logMessage(logFile, "Writing the packed array to the tiff...",DEBUG)
  outBand.WriteRaster(0,0,xsize,ysize,outArray)
  
  outBand.FlushCache()
  del outArray
  
# --------------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------------

message = 'start  %s %s' % (time.ctime(), logFileName)
faib.logMessage(logFile, message,DEBUG)
print message

# log some of the input parameters
faib.logMessage(logFile, 'reference_GDB_layer: %s' % refLayer,DEBUG)
faib.logMessage(logFile, 'pixel_size: %d' % int(pixel_size),DEBUG)
faib.logMessage(logFile, 'source gr_skey TIFF: %s' % srcDataset,DEBUG)

# --------------------------------------------------------------------------------
# rasterize management unit boundary on included
# --------------------------------------------------------------------------------
message = "%s creating %s..." % (time.ctime(),includedTIFF)
faib.logMessage(logFile, message,DEBUG)
faib.rasterizeGBDlayer2TIFF(workspace,refLayer,refLayer,'included',includedTIFF,pixel_size,logFile)

# --------------------------------------------------------------------------------
# clip provincial gr_skey to management unit boundary as defined by included
# --------------------------------------------------------------------------------

message = "%s creating %s..." % (time.ctime(),clippedTIFF)
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
# mask clipped gr_skey to management unit boundary
# --------------------------------------------------------------------------------

# read the raster data into arrays
message = "%s creating %s..." % (time.ctime(),skey_outfile)
faib.logMessage(logFile, message,DEBUG)

faib.logMessage(logFile, "Reading the raster data into tuples...",DEBUG)
clipTuple = readRasterValues(clippedTIFF)
includedTuple = readRasterValues(includedTIFF)

faib.logMessage(logFile, "Creating lists from tuples...",DEBUG)
clipList = tupleToList(clipTuple)
includedList = tupleToList(includedTuple)
del clipTuple
del includedTuple

skey = rasterMultiplyNegativeSequence(clipList,includedList)
del clipList
del includedList

createTiffCopy(includedTIFF,skey_outfile)
writeRaster(skey_outfile,skey)

faib.logMessage(logFile, "Created %s" % (skey_outfile),DEBUG)

# --------------------------------------------------------------------------------
# load skey to PostGIS (with wkb_geometry)
# --------------------------------------------------------------------------------

message = "%s creating PostGIS table %s..." % (time.ctime(),tableName)
faib.logMessage(logFile, message,DEBUG)

# open the source
src_ds = gdal.Open(skey_outfile)
srcband = src_ds.GetRasterBand(1)

drv = ogr.GetDriverByName("PostgreSQL")
dst_ds =  drv.Open("PG:dbname=postgres")

srs = osr.SpatialReference()
srs.ImportFromWkt( src_ds.GetProjectionRef())

# check if table exists
try:
	dst_layer = dst_ds.GetLayerByName(tableName)
except:
	dst_layer = None

# if table doesn't exist, create it
if dst_layer is None:
	dst_layer = dst_ds.CreateLayer(tableName,srs = srs)
# if table exists
else :
	# delete
	dst_ds.DeleteLayer(tableName)
	# create
	dst_layer = dst_ds.CreateLayer(tableName,srs = srs)

# define the output field name
# this will be in field index 0
field_def = ogr.FieldDefn(dst_fieldname,ogr.OFTInteger)
dst_layer.CreateField(field_def)

#gdal.Polygonize(SrcBAnd,MaskBand,OutLayer,PixValField (index), Options)
faib.logMessage(logFile, 'gdal.Polygonize...',DEBUG)
err = gdal.Polygonize(srcband, maskband, dst_layer,0)

faib.logMessage(logFile, 'removing ' + clippedTIFF + '...',DEBUG)
os.remove(clippedTIFF)
dst_ds.Destroy()

# --------------------------------------------------------------------------------
# done
# --------------------------------------------------------------------------------

message = 'finish %s %s' % (time.ctime(), logFileName)
faib.logMessage(logFile, message,DEBUG)
print message
