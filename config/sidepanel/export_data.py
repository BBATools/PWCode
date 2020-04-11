############### USER INPUT ###############

SYSTEM_NAME = 'test'
DB_NAME = 'db1'
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
MAX_JAVA_HEAP = 1024

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
    bin_dir = os.environ["pwcode_bin_dir"] # Get PWCode executable path
    class_path = os.environ['CLASSPATH'] # Get Java jar path
    config_dir = os.environ["pwcode_config_dir"] # Get PWCode config path

    if SYSTEM_NAME:
        data_dir = os.environ["pwcode_data_dir"] + '/' + SYSTEM_NAME # --> projects/[system]

        if DB_NAME and DB_SCHEMA:
            url, driver_jar, driver_class = get_db_details(JDBC_URL, bin_dir)
            if driver_jar and driver_class:
                try:
                    jdbc = Jdbc(url, DB_USER, DB_PASSWORD, driver_jar, driver_class, True, True)
                    if jdbc:
                        conn= jdbc.connection
                        cursor = conn.cursor()
                        tables = get_tables(conn, DB_SCHEMA)

                        # TODO: Hent ut linjer pr tabell her
                        for table in tables:
                            print(table)

            
                        conn.close()
                    subsystem_dir = data_dir + '/content/sub_systems/' + DB_NAME + '_' + DB_SCHEMA
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
        init_jvm(class_path, MAX_JAVA_HEAP) # Start Java virtual machine
        import java.lang
        WbManager = jp.JPackage('workbench').WbManager
        WbManager.prepareForEmbedded()
        batch = jp.JPackage('workbench.sql').BatchRunner()
        batch.setAbortOnError(True) 

        # Export database schema as xml:
        batch.setBaseDir(subsystem_dir + '/documentation/')    
        batch.runScript("WbConnect -url='" + url + "' -password=" + DB_PASSWORD + ";")
        gen_report_str = "WbSchemaReport -file=metadata.xml -schemas=" + DB_SCHEMA + " -types=SYNONYM,TABLE,VIEW -includeProcedures=true \
                                -includeTriggers=true -writeFullSource=true;"
        batch.runScript(gen_report_str) 

        # Generate db copy code:
        header_xml_file = subsystem_dir + '/documentation/metadata.xml'
#        stylesheet = 

#        WbXslt
#        -inputfile= header_xml_file
#        -stylesheet=$[pwb_path]/xslt/metadata2wbcopy.xslt
#        -xsltOutput=$[wb_dir]/bin/tmp/wbcopy.sql;

        # Copy schema data:

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

































