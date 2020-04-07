import os, sys
from pathlib import Path
import jpype as jp
import jpype.imports


bin_dir = os.environ["pwcode_bin_dir"]
data_dir = os.environ["pwcode_data_dir"]
class_path = bin_dir + '/vendor/jdbc/sqlworkbench.jar'



try:
    jp.startJVM(jpype.getDefaultJVMPath(), "-ea", "-Djava.class.path=%s"%class_path)
    import java.lang

    WbManager = jp.JPackage('workbench').WbManager
    WbManager.prepareForEmbedded()
#    WbManager.runEmbedded('displayResult=True', False)

    batch = jp.JPackage('workbench.sql').BatchRunner()
    batch.setBaseDir(data_dir + '/jpype_test/')
    batch.setErrorScript('error.log')

#    batch.setScriptToRun('wbexport.sql')
#    batch.execute()

    batch.runScript('''WbConnect -url="jdbc:h2:/home/bba/Desktop/DoculiveHist_dbo;LAZY_QUERY_EXECUTION=1" -password='';''')
#    gen_report_str = '''WbSchemaReport -file=metadata.xml -schemas=PUBLIC -types=SYNONYM,TABLE,VIEW -includeProcedures=true -includeTriggers=true -writeFullSource=true;'''
#    batch.runScript(gen_report_str) 
    batch.runScript('select * from ca_eldok;')

except Exception as e:
    print(e)







#    startJVM(bin_dir+ '/vendor/linux/jre/bin/java', "-ea", "-Djava.class.path=" + class_path)
#    jp.imports.registerDomain('workbench') 
#    from workbench import WbManager



#    JClass("workbench.WbManager").runEmbedded(new String[] {-logfile="/home/bba/test.log"}, false)
#    JClass("workbench.WbManager").runEmbedded(null, false)


#    wb = WbManager()

#    BatchRunner([jp.JString('-script'), jp.JString(bin_dir + '/h2_to_tsv.sql')])

# TODO: Se her:
#https://groups.google.com/forum/#!topicsearchin/sql-workbench/runEmbedded;context-place=topic/sql-workbench/AI9YtxkfNT4/sql-workbench/imMesRCaMFA
#https://jpype.readthedocs.io/en/latest/quickguide.html
#http://sqlworkbench.mgm-tp.com/viewvc/trunk/sqlworkbench/src/workbench/WbManager.java?view=log
#https://groups.google.com/forum/#!msg/sql-workbench/g7JCxVkVJW0/nOLNJKR1BQAJ
#https://groups.google.com/forum/#!topicsearchin/sql-workbench/runEmbedded;context-place=topic/sql-workbench/AI9YtxkfNT4/sql-workbench/imMesRCaMFA
#https://stackoverflow.com/questions/56760450/redirect-jar-output-when-called-via-jpype-in-python
#https://stackoverflow.com/questions/15959004/how-do-i-import-user-built-jars-in-python-using-jpype
#https://github.com/costin/sqlworkbench

#    br = BatchRunner([jp.JString('-script'), jp.JString(bin_dir + '/h2_to_tsv.sql')])
#    BatchRunner.runScript() 
#    BatchRunner(['-script', bin_dir + '/h2_to_tsv.sql'])

#     jp.startJVM(jpype.getDefaultJVMPath(), "-ea", "-Djava.class.path=%s"%class_path)

#    ExtentReports = JClass('com.relevantcodes.extentreports.ExtentReports')

#    jp.imports.registerDomain('workbench.sql') 
#    from workbench import sql
#     from workbench.sql import BatchRunner

#    wb = jp.JClass('WbManager')()

#    wbmanager = jp.JClass('workbench.WbManager')
#    arg = jp.JArray(jp.JString)('-script=' + bin_dir + '/h2_to_tsv.sql')
#    arg = jp.JString('-script=' + bin_dir + '/h2_to_tsv.sql')

#    jp.JClass("workbench.WbStarter").main(['-script', bin_dir + '/h2_to_tsv.sql'])
#    jp.JClass("workbench.sql").BatchRunner(['-script', bin_dir + '/h2_to_tsv.sql'])

#     Bjp.JClass("workbench.sql.BatchRunner")

#    wbmanager.prepareForEmbedded()
#    CommandLine.main(['-i', input_file, '-o', output_file])
#    wbmanager.runEmbedded(['-script', bin_dir + '/h2_to_tsv.sql'], True)

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


















