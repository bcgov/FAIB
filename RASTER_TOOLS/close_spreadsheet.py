# ================================================================================
# NAME:
#    close_spreadsheet.py
#
# FUNCTION:
#   - close a spreadsheet containing database of wrk feature classes
#
# HISTORY:
#   20161007 Doug Layden -- original coding from mkresultants.py
#
# ================================================================================

import sys

# get ready to import local modules
# define the path to the modules and append it to the system path
module_path = '//spatialfiles2.bcgov/work/FOR/VIC/HTS/ANA/Workarea/TOOLS/python/PythonLib/Production'
sys.path.append(module_path)

# continue importing modules
import FAIB_Tools as faib
import string, os, time
import psycopg2
from win32com.client import Dispatch
	
# ============================================================================
# hardcoded values
# ============================================================================
parameterFileName = "projectParameters.txt"
parameters = {}
parametersNeeded = {}
parametersNeeded["dataDictionary"] = "project data dictionary"
faib.getProjectParameters(parameterFileName, parameters, parametersNeeded)

# --------------------------------------------------------------------------------
# local variables
# --------------------------------------------------------------------------------

# ============================================================================
# MAIN
# ============================================================================

# --------------------------------------------------------------------------------
# local variables
# --------------------------------------------------------------------------------
dataDictionary = parameters["dataDictionary"]

if not os.path.isfile(dataDictionary):
  print("Data dictionary '" + dataDictionary + "' not found.")
  sys.exit(1)	

print 'closing', dataDictionary

xl = Dispatch("Excel.Application")
workbook = xl.Workbooks.Open(dataDictionary)

# --------------------------------------------------------------------------------
# close the spreadsheet
# --------------------------------------------------------------------------------
xl.ActiveWorkbook.Close(SaveChanges=0)
worksheet = None
workbook = None
xl.Quit()
xl = None
