import os, sys
from pathlib import Path
import jpype as jp
#from jpype import JPackage, startJVM, getDefaultJVMPath, JClass

bin_dir = os.environ["pwcode_bin_dir"]
data_dir = os.environ["pwcode_data_dir"]
class_path = bin_dir + '/vendor/jdbc/sqlworkbench.jar'

# TODO: Se her:
#https://groups.google.com/forum/#!topicsearchin/sql-workbench/runEmbedded;context-place=topic/sql-workbench/AI9YtxkfNT4/sql-workbench/imMesRCaMFA
#https://jpype.readthedocs.io/en/latest/quickguide.html
#http://sqlworkbench.mgm-tp.com/viewvc/trunk/sqlworkbench/src/workbench/WbManager.java?view=log
#https://groups.google.com/forum/#!msg/sql-workbench/g7JCxVkVJW0/nOLNJKR1BQAJ
#https://groups.google.com/forum/#!topicsearchin/sql-workbench/runEmbedded;context-place=topic/sql-workbench/AI9YtxkfNT4/sql-workbench/imMesRCaMFA
#https://stackoverflow.com/questions/56760450/redirect-jar-output-when-called-via-jpype-in-python
#https://stackoverflow.com/questions/15959004/how-do-i-import-user-built-jars-in-python-using-jpype


try:
    import jpype.imports
    jp.startJVM(jpype.getDefaultJVMPath(), "-ea", "-Djava.class.path=" + class_path)
    import java.lang
    jp.imports.registerDomain('workbench') 
#    from workbench import WbManager

#    wb = jp.JClass('WbManager')()

    wbmanager = jp.JClass('workbench.WbManager')
    arg = jp.JArray(jp.JString)('-script=' + bin_dir + '/h2_to_tsv.sql')
#    arg = jp.JString('-script=' + bin_dir + '/h2_to_tsv.sql')

    wbmanager.prepareForEmbedded()
    wbmanager.runEmbedded(arg, True)

#    wbmanager.prepareForEmbedded(arg, True)
#    wbmanager.prepareForEmbedded(jp.JArray(jp.JChar)([arg]), True)


#    wbmanager.prepareForEmbedded()
#    wbmanager.startApplication()
#    jpype.shutdownJVM()



#    from workbench import WbManager
#    import workbench
#    JClass("workbench.WbManager").prepareForEmbedded()

#    from workbench.sql import BatchRunner

#    JClass("workbench.sql.BatchRunner").BatchRunner()
#    JClass("workbench.sql.BatchRunner").BatchRunner(data_dir + 'test.sql')

#    JClass("workbench.WbManager").runEmbedded(new String[] {-logfile="/home/bba/test.log"}, false)
#    JClass("workbench.WbManager").runEmbedded(null, false)

#  WbManager.runEmbedded(new String[] {"-logfile=c:/temp/wbimport.log"}, false); 
#    JClass("workbench.WbStarter").main()
#    JClass("workbench.WbStarter").main(new String[] { "a", "b" })
    print('success')
#    startJVM(bin_dir+ '/vendor/linux/jre/bin/java', "-ea", "-Djava.class.path=" + class_path)
except Exception as e:
    print(e)


