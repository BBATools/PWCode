import os, subprocess
import jpype as jp
import jpype.imports
from pathlib import Path

# Start java virtual machine:
def init_jvm(class_path, max_heap_size):
    if jpype.isJVMStarted():
        return
    jpype.startJVM(jpype.getDefaultJVMPath(), 
                            '-Djava.class.path=%s' % class_path,
                            '-Dfile.encoding=UTF8',
                            '-ea', '-Xmx{}m'.format(max_heap_size),
                            )

def unique_dir(directory):
    counter = 0
    while True:
        counter += 1
        path = Path(directory + str(counter))
        if not path.exists():
            return path 


def ensure_dirs(data_dir, subsystem_dir):
    dirs = [
                data_dir,
                data_dir + '/administrative_metadata/',        
                data_dir + '/descriptive_metadata/',
                data_dir + '/content/documentation/',
                subsystem_dir + '/header/',
                subsystem_dir + '/content/documents/',
                subsystem_dir + '/documentation/dip/'         
                ]

    for dir in dirs:            
        Path(dir).mkdir(parents=True, exist_ok=True) 


def get_db_details(JDBC_URL, bin_dir):
    if 'jdbc:h2:' in JDBC_URL: # H2 database
        url = JDBC_URL + ';LAZY_QUERY_EXECUTION=1' # Modify url for less memory use
        driver_jar = bin_dir + '/vendor/jdbc/h2-1.4.196.jar'
        driver_class = 'org.h2.Driver'

    return url, driver_jar, driver_class


def capture_files(config_dir, source_path, target_path):
    wim_cmd = config_dir + "/vendor/wimlib-imagex capture "
    if os.name == "posix":
        wim_cmd = "wimcapture " # WAIT: Bruk tar eller annet som kan mountes på posix. Trenger ikke wim da
    subprocess.run(wim_cmd + source_path + " " + target_path + " --no-acls --compress=none", shell=True)   


def get_tables(conn, schema):
    results = conn.jconn.getMetaData().getTables(None, schema, "%", None)
    table_reader_cursor = conn.cursor()
    table_reader_cursor._rs = results
    table_reader_cursor._meta = results.getMetaData()
    read_results = table_reader_cursor.fetchall()
    tables = [row[2] for row in read_results if row[3] == 'TABLE']
    return tables   


def export_schema(class_path, MAX_JAVA_HEAP, base_dir, url,  DB_PASSWORD, DB_SCHEMA):
    init_jvm(class_path, MAX_JAVA_HEAP) # Start Java virtual machine
    WbManager = jp.JPackage('workbench').WbManager
    WbManager.prepareForEmbedded()
    batch = jp.JPackage('workbench.sql').BatchRunner()
    batch.setAbortOnError(True) 

    batch.setBaseDir(base_dir)    
    batch.runScript("WbConnect -url='" + url + "' -password=" + DB_PASSWORD + ";")
    gen_report_str = "WbSchemaReport -file=metadata.xml -schemas=" + DB_SCHEMA + " -types=SYNONYM,TABLE,VIEW -includeProcedures=true \
                            -includeTriggers=true -writeFullSource=true;"
    batch.runScript(gen_report_str) 


# TODO: Gjør ferdig og test denne:
# def copy_table(class_path, MAX_JAVA_HEAP, base_dir, url,  DB_PASSWORD, DB_SCHEMA, DB_NAME, table):
#     init_jvm(class_path, MAX_JAVA_HEAP) # Start Java virtual machine
#     WbManager = jp.JPackage('workbench').WbManager
#     WbManager.prepareForEmbedded()
#     batch = jp.JPackage('workbench.sql').BatchRunner()
#     batch.setAbortOnError(True) 

#     target_url = 'jdbc:h2:' + base_dir + DB_NAME + '_' +  DB_SCHEMA
#     std_params =  '-mode=INSERT -commitEvery=10000 -ignoreIdentityColumns=false -removeDefaults=true -showProgress=10000 -createTarget=true'
#     target_conn = '"username=,password=,url=' + target_url + ';LOG=0;CACHE_SIZE=65536;LOCK_MODE=0;UNDO_LOG=0" ' + std_params 
#     copy_data_str = 'WbCopy -targetConnection=' + target_conn + ' -sourceSchema=' + DB_SCHEMA + ' -targetSchema=PUBLIC  -sourceTable=' + table + ' -targetTable=' + table + ';' 
#     batch.runScript(copy_data_str) 






















