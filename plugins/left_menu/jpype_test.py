import os, sys
from pathlib import Path
#from database.jdbc import Jdbc

from pathlib import Path
#from collections import OrderedDict
#from decimal import Decimal
from jpype import JPackage, startJVM, getDefaultJVMPath

bin_dir = os.environ["pwcode_bin_dir"]

#print(getDefaultJVMPath())


#sys.exit()

class_path = bin_dir + '/vendor/sqlwbj/sqlworkbench.jar'

try:
    startJVM(getDefaultJVMPath(), "-ea", "-Djava.class.path=" + class_path)
#    startJVM(bin_dir+ '/vendor/linux/jre/bin/java', "-ea", "-Djava.class.path=" + class_path)
except Exception as e:
    print(e)

print('test')

#data_dir = os.environ["pwcode_data_dir"] + '/test_lob_extract'
#Path(data_dir).mkdir(parents=True, exist_ok=True)



            




























































