import os, sys

# doit.py: calling / looping script to run other scripts using a list file
#
# History:
#   Jun-06 Doug Layden

# Import system modules
import sys, string, os

# usage
if len(sys.argv) < 2:
  print "Usage: doit <listFileName>"
  sys.exit(0)

# list file
listFileName = sys.argv[1]
listFile = open(listFileName,"r")

# first record
record = listFile.readline()
record = record.replace("\n","")

while record:

  # modify / run commands here
  # -----------------------------------------------------------------------------------

  #set projectParameters to current tsa from list file
  cmd = 'python setParams4TSA.py projectParameters.K %s' % (record)
  print cmd
  os.system(cmd)

##  cmd = r'mkdir ..\..\units\%s' % (record) # create folder for each tsa under units folder
##  cmd = 'createGDB4TSR' # create database for each TSA
##  cmd = 'python getBnd.py %s' % (record)       # get boundary feature class for a TSA
##  cmd = 'python W:/FOR/VIC/HTS/ANA/Workarea/TOOLS/python/FAIB_Tools/extractFromBCGW10.py vri' # extract the VRI from BCGW"
##  cmd = 'python batchExtract.py'        # extract a set of standard layers
  #cmd = 'E:\sw_nt\Python27\ArcGISx6410.3\python.exe getTHLB2018_kelly.py %s' % (record) # get THLB from consolidated THLB GDB# needs tsa_number.lst for now....edit getTHLB script###############
  cmd = 'python getTHLB2018_kelly.py %s' % (record) # get THLB from consolidated THLB GDB# needs tsa_number.lst for now....edit getTHLB script###############
##  cmd = 'E:\sw_nt\Python27\ArcGISx6410.3\python.exe getIntegratedRoads.py'
  # cmd = 'python getIntegratedRoadsKtest.py'

  # EDIT parameter file and run for std2wrk_2018
  # EDIT parameter file and re-run for vri2wrk_2018
##  cmd = 'E:\sw_nt\Python27\ArcGISx6410.3\python.exe mkSrc2wrkScripts10.py'
##  os.system(cmd)

##  cmd = 'run_std2wrk.bat'    # run scripts for standard set of feature classes
##  cmd = 'run_vri2wrk.bat'    # run script for VRI (separate because it's slow)
##  cmd = 'E:\sw_nt\Python27\ArcGISx6410.3\python.exe getCutblocks2018.py' # NOT READY as of 2018-06-13

  # EDIT Calculate Species##
  #cmd = 'E:\sw_nt\Python27\ArcGISx6410.3\python.exe TabularizeTreeSpeciesVolume_125_UPDATED.py' # Updated TabularizeTreeSpeciesVolume_125 and doug's GroupSpecies scripts

  print cmd
  os.system(cmd)
  # -----------------------------------------------------------------------------------

  record = listFile.readline()
  record = record.replace("\n","")

listFile.close()

