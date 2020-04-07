import os, sys
from pathlib import Path
import jpype as jp
import jpype.imports
import jaydebeapi
from database.jdbc import Jdbc

def init_jvm(class_path, max_heap_size):
    if jpype.isJVMStarted():
        return
    jpype.startJVM(jpype.getDefaultJVMPath(), 
#                            '-Djava.class.path=%s' % class_path,
                            '-Dfile.encoding=UTF8',
                            '-ea', '-Xmx{}m'.format(max_heap_size),
#                            convertStrings=True # TODO: Bare for nyere versjon av jpype?
                            )

if __name__ == '__main__':
    bin_dir = os.environ["pwcode_bin_dir"]
    data_dir = os.environ["pwcode_data_dir"]

    class_path = bin_dir + '/vendor/jdbc/sqlworkbench.jar'
    max_heap_size = 1024

    url = 'jdbc:h2:/home/bba/Desktop/DoculiveHist_dbo;LAZY_QUERY_EXECUTION=1'
    driver_jar = bin_dir + '/vendor/jdbc/h2-1.4.196.jar'
    driver_class = 'org.h2.Driver'
    user = ''
    pwd = ''    

    #conn = jaydebeapi.connect(url, user, pwd, driver_jar, driver_class)
    os.environ['CLASSPATH'] = class_path
    conn = Jdbc(url, user, pwd, driver_jar, driver_class, True, True)
    #
    #
    if conn:
        print('test')
        conn.close()
    #    jpype.shutdownJVM()



    try:
        init_jvm(class_path, max_heap_size)
        import java.lang

        WbManager = jp.JPackage('workbench').WbManager
        WbManager.prepareForEmbedded()
    #    WbManager.runEmbedded('displayResult=True', False)

        batch = jp.JPackage('workbench.sql').BatchRunner()

        batch.setBaseDir(data_dir + '/jpype_test/')
    #    batch.setStoreErrors(True)
    #    batch.setErrorScript('error.log')
    #    batch.setShowStatementWithResult(True)


    #    batch.setScriptToRun('wbexport.sql')
    #    batch.execute()

        batch.runScript("WbConnect -url='" + url + "' -password=" + pwd + ";")
        gen_report_str = '''WbSchemaReport -file=metadata.xml -schemas=PUBLIC -types=SYNONYM,TABLE,VIEW -includeProcedures=true -includeTriggers=true -writeFullSource=true;'''
        batch.runScript(gen_report_str) 

        batch.showResultSets(True) # TODO: Viser resultat da -> Fikse bedre visning i console hvordan?
    #    batch.setVerboseLogging(True)

        batch.setAbortOnError(True)
        batch.setMaxRows(20)
    #    result = batch.runScript('select * from ca_eldok;')
    #    print(str(result)) # TODO: Gir success hvis kjørt uten feil, Error hvis ikke

    #    result = batch.runScript('WbList;')


    #    print(test)
    except Exception as e:
        print(e)



#    ErrorReportLevel = jp.JPackage('workbench.sql').ErrorReportLevel
#    batch.setErrorStatementLogging(ErrorReportLevel.full)



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




























