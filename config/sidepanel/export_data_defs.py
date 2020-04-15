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
        if not 'LAZY_QUERY_EXECUTION' in jdbc_url:
            jdbc_url = jdbc_url + ';LAZY_QUERY_EXECUTION=1' # Modify url for less memory use
        driver_jar = bin_dir + '/vendor/jdbc/h2-1.4.196.jar'
        driver_class = 'org.h2.Driver'

    return jdbc_url, driver_jar, driver_class


def capture_dirs(subsystem_dir, config_dir, dir_paths):
    i = 0
    for source_path in dir_paths:
        if os.path.isdir(source_path):
            i += 1
            target_path = subsystem_dir + '/content/documents/' + "dir" + str(i) + ".wim"
            print(target_path)
            if not os.path.isfile(target_path):
                capture_files(config_dir, source_path, target_path)
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
        cursor.execute('SELECT COUNT(*) from "' + table + '";')
        (row_count,)=cursor.fetchone()
        db_tables[table] = row_count

        # Get column names per table:
        cursor.execute('SELECT * from "' + table + '" limit 1') # WAIT: TOP eller rownum når mssql, oracle
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


def get_blob_tables(subsystem_dir, export_tables):  
    blob_tables = []
    schema_file = subsystem_dir + '/documentation/metadata.xml'
    tree = ET.parse(schema_file)

    table_defs = tree.findall("table-def")
    for table_def in table_defs:
        table_name = table_def.find("table-name") 
        blobs = False
        if table_name.text not in export_tables:
            continue

        column_defs = table_def.findall("column-def")
        for column_def in column_defs:
            java_sql_type = column_def.find('java-sql-type') 
            if int(java_sql_type.text) in (-4,-3,-2,2004,2005,2011):
                blob_tables.append(table_name.text)
                blobs = True
                continue

    return blob_tables 


def get_primary_keys(subsystem_dir, sync_tables):  
    pk_dict = {}
    schema_file = subsystem_dir + '/documentation/metadata.xml'
    tree = ET.parse(schema_file)

    table_defs = tree.findall("table-def")
    for table_def in table_defs:
        table_name = table_def.find("table-name") 
        pk = False
        if table_name.text not in sync_tables:
            continue

        pk_list = []
        column_defs = table_def.findall("column-def")
        for column_def in column_defs:
            column_name = column_def.find('column-name')
            primary_key = column_def.find('primary-key')            

            if primary_key.text == 'true':
                pk_list.append(column_name.text)

        if not pk_list:
            print_and_exit("Table '" + table_name.text + "' has no primary key and cannot be synced. Exiting.")
        pk_dict[table_name.text] = ', '.join(sorted(pk_list)) 

    print(pk_dict)


def table_check(incl_tables, skip_tables, sync_tables, db_tables, subsystem_dir):
    non_empty_tables = {k:v for (k,v) in db_tables.items() if v > 0}
    if incl_tables:
        for tbl in incl_tables:
            if tbl not in non_empty_tables:
                print_and_exit("Table '" + tbl + "' is empty or not in schema. Exiting.")
        for tbl in list(non_empty_tables):
            if tbl not in incl_tables:
                del non_empty_tables[tbl]
    elif skip_tables:
        for tbl in skip_tables:
            if tbl in non_empty_tables:
                del non_empty_tables[tbl]
            else:
                print_and_exit("Table '" + tbl + "' is empty or not in schema. Exiting.") 
    
    if sync_tables:
        for tbl in sync_tables:
            if tbl not in non_empty_tables:
                print_and_exit("Table '" + tbl + "' is empty or not in source schema. Exiting.")

        get_primary_keys(subsystem_dir, sync_tables)

    return non_empty_tables, sync_tables        


def copy_db_schema(subsystem_dir, db_name, db_schema, overwrite, class_path, max_java_heap, export_tables, url, db_password, bin_dir, table_columns, sync_tables):     
    std_params =  '-mode=INSERT -ignoreIdentityColumns=false -removeDefaults=true -createTarget=true -commitEvery=1000'
    if overwrite:
        std_params = std_params + ' -dropTarget=true'    
    else:
        target_path = subsystem_dir + '/documentation/' + db_name + '_' +  db_schema + '.mv.db'
        if os.path.isfile(target_path):
            print_and_exit("'" + target_path + "' already exists. Exiting")
    
    # Start Java virtual machine if not started already:
    init_jvm(class_path, max_java_heap) 

    # Create instance of sqlwb Batchrunner:
    WbManager = jp.JPackage('workbench').WbManager
    WbManager.prepareForEmbedded()
    batch = jp.JPackage('workbench.sql').BatchRunner()
    batch.setAbortOnError(True)         
    
    # TODO: Detekterer per tabell om finnes blober. Hvis ja sett commit til 500... -> Eller batch size? -> Avvent test med annet enn H2(leser hele tabell til minne?)
    # TODO: Hverken batchsize eller commitevery ser ut til å bety noe for minnebruk
    target_url = 'jdbc:h2:' + subsystem_dir + '/documentation/' + db_name + '_' +  db_schema + ';autocommit=off'

    # WAIT: Legg inn tilpasset kopiering av tabeller i blob_tables. Ta disse først i uttrekket -> flytt til først i dict export_tables
    blob_tables = get_blob_tables(subsystem_dir, export_tables)

    # TODO: Lag sjekk på sync_tables her
    
    for table, row_count in export_tables.items():
        print("Copying table '" + table + "':")
        batch.runScript("WbConnect -url='" + url + "' -password=" + db_password + ";")
        target_conn = '"username=,password=,url=' + target_url + ';LOG=0;CACHE_SIZE=65536;LOCK_MODE=0;UNDO_LOG=0" ' + std_params 
        source_query = 'SELECT "' + '","'.join(table_columns[table]) + '" FROM "' + db_schema + '"."' + table + '"' 
        quote_table = '"' + table + '"'
        copy_data_str = "WbCopy -targetConnection=" + target_conn + " -targetSchema=PUBLIC -targetTable=" + quote_table + " -sourceQuery='" + source_query + "';" 
        # batch.runScript('WbFeedback traceOff;') 
        result = batch.runScript(copy_data_str) 
        batch.runScript("WbDisconnect;")
        jp.java.lang.System.gc()
        if str(result) == 'Error':
            print_and_exit("Error on copying table '" + table + "'\nScroll up for details.")
        
    print('\nDatabase copy finished. Verifying data...')  
    verify_db_copy(class_path, max_java_heap, target_url, bin_dir, export_tables)   


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


def verify_db_copy(class_path, max_java_heap, target_url, bin_dir, export_tables):
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
        for table, row_count in export_tables.items():
            if table in target_tables:
                if not target_tables[table] == row_count:
                    print("Row count mismatch for table '" + table + "'")
                    row_errors += 1
            else:
                print("'" + table + "' missing from database copy.")

        if row_errors == 0:
            print_and_exit('Copied data rows matches source database. Create system data package now if finished extracting all system data.') 


     












