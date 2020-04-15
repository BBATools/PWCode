############### USER INPUT ###############
### SYSTEM ###
SYSTEM_NAME = 'test2' # Will also be the name of the generated data package
EXPORT_TYPE = 'DATABASE' # DATABASE | FILES | BOTH
OVERWRITE = True # Overwrite extracted data if previous export detected

### DATABASE ###
DB_NAME = 'DOCULIVEHIST_DBO'
DB_SCHEMA = 'PUBLIC'
JDBC_URL = 'jdbc:h2:/home/bba/Desktop/DOCULIVEHIST_DBO_PUBLIC'
DB_USER = ''
DB_PASSWORD = ''
MAX_JAVA_HEAP = '-Xmx4g' # g=GB. Increase available memory as needed
# Copy all tables in schema except this:
SKIP_TABLES =      [         
#                            'EDOKFILES',
#                            'tabnavn',
                            ]
# Copy only these tables (overrides 'SKIP_TABLES') :
INCL_TABLES =      [
#                            'EDOKFILES',
                            'ALL',
                            ]
# Sync these tables rather than drop and insert:
SYNC_TABLES =     [
#                            'EDOKFILES',
                            'ALL',
                            ]

### FILES ###
SUB_NAME = 'dir1' # Name of subsystem. Not needed or used if a combined database/files export
# Extract all files from these directories:
DIR_PATHS =         [
#                            "path/to/extract/on/linux", 
                            "/home/bba/Downloads/python/",        
#                            "c:\path\on\windows"
                            ]


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
    db_tables = {} # All database tables
    export_tables = {} # All tables to be exported
    table_columns = {} # Columns per table
    sync_tables = {} # Sync these instead of drop and insert
    bin_dir = os.environ["pwcode_bin_dir"] # Get PWCode executable path
    class_path = os.environ['CLASSPATH'] # Get Java jar path
    config_dir = os.environ["pwcode_config_dir"] # Get PWCode config path

    if SYSTEM_NAME:
        data_dir = os.environ["pwcode_data_dir"] + SYSTEM_NAME # --> projects/[system]

        if SUB_NAME and EXPORT_TYPE == 'FILES':                
            subsystem_dir = data_dir + '/content/sub_systems/' + SUB_NAME
        elif DB_NAME and DB_SCHEMA:
            subsystem_dir = data_dir + '/content/sub_systems/' + DB_NAME + '_' + DB_SCHEMA
        else:
            if EXPORT_TYPE == 'FILES':
                print_and_exit('Missing subsystem name. Exiting.')  
            else:
                print_and_exit('Missing database- or schema -name. Exiting.')

        # Create data package directories:
        ensure_dirs(data_dir, subsystem_dir) 
    
        if DIR_PATHS and EXPORT_TYPE != 'DATABASE':
            # Extract files from paths:
            capture_dirs(subsystem_dir, config_dir, DIR_PATHS, OVERWRITE)   

        if DB_NAME and DB_SCHEMA and JDBC_URL and EXPORT_TYPE != 'FILES':
            # Get details for database type:
            url, driver_jar, driver_class = get_db_details(JDBC_URL, bin_dir)
            if driver_jar and driver_class:
                # Start Java virtual machine if not started already:
                class_paths = class_path + ':' + driver_jar
                init_jvm(class_paths, MAX_JAVA_HEAP) 

                try:
                    jdbc = Jdbc(url, DB_USER, DB_PASSWORD, DB_NAME, DB_SCHEMA, driver_jar, driver_class, True, True)
                    if jdbc:                
                        # Get database metadata:
                        db_tables, table_columns = get_db_meta(jdbc)   
                        export_schema(class_path, MAX_JAVA_HEAP, subsystem_dir, jdbc)   
                        add_row_count_to_schema_file(subsystem_dir, db_tables)          
                        export_tables, sync_tables = table_check(INCL_TABLES, SKIP_TABLES, SYNC_TABLES, db_tables, subsystem_dir)   

                    if export_tables:
                         # Copy schema data:
                        copy_db_schema(subsystem_dir, jdbc, OVERWRITE, class_path, MAX_JAVA_HEAP, export_tables, bin_dir, table_columns, sync_tables)
                    else:
                        print_and_exit('No table data to export. Exiting.')  
                    
                except Exception as e:
                    print_and_exit(e)

            else:
                print_and_exit('Not a supported jdbc url. Exiting')
    else:
        print_and_exit('Missing system name. Exiting.')


    print_and_exit('Data copied. Create system data package now if finished extracting all system data.') 

















