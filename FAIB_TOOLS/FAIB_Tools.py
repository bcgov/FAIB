# FAIB_Tools/python module for importing into python scripts

import os
import sys
from osgeo import ogr
from osgeo import gdal

# list of functions in module:
#   getProjectParameters(parameterFileName, parameters, parametersNeeded)
#   calcRasterExtents(x_min, y_min, x_max, y_max, pixel_size,DEBUG=False)
#   logMessage(logFile, message)
#   rasterizeGBDlayer2TIFF(gdbFile,gdbLayer,refLayer,col_name,dstFile,pixel_size,logFile=None,noDataValue=-99)

# ========================================================================

def getProjectParameters(parameterFileName, parameters, parametersNeeded):

  # ----------------------------------------------------------------------
  # read project parameters file and check that all parameters that are
  # needed exist in the parameter file
  # ----------------------------------------------------------------------

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

# ========================================================================

def calcRasterExtents(x_min, y_min, x_max, y_max, pixel_size,logFile):

  # ----------------------------------------------------------------------
  # return set of raster extents aligned with provincial HaBC exents given
  # a set of xmin, ymin, xmax, ymax coordinates
  # ----------------------------------------------------------------------

  # calculate raw extents aligned to provincial extents
  prov_x_min =  159587.5
  prov_y_min =  173787.5
  prov_x_max = 1881187.5
  prov_y_max = 1748187.5

  # calculate offset from prov DEM lower left
  Xoff_ll = x_min - prov_x_min
  Yoff_ll = y_min - prov_y_min
  Xoff_ll = int(Xoff_ll / pixel_size) * pixel_size
  Yoff_ll = int(Yoff_ll / pixel_size) * pixel_size
  
  # calculate offset from prov DEM upper right
  Xoff_ur = prov_x_max - x_max
  Yoff_ur = prov_y_max - y_max
  Xoff_ur = int(Xoff_ur / pixel_size) * pixel_size
  Yoff_ur = int(Yoff_ur / pixel_size) * pixel_size
  
  # raster grid boundary
  rast_x_min = prov_x_min + Xoff_ll
  rast_y_min = prov_y_min + Yoff_ll
  rast_x_max = prov_x_max - Xoff_ur
  rast_y_max = prov_y_max - Yoff_ur

  # pixels
  x_size = (rast_x_max - rast_x_min) / pixel_size
  y_size = (rast_y_max - rast_y_min) / pixel_size

  if logFile:
    message = 'faib.calcRasterExtents: rast_x_min %.1f rast_y_min %.1f rast_x_max %.1f rast_y_max %.1f' % (rast_x_min, rast_y_min, rast_x_max, rast_y_max)
    logFile.write(message+"\n")
    message = 'faib.calcRasterExtents: pixels %d %d %d' % (x_size,y_size,x_size*y_size)
    logFile.write(message+"\n")

  return rast_x_min, rast_y_min, rast_x_max, rast_y_max

# ========================================================================

def logMessage(logFile, message,DEBUG=False):
  logFile.write(message+"\n")
  if DEBUG:
    print message

# ========================================================================

def rasterizeGBDlayer2TIFF(gdbFile,gdbLayer,refLayer,col_name,dstFile,pixel_size,logFile=None,noDataValue=-99,DEBUG=True):

  # specify column to rasterize on
	option = 'ATTRIBUTE=' + col_name

	# Open the data source
	sourceData = ogr.Open(gdbFile)
	if sourceData == None:
		message = "Error faib.rasterizeGBDlayer2TIFF: failed to open %s" % (gdbFile)
		logMessage(logFile, message)
		print message
		sys.exit(1)
	sourceLayer = sourceData.GetLayer(str(gdbLayer))
	if sourceLayer == None:
		message = "Error rasterizeGBDlayer2TIFF: rasterization layer %s not found in %s" % (gdbLayer,gdbFile)
		logMessage(logFile, message)
		print message
		sys.exit(2)
	sourceSrs = sourceLayer.GetSpatialRef()

	referenceLayer = sourceData.GetLayer(refLayer)
	if referenceLayer == None:
		message = "Error rasterizeGBDlayer2TIFF: reference layer %s not found in %s" % (refLayer,gdbFile)
		logMessage(logFile, message)
		print message
		sys.exit(3)

	#define extent
	x_min, x_max, y_min, y_max = referenceLayer.GetExtent()
	raster_x_min, raster_y_min, raster_x_max, raster_y_max = calcRasterExtents(x_min, y_min, x_max, y_max, pixel_size,logFile)
	x_res = int((raster_x_max - raster_x_min) / float(pixel_size))
	y_res = int((raster_y_max - raster_y_min) / float(pixel_size))

	if logFile:
		logMessage(logFile, "faib.rasterizeGBDlayer2TIFF: processing %s: %s" % (gdbLayer,option))
		logMessage(logFile, "faib.rasterizeGBDlayer2TIFF: pixel size %d"% pixel_size)
		logMessage(logFile, "faib.rasterizeGBDlayer2TIFF: pixels cols %d rows %d pixels %d" % (x_res, y_res, x_res*y_res))
		logMessage(logFile, 'faib.rasterizeGBDlayer2TIFF: x_min   x_max   y_min   y_max')
		logMessage(logFile, 'faib.rasterizeGBDlayer2TIFF: input %f %f %f %f' % (x_min, x_max, y_min, y_max))
		logMessage(logFile, 'faib.rasterizeGBDlayer2TIFF: output %.1f %.1f %.1f %.1f' % (raster_x_min, raster_x_max, raster_y_min, raster_y_max))


	# Create the destination data source
	numLayers = 1
	if os.path.exists(dstFile):
		os.remove(dstFile)
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
	err = gdal.RasterizeLayer(target_ds, bandList , sourceLayer, options=[option])
		
	if err != 0:
		raise Exception("error rasterizing layer: %s" % err)

# ========================================================================
