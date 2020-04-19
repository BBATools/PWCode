import os, sys, subprocess
import jpype as jp
import jpype.imports
from pathlib import Path
import xml.etree.ElementTree as ET
from database.jdbc import Jdbc
from toposort import toposort, toposort_flatten

# Start java virtual machine:
def init_jvm(class_path, max_heap_size):
    if jpype.isJVMStarted():
        return
    jpype.startJVM(jpype.getDefaultJVMPath(), 
                            '-Djava.class.path=%s' % class_path,
                            # '-Dworkbench.db.h2.create.table.temp="CREATE LOCAL TEMPORARY TABLE %fq_table_name% ( %columnlist% %pk_definition%)"'
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
            jdbc_url = jdbc_url + ';LAZY_QUERY_EXECUTION=1;' # Modify url for less memory use
        driver_jar = bin_dir + '/vendor/jdbc/h2-1.4.199.jar'            
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


def export_schema(class_path, max_java_heap, subsystem_dir, jdbc):
    base_dir = subsystem_dir + '/documentation/'
    if os.path.isfile(base_dir + 'metadata.xml'):
        return

    init_jvm(class_path, max_java_heap) # Start Java virtual machine
    WbManager = jp.JPackage('workbench').WbManager
    WbManager.prepareForEmbedded()
    batch = jp.JPackage('workbench.sql').BatchRunner()
    batch.setAbortOnError(True) 

    batch.setBaseDir(base_dir)    
    batch.runScript("WbConnect -url='" + jdbc.url + "' -password=" + jdbc.pwd + ";")
    gen_report_str = "WbSchemaReport -file=metadata.xml -schemas=" + jdbc.db_schema + " -types=SYNONYM,TABLE,VIEW -includeProcedures=true \
                            -includeTriggers=true -writeFullSource=true;"
    batch.runScript(gen_report_str) 


def print_and_exit(msg):
    print(msg)
    sys.exit()


def get_db_meta(jdbc):
    db_tables = {}
    table_columns = {}
    conn= jdbc.connection                        
    cursor = conn.cursor()                        
    tables = get_tables(conn, jdbc.db_schema)

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

    return non_empty_tables, sync_tables    
 


def wb_batch(class_path, max_java_heap):  
    # Start Java virtual machine if not started already:
    init_jvm(class_path, max_java_heap) 

    # Create instance of sqlwb Batchrunner:
    WbManager = jp.JPackage('workbench').WbManager
    WbManager.prepareForEmbedded()
    batch = jp.JPackage('workbench.sql').BatchRunner()
    batch.setAbortOnError(True)    
    return batch   


def get_target_tables(jdbc):
    target_tables = {}
    conn = jdbc.connection                        
    cursor = conn.cursor()                        
    tables = get_tables(conn, jdbc.db_schema)

    # Get row count per table:
    for table in tables:
        cursor.execute('SELECT COUNT(*) from "' + table + '";')
        (row_count,)=cursor.fetchone()
        target_tables[table] = row_count

    cursor.close()
    conn.close()
    return target_tables


def get_primary_keys(subsystem_dir, export_tables,sync_tables):  
    pk_dict = {}
    schema_file = subsystem_dir + '/documentation/metadata.xml'
    tree = ET.parse(schema_file)

    table_defs = tree.findall("table-def")
    for table_def in table_defs:
        table_name = table_def.find("table-name") 
        pk = False
        if table_name.text not in export_tables:
            continue

        pk_list = []
        column_defs = table_def.findall("column-def")
        for column_def in column_defs:
            column_name = column_def.find('column-name')
            primary_key = column_def.find('primary-key')            

            if primary_key.text == 'true':
                pk_list.append(column_name.text)

        if not pk_list:
            if table_name.text in sync_tables:
                print_and_exit("Table '" + table_name.text + "' has no primary key and cannot be synced. Exiting.")
        else:                
            pk_dict[table_name.text] = pk_list

    return pk_dict


def run_ddl(jdbc, sql):
    result = 'Success'
    try:
        conn = jdbc.connection                        
        cursor = conn.cursor()  
        cursor.execute(sql)                              
        cursor.close()
        conn.commit()
        conn.close()  
    except Exception as e:
        result = e

    if result != 'Success':
        print_and_exit(result)  


def run_select(jdbc, sql):
    conn = jdbc.connection                        
    cursor = conn.cursor()  
    cursor.execute(sql)  
    result = cursor.fetchall()               
    cursor.close()
    conn.close()
    return result


def copy_db_schema(subsystem_dir, s_jdbc, class_path, max_java_heap, export_tables, bin_dir, table_columns, sync_tables, DDL_GEN): 
    blob_tables = get_blob_tables(subsystem_dir, export_tables)     
    batch = wb_batch(class_path, max_java_heap)
    target_url = 'jdbc:h2:' + subsystem_dir + '/documentation/' + s_jdbc.db_name + '_' +  s_jdbc.db_schema + ';autocommit=off'
    target_url, driver_jar, driver_class = get_db_details(target_url, bin_dir)
    t_jdbc = Jdbc(target_url, '', '', '', 'PUBLIC', driver_jar, driver_class, True, True)
    target_tables = get_target_tables(t_jdbc)
    pk_dict = get_primary_keys(subsystem_dir, export_tables, sync_tables)

    if DDL_GEN == 'PWCode':
        ddl_columns = get_ddl_columns(subsystem_dir)
    
    mode = '-mode=INSERT'
    std_params = ' -ignoreIdentityColumns=false -removeDefaults=true -commitEvery=1000 ' 
    p_key = '' 
    for table, row_count in export_tables.items():
        params = mode + std_params
        source_query = 'SELECT "' + '","'.join(table_columns[table]) + '" FROM "' + s_jdbc.db_schema + '"."' + table + '"' 

        if table in sync_tables and table in target_tables: # TODO: Test denne med compound key
            params = '-mode=UPDATE,INSERT' + std_params
            p_key = ' -keyColumns=' + ', '.join(pk_dict[table]) # WAIT: Trengs det quotes for kolonnenavn her hvis ulovlig navn?
        elif DDL_GEN == 'SQLWB':                 
            params = mode + std_params + ' -createTarget=true -dropTarget=true' 
        elif DDL_GEN == 'PWCode' and table not in target_tables:
            t_jdbc = Jdbc(target_url, '', '', '', 'PUBLIC', driver_jar, driver_class, True, True)               
            ddl = '\nCREATE TABLE "' + table + '"\n(\n' + ddl_columns[table][:-1] + '\n);'
            if table in pk_dict:
                for col in pk_dict[table]:
                    ddl = ddl + '\nCREATE INDEX c_' +  col + ' ON "' + table + '" ("' + col + '");'
            print(ddl)
            sql = 'DROP TABLE IF EXISTS "' + table + '"; ' + ddl
            run_ddl(t_jdbc, sql)
        else:
            t_row_count = target_tables[table]
            if t_row_count == row_count:
                print("Table '" + table + "' is already exported.")
                continue
            elif table in pk_dict: # TODO: Test denne med compound key          
                source_query = source_query + ' WHERE ('
                target_query = 'SELECT '
                for col in pk_dict[table]:
                    source_query = source_query + '"' + col + '", '
                    target_query = target_query + '"' + col + '", '
                source_query = source_query[:-2]
                target_query = target_query[:-2] + ' FROM "' + table + '";' 

                t_jdbc = Jdbc(target_url, '', '', '', 'PUBLIC', driver_jar, driver_class, True, True)  
                target_values = run_select(t_jdbc, target_query)
                if len(pk_dict[table]) > 1: # Compound key
                    source_query = source_query + ') NOT IN (' + ', '.join(map(str, target_values)) + ')' 
                else:
                    source_query = source_query + ') NOT IN (' + ','.join(map(str, ([x[0] for x in target_values]))) + ')'                        
            else:
                print('hva her')               

        print("Copying table '" + table + "':")
        batch.runScript("WbConnect -url='" + s_jdbc.url + "' -password=" + s_jdbc.pwd + ";")
        target_conn = '"username=,password=,url=' + target_url + ';" ' + params 
        target_table = '"' + table + '"'
        copy_data_str = "WbCopy -targetConnection=" + target_conn + " -targetSchema=PUBLIC -targetTable=" + target_table + " -sourceQuery='" + source_query + "'" + p_key + ";" 
        result = batch.runScript(copy_data_str) 
        batch.runScript("WbDisconnect;")
        jp.java.lang.System.gc()
        if str(result) == 'Error':
            print_and_exit("Error on copying table '" + table + "'\nScroll up for details.")

    print('Database export complete.')            


# WAIT: Mangler disse for å ha alle i JDBC 4.0: ROWID=-8 og SQLXML=2009
#                        jdbc-id  iso-name               jdbc-name
jdbc_to_iso_data_type = {
                         '-16'  : 'clob',               # LONGNVARCHAR
                         '-15'  : 'varchar',            # NCHAR                       
                         '-9'   : 'varchar',            # NVARCHAR                                                                                                                                                                                                                                                                                                                                                  
                         '-7'   : 'boolean',            # BIT                          
                         '-6'   : 'integer',            # TINYINT                                                                          
                         '-5'   : 'integer',            # BIGINT
                         '-4'   : 'blob',               # LONGVARBINARY
                         '-3'   : 'blob',               # VARBINARY
                         '-2'   : 'blob',               # BINARY                      
                         '-1'   : 'clob',               # LONGVARCHAR
                         '1'    : 'varchar',            # CHAR
                         '2'    : 'numeric',            # NUMERIC  # TODO: Se xslt for ekstra nyanser på denne  
                         '3'    : 'decimal',            # DECIMAL  # TODO: Se xslt for ekstra nyanser på denne    
                         '4'    : 'integer',            # INTEGER 
                         '5'    : 'integer',            # SMALLINT
                         '6'    : 'float',              # FLOAT   
                         '7'    : 'real',               # REAL
                         '8'    : 'double precision',   # DOUBLE 
                         '12'   : 'varchar',            # VARCHAR 
                         '16'   : 'boolean',            # BOOLEAN
                         '91'   : 'date',               # DATE                        
                         '92'   : 'time',               # TIME
                         '93'   : 'timestamp',          # TIMESTAMP                                                                                                
                         '2004' : 'blob',               # BLOB 
                         '2005' : 'clob',               # CLOB
                         '2011' : 'clob',               # NCLOB
}            

# WAIT: Sortere long raw sist eller først for å unngå bug i driver?
# -> https://blog.jooq.org/tag/long-raw/
def get_ddl_columns(subsystem_dir):
    ddl_columns = {}
    schema_file = subsystem_dir + '/documentation/metadata.xml'
    tree = ET.parse(schema_file)

    table_defs = tree.findall("table-def")
    for table_def in table_defs:
        table_name = table_def.find("table-name")
        disposed = table_def.find("disposed")    

        ddl_columns_list = []
        column_defs = table_def.findall("column-def")
        for column_def in column_defs:
            column_name = column_def.find('column-name')
            java_sql_type = column_def.find('java-sql-type')
            dbms_data_size = column_def.find('dbms-data-size')
                
            if disposed.text != "true":
                iso_data_type = jdbc_to_iso_data_type[java_sql_type.text]
                if '()' in iso_data_type:
                    iso_data_type = iso_data_type.replace('()', '(' + dbms_data_size.text + ')')
                
                ddl_columns_list.append('"' + column_name.text + '" ' + iso_data_type + ',')                            


        ddl_columns[table_name.text] =  '\n'.join(ddl_columns_list)  

    return ddl_columns              









