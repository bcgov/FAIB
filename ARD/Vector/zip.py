
# TSA list file

listFileName = sys.argv[1]
listFile = open(listFileName,"r")
# first record
record = listFile.readline()
record = record.replace("\n","")
# start process clock
start = time.clock()
print 'starting process'
while record:
#############################################################################################################
  # zip up sql files and move the S drive----------
    print(record)
    #cmd = '7z a '+inpath+os.sep+record+'_ar_table.sql.7z '+outpath+os.sep+record+'_ar_table.sql'
    outCSV = r"S:\FOR\VIC\HTS\ANA\workarea\AR2020\units"+ os.sep + tsa
    cmd = '7z a '+outCSV+os.sep+'FN.7z '+ outCSV+os.sep+'FN.csv'
    print cmd
    os.system(cmd)


    if os.path.isfile(outCSV+os.sep+'FN.7z'):
  	os.remove(outCSV+os.sep+'FN.csv')

###########################################################################################

    record = listFile.readline()
    record = record.replace("\n","")


listFile.close()
end = time.clock()
run = round((end-start)/60,1)
print 'finished....total processing time = '+str(run)+' minutes'
