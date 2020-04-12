############### USER INPUT ###############

SYSTEM_NAME = 'test'
DB_NAME = 'DOCULIVEHIST_DBO'
DB_SCHEMA = 'PUBLIC'
JDBC_URL = 'jdbc:h2:/home/bba/Desktop/DoculiveHist_dbo'
DB_USER = ''
DB_PASSWORD = ''
FILE_PATHS = [
#                        "path/to/extract/on/linux", 
                        "/home/bba/Downloads/python/"        
#                        "c:\path\on\windows"
                     ]
OVERWRITE = True # Overwrite extracted data if previous extraction detected
MAX_JAVA_HEAP = '-Xmx6g'

################# CODE #################

# Import external code:
import os, sys
from pathlib import Path
import jpype as jp
import jpype.imports
from database.jdbc import Jdbc
from export_data_defs import *


# Start execution:
if __name__ == '__main__':
    db_tables = {}
    non_empty_tables = {}
    table_columns = {}
    bin_dir = os.environ["pwcode_bin_dir"] # Get PWCode executable path
    class_path = os.environ['CLASSPATH'] # Get Java jar path
    config_dir = os.environ["pwcode_config_dir"] # Get PWCode config path

    if SYSTEM_NAME:
        data_dir = os.environ["pwcode_data_dir"] + SYSTEM_NAME # --> projects/[system]

        if DB_NAME and DB_SCHEMA:
            url, driver_jar, driver_class = get_db_details(JDBC_URL, bin_dir)
            if driver_jar and driver_class:
                try:
                    jdbc = Jdbc(url, DB_USER, DB_PASSWORD, driver_jar, driver_class, True, True)
                    if jdbc:
                        conn= jdbc.connection                        
                        cursor = conn.cursor()                        
                        tables = get_tables(conn, DB_SCHEMA)

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
                
                    non_empty_tables = {k:v for (k,v) in db_tables.items() if v > 0}
                    if non_empty_tables:
                        subsystem_dir = data_dir + '/content/sub_systems/' + DB_NAME + '_' + DB_SCHEMA
                    else:
                        print('Database is empty. Exiting.')
                        sys.exit()
                except Exception as e:
                    print(e)
                    sys.exit()
            else:
                print('Not a supported jdbc url. Exiting')
                sys.exit()
        elif FILE_PATHS:
            subsystem_dir = str(unique_dir(data_dir + '/content/sub_systems/' + SYSTEM_NAME))
        else:
            print('Missing db or file paths. Exiting.')
            sys.exit()
    else:
        print('Missing system name. Exiting.')
        sys.exit()

    ensure_dirs(data_dir, subsystem_dir) # Create directories if not exists


    # Extract files from paths:
    i = 0
    for source_path in FILE_PATHS:
        if os.path.isdir(source_path):
            i += 1
            target_path = subsystem_dir + '/content/documents/' + "dir" + str(i) + ".wim"
            if not os.path.isfile(target_path) or OVERWRITE == True:
                capture_files(config_dir, source_path, target_path)
            else:
                print(target_path + ' already exsists. Exiting.')
                sys.exit()
        else:
            print(source_path + ' is not a valid path. Exiting.')
            sys.exit()


    # Connect to java database code:
    if DB_NAME and DB_SCHEMA:
        # Export database schema as xml:
        export_schema(class_path, MAX_JAVA_HEAP, subsystem_dir + '/documentation/', url,  DB_PASSWORD, DB_SCHEMA)

#        header_xml_file = subsystem_dir + '/documentation/metadata.xml'
        # TODO: Skriv row count til header_xml_fil her

        # Copy schema data:
        init_jvm(class_path, MAX_JAVA_HEAP) # Start Java virtual machine if not started already
        WbManager = jp.JPackage('workbench').WbManager
        WbManager.prepareForEmbedded()
        batch = jp.JPackage('workbench.sql').BatchRunner()
        batch.setAbortOnError(True) 
        target_url = 'jdbc:h2:' + subsystem_dir + '/documentation/' + DB_NAME + '_' +  DB_SCHEMA
        target_path = subsystem_dir + '/documentation/' + DB_NAME + '_' +  DB_SCHEMA + '.mv.db'
        
        if os.path.isfile(target_path) and OVERWRITE == False:
            print(target_path + ' already exists. Exiting')
            sys.exit()
        else:
            if os.path.isfile(target_path):
                os.remove(target_path)
            if os.path.isfile(target_url + '.trace.db'):
                os.remove(target_url + '.trace.db')                
        
            # TODO: Detekterer per tabell om finnes blober. Hvis ja sett commit til 500 eller mindre, ca 10000 ellers
            for table, row_count in non_empty_tables.items():
                batch.runScript("WbConnect -url='" + url + "' -password=" + DB_PASSWORD + ";")
                std_params =  '-mode=INSERT -commitEvery=500 -ignoreIdentityColumns=false -removeDefaults=true -showProgress=500 -createTarget=true'
                target_conn = '"username=,password=,url=' + target_url + ';LOG=0;CACHE_SIZE=65536;LOCK_MODE=0;UNDO_LOG=0" ' + std_params 
                copy_data_str = 'WbCopy -targetConnection=' + target_conn + ' -sourceSchema=' + DB_SCHEMA + ' -targetSchema=PUBLIC  -sourceTable=' + table + ' -targetTable=' + table + ';' 
                batch.runScript(copy_data_str) 
                batch.runScript("WbDisconnect;")
                jp.java.lang.System.gc()
        
        
            print('\nDatabase copy finished. Verifying data...')

            # Check if row count matches source database:
            init_jvm(class_path, MAX_JAVA_HEAP) # Start Java virtual machine if not started already
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
                    if table in target_table:
                        if not target_tables[table] == row_count:
                            print("Row count mismatch for table '" + table + "'")
                            row_errors += 1
                    else:
                        print("'" + table + "' missing from database copy.")

                if row_errors == 0:
                    print('\nCopied data rows matches source database. \nCreate system data package now if finished extracting all system data.')




        # Generate db copy code:
        # TODO: Trengs denne?
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









































