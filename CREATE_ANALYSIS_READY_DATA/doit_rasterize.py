

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

while record:

  # modify / run commands here
  # -----------------------------------------------------------------------------------

  #set projectParameters to current tsa from list file
  cmd = 'python setParams4TSA.py projectParameters.K %s' % (record)
  print cmd
  os.system(cmd)
  # move gdb for S: drive to D drive
  inpath =  r"S:\FOR\VIC\HTS\ANA\workarea\AR2018\units"+os.sep+record
  outpath = r"C:\data\RasterARD"+os.sep+record
  print inpath
  print outpath
  
  shutil.copytree(inpath, outpath)
  # vacuum postgres database before rasterizing
  cmd = 'psql -d postgres -c vacuum'
  print cmd
  os.system(cmd)
  # run creat_skey batch file
  cmd = '01_create_skey' # 
  print cmd
  os.system(cmd)
  # run vri batch - add vri attributes to resultant table (2018 - 96 fields)
  cmd = '02_add_vri2skey vri res_0' # 
  print cmd
  os.system(cmd)
  # run makeResultant batch - add selected feature class attributes to resultant table (2018 - 63 fields)
  cmd = '03_mkResultants res_0 ar_table' # 
  print cmd
  os.system(cmd)
  # calculate rasterization proces time
  end = time.clock()
  run = round((end-start)/60,1)
  print 'finished....total rasterizing time = '+str(run)+' minutes' 

  # dump resultant tables to sql files-----------------
  cmd = 'pg_dump -t '+record+'_skey -f '+outpath+os.sep+record+'_skey.sql' # 
  print cmd
  os.system(cmd)

  cmd = 'pg_dump -t '+record+'_ar_table -f '+outpath+os.sep+record+'_ar_table.sql' # 
  print cmd
  os.system(cmd)

  # drop temp tables from postgres database----------------
  cmd = 'psql -c \"drop table '+record+'_skey;\"'
  print cmd
  os.system(cmd)

  cmd = 'psql -c \"drop table '+record+'_res_0;\"'
  print cmd
  os.system(cmd)

  cmd = 'psql -c \"drop table '+record+'_ar_table;\"'
  print cmd
  os.system(cmd)

  # zip up sql files and move the S drive----------
  cmd = '7z a '+inpath+os.sep+record+'_skey.sql.7z '+outpath+os.sep+record+'_skey.sql'
  print cmd
  os.system(cmd)


  if os.path.isfile(inpath+os.sep+record+'_skey.sql.7z'):
  	os.remove(outpath+os.sep+record+'_skey.sql')

  cmd = '7z a '+inpath+os.sep+record+'_ar_table.sql.7z '+outpath+os.sep+record+'_ar_table.sql'
  print cmd
  os.system(cmd)

  if os.path.isfile(inpath+os.sep+record+'_ar_table.sql.7z'):
  	os.remove(outpath+os.sep+record+'_ar_table.sql')

  	
  end = time.clock()
  run = round((end-start)/60,1)
  print 'finished....total processing time = '+str(run)+' minutes'
	

   #-----------------------------------------------------------------------------------

  record = listFile.readline()
  record = record.replace("\n","")
  shutil.rmtree(outpath, ignore_errors=True) 	

listFile.close()
end = time.clock()
run = round((end-start)/60,1)
print 'finished....total processing time = '+str(run)+' minutes' 
