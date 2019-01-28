# Import system modules
import sys, string, os

# usage
if len(sys.argv) < 2:
  print "Usage: setTSA.py <template> <TSA>"
  sys.exit(0)

# list file
template = sys.argv[1]
tsa = sys.argv[2]

# open template and project parameters file
inParam = open(template,"r")
outParam = open('projectParameters.txt',"w")

for s in inParam.xreadlines():
  outParam.write(s.replace('TSAxx', tsa))

# close project parameters files
# inParam.close()
# outParam.close()