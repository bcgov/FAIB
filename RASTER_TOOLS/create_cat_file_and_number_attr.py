import sys

# get ready to import local modules
# define the path to the modules and append it to the system path
module_path = '//spatialfiles2.bcgov/work/FOR/VIC/HTS/ANA/Workarea/TOOLS/python/PythonLib/Production'
# module_path = 'C:/Data/training_201806/python/lib'
sys.path.append(module_path)

# continue importing modules
import FAIB_Tools as faib
import os,time
import psycopg2

# usage
if len(sys.argv) < 3:
  print "Usage: python create_cat_file_and_number_attr.py [res_table] [attribute_name]"
  sys.exit(0)

# commandline argument
resName = sys.argv[1]
attr = sys.argv[2]

# FAIB parameters
parameterFileName = "projectParameters.txt"
parameters = {}
parametersNeeded = {}
parametersNeeded["managementUnit"] = "management unit"
parametersNeeded["catsPath"] = "path to folder where SELES cats files are stored"
parametersNeeded["DEBUG"] = "DEBUG = True or False"
faib.getProjectParameters(parameterFileName, parameters, parametersNeeded)

# local variables
managementUnit = parameters["managementUnit"]
catsPath = parameters["catsPath"]
if (parameters["DEBUG"] == 'False'):
  DEBUG = False
else:
  DEBUG = True
logFileName = managementUnit+'_create_cat_file_and_%s_number.log' % (attr)
logFile = file(logFileName, "w")
res = '%s_%s' % (managementUnit,resName)
cat_tmp = '%s_%s_cat_tmp' % (managementUnit, attr)
res_tmp = '%s_%s_tmp' % (managementUnit,resName)

if DEBUG:
  print 'create_cat_file_and_number_attr start  ', time.ctime()

# ------------------------------------------------------------------------------
def create_cat_and_update(res, managementUnit, attr, catsPath, cat_tmp, res_tmp, DEBUG=True):

  connection = psycopg2.connect("dbname=postgres user=postgres")
  cursor = connection.cursor()
  if connection:

    stmt = "drop table if exists %s;" % (cat_tmp)
    if DEBUG:
      print stmt
    cursor.execute(stmt)

    stmt = "create table " + cat_tmp + " as" \
           " select distinct " + attr + "," \
           " dense_rank() over (order by " + attr + " NULLS LAST) as " + attr + "_number" \
           " from " + res + " where " + attr + " is not null;"
    faib.logMessage(logFile, stmt, DEBUG)
    cursor.execute(stmt)

    connection.commit()

    catsFile = '%s/%s_%s_number' % (catsPath,managementUnit,attr)
    if os.path.exists(catsFile):
    	os.remove(catsFile)
    	faib.logMessage(logFile, 'remove catsFile', DEBUG)
    cmd = "psql -t -c \"select %s_number||':'||%s from %s order by %s_number;\" > %s" % (attr,attr,cat_tmp,attr,catsFile)
    faib.logMessage(logFile, cmd, DEBUG)
    os.system(cmd)


    stmt = "alter table %s drop column if exists %s_number;" % (res,attr)
    faib.logMessage(logFile, stmt, DEBUG)
    cursor.execute(stmt)

    stmt = "alter table %s add column %s_number int8;" % (res,attr)
    if DEBUG:
      print stmt
    cursor.execute(stmt)

    stmt = "update " + res + " set " + attr + "_number = " + cat_tmp + "." + attr + "_number from " + cat_tmp + " where " +res + "." + attr + " = " + cat_tmp + "." + attr + ";"
    faib.logMessage(logFile, stmt, DEBUG)
    cursor.execute(stmt)

    connection.commit()

    stmt = "vacuum %s;" % (res)
    # faib.logMessage(logFile, stmt, DEBUG)
    # cursor.execute(stmt)


    stmt = "drop table if exists %s;" % (cat_tmp)
    faib.logMessage(logFile, stmt, DEBUG)
    cursor.execute(stmt)

    connection.commit()

# ==============================================================================
if __name__ == '__main__':

  message = 'start  %s %s' % (time.ctime(), logFileName)
  faib.logMessage(logFile, message,DEBUG)
  print message

  # create SELES cats folder if necessary
  if not os.path.exists(catsPath):
    os.makedirs(catsPath)

  create_cat_and_update(res, managementUnit, attr, catsPath, cat_tmp, res_tmp, DEBUG)

# --------------------------------------------------------------------------------
# done
# --------------------------------------------------------------------------------

message = 'finish %s %s' % (time.ctime(), logFileName)
faib.logMessage(logFile, message,DEBUG)
print message
