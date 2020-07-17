import os, sys

# doit.py: create ARDs
# History:
#   April, 2020 Iaian McDougall
#Needed inputs:
# 1. projectParameters.S

# Import system modules
import sys, string, os, subprocess

# usage
if len(sys.argv) < 2:
  print "Usage: doit <listFileName>"
  sys.exit(0)

# TSA list file
tsaListFile = sys.argv[1]


# list file
if len(sys.argv) > 2:
    extractDatasetName = sys.argv[2]

# list file
if len(sys.argv) > 3:
    booleanArg = sys.argv[3]

#######################HARD CODED VALUES####################################################
############CHANGE YEAR###########
year = 2020
root  = r"S:\for\VIC\HTS\ANA\workarea\AR" + str(year) + "\units"
tsaFC = r"W:\FOR\VIC\HTS\ANA\Workarea\PROVINCIAL\provincial.gdb\wrk\tsa_boundaries_2020"
intRds= r"S:\\FOR\\VIC\\HTS\\ANA\\workarea\\AR2020\\BC_CE_Integrated_Roads_2019_20190307.gdb\\integrated_roads_buffer"
thlb = r"W:\FOR\VIC\HTS\DAM\Workarea\mcdougall\data\prov_thlb.gdb\thlb"
dataDictionary = r"S:\for\VIC\HTS\ANA\workarea\AR2020\docs\dataDictionary_AR2020.xlsx"
tab = "allsrc2wrk"



#############################################################################################################
#Create TSA directories and file gdbs
cmd = 'E:\sw_nt\Python27\ArcGISx6410.6\python.exe createARDdir.py %s %s %s' %(tsaListFile, root, year)
process = subprocess.Popen(cmd)
process.wait()

#Popuplate gdbs with tsa bondaries
cmd = 'E:\sw_nt\Python27\ArcGISx6410.6\python.exe getBnd.py %s %s %s %s' %(tsaListFile, root, year,tsaFC)
process = subprocess.Popen(cmd)
process.wait()


#Upload Datasets from BCGW and to ard directory
cmd = 'E:\sw_nt\Python27\ArcGISx6410.6\python.exe updated_batchExtract.py %s %s %s %s %s' %(tsaListFile, root, year, extractDatasetName, booleanArg)        # Faster batch extract script 3 args 1. tsaNum list .txt 2. Datasets List .txt 3.overwrite Y or N
process = subprocess.Popen(cmd)
process.wait()
##
#Fix lu overlaps
cmd = 'E:\sw_nt\Python27\ArcGISx6410.6\python.exe resolve_lu.py %s %s %s' %(tsaListFile, root, year)        # Creat a clean landscape Unit dataset
process = subprocess.Popen(cmd)
process.wait()
##
#fix uwr overlaps
cmd = 'E:\sw_nt\Python27\ArcGISx6410.6\python.exe resolve_uwr.py %s %s %s' %(tsaListFile,root, year)
process = subprocess.Popen(cmd)
process.wait()
##
#get integrated roads overlaps
cmd = 'E:\sw_nt\Python27\ArcGISx6410.6\python.exe getIntegratedRoads.py %s %s %s %s' %(tsaListFile, root, year, intRds)
process = subprocess.Popen(cmd)
process.wait()
##
#get thlb
cmd = 'E:\sw_nt\Python27\ArcGISx6410.6\python.exe getTHLB.py %s %s %s %s' %(tsaListFile, root, year, thlb)
process = subprocess.Popen(cmd)
process.wait()


cmd = 'E:\sw_nt\Python27\ArcGISx6410.6\python.exe srcToWrkBatch.py %s %s %s %s %s' %(tsaListFile, root, year, dataDictionary, tab)
process = subprocess.Popen(cmd)
process.wait()

##cmd = 'E:\sw_nt\Python27\ArcGISx6410.6\python.exe TabularizeTreeSpeciesVolume_125_UPDATED.py %s' %(tsaListFile) # Updated TabularizeTreeSpeciesVolume_125 and doug's GroupSpecies scripts
##process = subprocess.Popen(cmd)
##process.wait()




