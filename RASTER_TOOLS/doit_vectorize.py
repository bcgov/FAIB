

# doit.py: calling / looping script to run other scripts using a list file
#
# History:
#   Oct 8, 2018 Kelly Izzard

# Import system modules
import os, sys, time
import shutil,string

# usage
if len(sys.argv) < 2:
  print "Usage: doit <listFileName>"
  sys.exit(0)

# list file of TSA #s
listFileName = sys.argv[1]
listFile = open(listFileName,"r")

# first record
record = listFile.readline()
record = record.replace("\n","")
# start process clock
start = time.clock()
print 'starting process'
inpath =  r"S:\FOR\VIC\HTS\ANA\workarea\AR2018\units"+os.sep+record
outpath = r"C:\data\RasterARD"+os.sep+record
#print cmd


while record:

  # modify / run commands here
  # -----------------------------------------------------------------------------------

  #set projectParameters to current tsa from list file
  cmd = 'python setParams4TSA.py projectParameters.K %s' % (record)
  print cmd
  os.system(cmd)   
  #shutil.copytree(inpath, outpath)
  # vacuum postgres database before rasterizing
  #cmd = 'psql -d postgres -c vacuum'
  #print cmd
  #os.system(cmd)
  #cmd = '01_create_skey' # 
  #print cmd
  #os.system(cmd)

 #---------------------------------resultant
  
  
  start_skey = time.clock()
  cmd = 'ogr2ogr -f \"FileGDB\" -nlt MULTIPOLYGON -nln \"'+record+'_skey\" -progress -overwrite -sql \"SELECT * FROM '+record+'_skey'
  cmd = cmd + '\" -mapFieldType Integer64=Integer '+outpath+os.sep+record+'_2018.gdb PG:\"user=postgres dbname=postgres password=postgres\"'
  print 'create vector skey'
  os.system(cmd)
  end_skey = time.clock()
  run_skey = round((end_skey-start_skey)/60,1)
  print 'finished....total skey processing time = '+str(run_skey)+' minutes' 
  
  # start_ar = time.clock()
  # cmd = 'ogr2ogr -f \"FileGDB\" -nln \"'+record+'_ar_table\" -progress -overwrite -sql \"SELECT * FROM '+record+'_ar_table WHERE included > 0'
  # cmd = cmd + '\" -mapFieldType Integer64=Integer '+outpath+os.sep+record+'.gdb PG:\"user=postgres dbname=postgres password=postgres\"'
  # print 'create ar table'
  # os.system(cmd)
  # end_ar = time.clock()
  # run_ar = round((end_ar-start_ar)/60,1)
  # print 'finished....total ar processing time = '+str(run_ar)+' minutes'
  # start_ar = 0
  # end_ar = 0
  # run_ar = 0
  
  record = listFile.readline()
  record = record.replace("\n","")
 
listFile.close()
end = time.clock()
run = round((end-start)/60,1)
print 'finished....total processing time = '+str(run)+' minutes' 
