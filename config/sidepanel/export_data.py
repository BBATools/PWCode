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
MAX_JAVA_HEAP = '-Xmx3g' # g=GB

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
                # Start Java virtual machine if not started already:
                class_paths = class_path + ':' + driver_jar
                init_jvm(class_paths, MAX_JAVA_HEAP) 

                try:
                    jdbc = Jdbc(url, DB_USER, DB_PASSWORD, driver_jar, driver_class, True, True)
                    if jdbc:
                        db_tables, table_columns = get_db_meta(jdbc, DB_SCHEMA)                
                        non_empty_tables = {k:v for (k,v) in db_tables.items() if v > 0}

                    if non_empty_tables:
                        subsystem_dir = data_dir + '/content/sub_systems/' + DB_NAME + '_' + DB_SCHEMA
                    else:
                        print_and_exit('Database is empty. Exiting.')
                except Exception as e:
                    print_and_exit(e)

            else:
                print_and_exit('Not a supported jdbc url. Exiting')
        elif FILE_PATHS:
            subsystem_dir = str(unique_dir(data_dir + '/content/sub_systems/' + SYSTEM_NAME))
        else:
            print_and_exit('Missing db or file paths. Exiting.')
    else:
        print_and_exit('Missing system name. Exiting.')

    # Create data package directories:
    ensure_dirs(data_dir, subsystem_dir) 

    # Extract files from paths:
    capture_dirs(subsystem_dir, config_dir, FILE_PATHS, OVERWRITE)

    # Export database:
    if DB_NAME and DB_SCHEMA:
        # Export database schema as xml:
        export_schema(class_path, MAX_JAVA_HEAP, subsystem_dir + '/documentation/', url,  DB_PASSWORD, DB_SCHEMA)
        add_row_count_to_schema_file(subsystem_dir, db_tables)

        # Copy schema data:
        # TODO: Ha jdbc object som argument heller?
        copy_db_schema(subsystem_dir, DB_NAME, DB_SCHEMA, OVERWRITE, class_path, MAX_JAVA_HEAP, non_empty_tables, url, DB_PASSWORD, bin_dir)
    else:
        print('\nData copied. Create system data package now if finished extracting all system data.') 


#Generate db copy code:
#TODO: Trengs denne?'

















