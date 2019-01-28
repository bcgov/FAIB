import sys

# get ready to import local modules
# define the path to the modules and append it to the system path
module_path = '//spatialfiles2.bcgov/work/FOR/VIC/HTS/ANA/Workarea/TOOLS/python/PythonLib/Production'
sys.path.append(module_path)

# continue importing modules
import FAIB_Tools as faib
import time, psycopg2

# usage
if len(sys.argv) < 2:
  print "Usage: join_geometry2resultants.py [res_table]"
  sys.exit(0)
  
# system arguments
res = sys.argv[1]

# FAIB parameters
parameterFileName = "projectParameters.txt"
parameters = {}
parametersNeeded = {}
parametersNeeded["managementUnit"] = "Management Unit/project prefix"
parametersNeeded["DEBUG"] = "DEBUG = True or False"
faib.getProjectParameters(parameterFileName, parameters, parametersNeeded)
managementUnit = parameters["managementUnit"]
if (parameters["DEBUG"] == 'False'):
  DEBUG = False
else:
  DEBUG = True
logFileName = managementUnit+'_join_geometry2resultants.log'
logFile = file(logFileName, "w")

# local variables
res = managementUnit+'_'+res
skey = managementUnit+'_skey'

# --------------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------------

message = 'start  %s %s' % (time.ctime(), logFileName)
faib.logMessage(logFile, message,DEBUG)
print message


message = 'Adding geometry to %s...' % (res)
faib.logMessage(logFile, message,DEBUG)

connection = psycopg2.connect("dbname=postgres user=postgres")
cursor = connection.cursor()
if connection:

  stmt = "alter table %s drop column if exists wkb_geometry;" % (res)
  faib.logMessage(logFile, stmt,DEBUG)
  cursor.execute(stmt)

  stmt = "select AddGeometryColumn('%s','wkb_geometry',3005,'POLYGON',2);" % (res)
  faib.logMessage(logFile, stmt,DEBUG)
  cursor.execute(stmt)
  connection.commit()

  message = 'Indexing...'
  faib.logMessage(logFile, message,DEBUG)

  stmt = "drop index if exists idx1;"
  faib.logMessage(logFile, stmt,DEBUG)
  cursor.execute(stmt)
  
  stmt = "drop index if exists idx2;"
  faib.logMessage(logFile, stmt,DEBUG)
  cursor.execute(stmt)

  stmt = "create index idx1 on %s(ogc_fid);" % (res)
  faib.logMessage(logFile, stmt,DEBUG)
  cursor.execute(stmt)

  stmt = "create index idx2 on %s(ogc_fid);" % (skey)
  faib.logMessage(logFile, stmt,DEBUG)
  cursor.execute(stmt)

  connection.commit()

  stmt = "update " + res + \
         " set wkb_geometry = s.wkb_geometry" + \
         " from " + skey + " s" + \
         " where " + res + ".ogc_fid = s.ogc_fid;"
  faib.logMessage(logFile, stmt,DEBUG)
  cursor.execute(stmt)

  connection.commit()

  stmt = "drop index if exists idx1;"
  faib.logMessage(logFile, stmt,DEBUG)
  cursor.execute(stmt)
  
  stmt = "drop index if exists idx2;"
  faib.logMessage(logFile, stmt,DEBUG)
  cursor.execute(stmt)

  old_isolation_level = connection.isolation_level
  connection.set_isolation_level(0)
  stmt = "vacuum full %s;" % (res)
  faib.logMessage(logFile, stmt,DEBUG)
  cursor.execute(stmt)
  connection.set_isolation_level(old_isolation_level)

  cursor.close()
  connection.close()

message = 'finish %s %s' % (time.ctime(), logFileName)
faib.logMessage(logFile, message,DEBUG)
print message
