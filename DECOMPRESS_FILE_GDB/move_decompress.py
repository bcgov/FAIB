import sys, string, os, win32com.client, os.path, time
import win32api,win32pdhutil,win32con
import arcpy, os, os.path, shutil
import tempfile

start = time.clock()
print ('starting process')
from arcpy import env
arcpy.CheckOutExtension("Spatial")
from arcpy.sa import *


if len(sys.argv) < 2:
    print ("Usage: doit <listFileName>")
    sys.exit(0)

# list file
listFileName = sys.argv[1]
listFile = open(listFileName,"r")

# first record
record = listFile.readline()
record = record.replace("\n","")

while record:
    inpath =  r"S:\FOR\VIC\HTS\ANA\workarea\AR2018\units"+os.sep+record
    outpath = r"W:\FOR\VIC\HTS\ANA\Workarea\AR2018_compressed"+os.sep+record
    #outpath = r"D:"+os.sep+record
    ingdb = inpath+os.sep+record+'_2018.gdb'
    outgdb = outpath+os.sep+record+'_2018.gdb'
    if os.path.isdir(outpath):
        print ("folder "+outpath+" exists....removing")
        shutil.rmtree(outpath, ignore_errors=True)
        os.makedirs(outpath)
    else:
        print ("creating folder on W drive")
        os.makedirs(outpath)

    print ("copying gdb to w drive")
    shutil.copytree(ingdb, outgdb)
    arcpy.env.workspace = outpath
    #List all file geodatabases in the current workspace
    workspaces = arcpy.ListWorkspaces("*", "FileGDB")
    for workspace in workspaces:
        print ("decompressing "+workspace)
        arcpy.UncompressFileGeodatabaseData_management(workspace)
    record = listFile.readline()
    record = record.replace("\n","")

listFile.close()
end = time.clock()
run = round((end-start)/60,1)
print ('finished....total processing time = '+str(run)+' minutes')
