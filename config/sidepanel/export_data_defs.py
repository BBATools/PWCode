import os, sys, subprocess
import jpype as jp
import jpype.imports
from pathlib import Path
import xml.etree.ElementTree as ET
from database.jdbc import Jdbc

# Start java virtual machine:
def init_jvm(class_path, max_heap_size):
    if jpype.isJVMStarted():
        return
    jpype.startJVM(jpype.getDefaultJVMPath(), 
                            '-Djava.class.path=%s' % class_path,
                            '-Dfile.encoding=UTF8',
                            '-ea', max_heap_size,
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


def get_db_details(jdbc_url, bin_dir):
    if 'jdbc:h2:' in jdbc_url: # H2 database
        url = jdbc_url + ';LAZY_QUERY_EXECUTION=1;LOB_TIMEOUT=500' # Modify url for less memory use
        driver_jar = bin_dir + '/vendor/jdbc/h2-1.4.196.jar'
        driver_class = 'org.h2.Driver'

    return url, driver_jar, driver_class


def capture_dirs(subsystem_dir, config_dir, file_paths, overwrite):
    i = 0
    for source_path in file_paths:
        if os.path.isdir(source_path):
            i += 1
            target_path = subsystem_dir + '/content/documents/' + "dir" + str(i) + ".wim"
            if not os.path.isfile(target_path) or overwrite == True:
                capture_files(config_dir, source_path, target_path)
            else:
                print_and_exit(target_path + ' already exsists. Exiting.')
        else:
            print_and_exit(source_path + ' is not a valid path. Exiting.')    


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


def export_schema(class_path, max_java_heap, base_dir, url, db_password, db_schema):
    init_jvm(class_path, max_java_heap) # Start Java virtual machine
    WbManager = jp.JPackage('workbench').WbManager
    WbManager.prepareForEmbedded()
    batch = jp.JPackage('workbench.sql').BatchRunner()
    batch.setAbortOnError(True) 

    batch.setBaseDir(base_dir)    
    batch.runScript("WbConnect -url='" + url + "' -password=" + db_password + ";")
    gen_report_str = "WbSchemaReport -file=metadata.xml -schemas=" + db_schema + " -types=SYNONYM,TABLE,VIEW -includeProcedures=true \
                            -includeTriggers=true -writeFullSource=true;"
    batch.runScript(gen_report_str) 


def print_and_exit(msg):
    print(msg)
    sys.exit()


def get_db_meta(jdbc, db_schema):
    db_tables = {}
    table_columns = {}
    conn= jdbc.connection                        
    cursor = conn.cursor()                        
    tables = get_tables(conn, db_schema)

    # Get row count per table:
    for table in tables:
        cursor.execute("SELECT COUNT(*) from " + table)
        (row_count,)=cursor.fetchone()
        db_tables[table] = row_count

        # Get column names per table:
        cursor.execute("SELECT * from " + table + ' limit 1') # WAIT: TOP eller rownum når mssql, oracle
        columns = [desc[0] for desc in cursor.description]
        table_columns[table] = columns              

    cursor.close()
    conn.close()
    return db_tables, table_columns


def indent(elem, level=0):
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i
                

def add_row_count_to_schema_file(subsystem_dir, db_tables):
    schema_file = subsystem_dir + '/documentation/metadata.xml'
    tree = ET.parse(schema_file)

    table_defs = tree.findall("table-def")
    for table_def in table_defs:
        table_name = table_def.find("table-name")

        disposed = ET.Element("disposed")
        disposed.text = "false"
        disposal_comment = ET.Element("disposal_comment")
        disposal_comment.text = " "
        rows = ET.Element("rows")

        row_count = db_tables[table_name.text]
        if row_count == 0:
            disposed.text = "true"
            disposal_comment.text = "Empty table"
        rows.text = str(row_count)

        table_def.insert(5, rows)
        table_def.insert(6, disposed)
        table_def.insert(7, disposal_comment)

    root = tree.getroot()
    indent(root)
    tree.write(schema_file)   


def overwrite_db_copy_maybe(subsystem_dir, db_name, db_schema, overwrite):
    target_path = subsystem_dir + '/documentation/' + db_name + '_' +  db_schema
    if os.path.isfile(target_path + '.mv.db') and overwrite == False:
        print_and_exit("'" + target_path + ".mv.db' already exists. Exiting")
    else:
        if os.path.isfile(target_path + '.mv.db'):
            os.remove(target_path + '.mv.db')
        if os.path.isfile(target_path + '.trace.db'):
            os.remove(target_path + '.trace.db')               


def copy_db_schema(subsystem_dir, db_name, db_schema, overwrite, class_path, max_java_heap, non_empty_tables, url, db_password, bin_dir):     
    init_jvm(class_path, max_java_heap) # Start Java virtual machine if not started already
    WbManager = jp.JPackage('workbench').WbManager
    WbManager.prepareForEmbedded()
    batch = jp.JPackage('workbench.sql').BatchRunner()
    batch.setAbortOnError(True) 
    target_url = 'jdbc:h2:' + subsystem_dir + '/documentation/' + db_name + '_' +  db_schema + ';autocommit=off'

    overwrite_db_copy_maybe(subsystem_dir, db_name, db_schema, overwrite)            
    
    # TODO: Detekterer per tabell om finnes blober. Hvis ja sett commit til 500... -> Eller batch size? -> Avvent test med annet enn H2(leser hele tabell til minne?)
    # TODO: Hverken batchsize eller commitevery ser ut til å bety noe for minnebruk

    for table, row_count in non_empty_tables.items():
        print("Copying table '" + table + "':")
        batch.runScript("WbConnect -url='" + url + "' -password=" + db_password + ";")

        std_params =  '-mode=INSERT -ignoreIdentityColumns=false -removeDefaults=true -createTarget=true -commitEvery=1000'
        target_conn = '"username=,password=,url=' + target_url + ';LOG=0;CACHE_SIZE=65536;LOCK_MODE=0;UNDO_LOG=0" ' + std_params 
        copy_data_str = 'WbCopy -targetConnection=' + target_conn + ' -targetSchema=PUBLIC  -sourceTable=' + table + ' -targetTable=' + table + ';' 
        # TODO: Virker bare uten sourceschema siden det er default schema det hentes fra? Spesifiser sechema i connection? Del av tabellnavn?
#                copy_data_str = 'WbCopy -targetConnection=' + target_conn + ' -sourceSchema=' + DB_SCHEMA + ' -targetSchema=PUBLIC  -sourceTable=' + table + ' -targetTable=' + table + ';' 
#                batch.runScript('WbFeedback traceOff;') 
        result = batch.runScript(copy_data_str) 
        batch.runScript("WbDisconnect;")
        jp.java.lang.System.gc()
        if str(result) == 'Error':
            print_and_exit("Error on copying table '" + table + "'\nScroll up for details.")
        
    print('\nDatabase copy finished. Verifying data...')  
    verify_db_copy(class_path, max_java_heap, target_url, bin_dir, non_empty_tables)   


#        

#-showProgress=10000 -targetSchema=PUBLIC -createTarget=true -targetTable="CA_ELDOK" -sourceQuery='SELECT "ELDOKID", "KATEGORI", "BESKRIVELSE", "PAPIR", "LOKPAPIR", "ELDOKSTATUS", "UTARBAV", "BEGRENSNING", "GRADVEKT", "AVSKJERMING", "UOFF", "AVGRADERING", "NEDGRADDATO", "GRUPPE", "ANTVERS", "AVLEVER" FROM "CA_ELDOK"'; COMMIT;




#        batch.setStoreErrors(True)
#        batch.setErrorScript('error.log')
#        batch.setShowStatementWithResult(True)
#        batch.setScriptToRun('wbexport.sql')
#        batch.execute()
#        batch.showResultSets(True) # TODO: Viser resultat da -> Fikse bedre visning i console hvordan?
#        batch.setVerboseLogging(True)
#        batch.setMaxRows(20)
#        result = batch.runScript('select * from ca_eldok;')
#        print(str(result)) # TODO: Gir success hvis kjørt uten feil, Error hvis ikke
#        result = batch.runScript('WbList;')    


def verify_db_copy(class_path, max_java_heap, target_url, bin_dir, non_empty_tables):
    # Check if row count matches source database:
    init_jvm(class_path, max_java_heap) # Start Java virtual machine if not started already
    url, driver_jar, driver_class = get_db_details(target_url, bin_dir)
    jdbc = Jdbc(url, '', '', driver_jar, driver_class, True, True)
    target_tables = {}
    if jdbc:
        conn= jdbc.connection                        
        cursor = conn.cursor()                        
        tables = get_tables(conn, 'PUBLIC')

        # Get row count per table:
        for table in tables:
            cursor.execute("SELECT COUNT(*) from " + table)
            (row_count,)=cursor.fetchone()
            target_tables[table] = row_count          

        cursor.close()
        conn.close()

        row_errors = 0
        for table, row_count in non_empty_tables.items():
            if table in target_tables:
                if not target_tables[table] == row_count:
                    print("Row count mismatch for table '" + table + "'")
                    row_errors += 1
            else:
                print("'" + table + "' missing from database copy.")

        if row_errors == 0:
            print('Copied data rows matches source database. Create system data package now if finished extracting all system data.') 














