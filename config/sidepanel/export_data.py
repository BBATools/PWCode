############### USER INPUT ###############
### SYSTEM ###
SYSTEM_NAME = 'test' # Will also be the name of the generated data package
OVERWRITE = True # Overwrite extracted data if previous export detected
EXPORT_TYPE = 'BOTH' # DATABASE | FILES | BOTH

### DATABASE ###
DB_NAME = 'DOCULIVEHIST_DBO'
DB_SCHEMA = 'PUBLIC'
JDBC_URL = 'jdbc:h2:/home/bba/Desktop/DOCULIVEHIST_DBO_PUBLIC'
DB_USER = ''
DB_PASSWORD = ''
MAX_JAVA_HEAP = '-Xmx3g' # g=GB. Increase available memory as needed
# Copy all tables in schema except this:
SKIP_TABLES =      [         
#                            'EDOKFILES',
#                            'tabnavn',
                            ]
# Copy only these tables (overrides 'SKIP_TABLES') :
INCL_TABLES =      [
#                            'EDOKFILES',
#                            'tabnavn',
                            ]
# Sync these tables rather than drop and insert:
SYNC_TABLES =     [
#                            'EDOKFILES',
#                            'tabnavn',
                            ]

### FILES ###
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
    non_empty_tables = {} # All tables with content
    table_columns = {} # Columns per table
    bin_dir = os.environ["pwcode_bin_dir"] # Get PWCode executable path
    class_path = os.environ['CLASSPATH'] # Get Java jar path
    config_dir = os.environ["pwcode_config_dir"] # Get PWCode config path

    if SYSTEM_NAME:
        data_dir = os.environ["pwcode_data_dir"] + SYSTEM_NAME # --> projects/[system]

        if DB_NAME and DB_SCHEMA and JDBC_URL and EXPORT_TYPE != 'FILES':
            # Get details for database type:
            url, driver_jar, driver_class = get_db_details(JDBC_URL, bin_dir)
            if driver_jar and driver_class:
                # Start Java virtual machine if not started already:
                class_paths = class_path + ':' + driver_jar
                init_jvm(class_paths, MAX_JAVA_HEAP) 

                try:
                    # Test connection:
                    jdbc = Jdbc(url, DB_USER, DB_PASSWORD, driver_jar, driver_class, True, True)
                    if jdbc:
                        # Get table data:
                        db_tables, table_columns = get_db_meta(jdbc, DB_SCHEMA)                
                        non_empty_tables = {k:v for (k,v) in db_tables.items() if v > 0}

                        if INCL_TABLES:
                            for tbl in INCL_TABLES:
                                if tbl not in non_empty_tables:
                                    print_and_exit("'" + tbl + "' is empty or not in schema. Exiting.")
                            for tbl in list(non_empty_tables):
                                if tbl not in INCL_TABLES:
                                    del non_empty_tables[tbl]
                        elif SKIP_TABLES:
                            for tbl in SKIP_TABLES:
                                if tbl in non_empty_tables:
                                    del non_empty_tables[tbl]
                                else:
                                    print_and_exit("'" + tbl + "' is empty or not in schema. Exiting.") 
                        
                        if SYNC_TABLES: # TODO: Bruk denne for tabeller i listen samt tabeller som inneholder blober
                            # TODO: SJekk først om har primary key. Kan ikke synces ellers           

                    if non_empty_tables:
                        subsystem_dir = data_dir + '/content/sub_systems/' + DB_NAME + '_' + DB_SCHEMA
                    else:
                        print_and_exit('Database is empty. Exiting.')
                except Exception as e:
                    print_and_exit(e)

            else:
                print_and_exit('Not a supported jdbc url. Exiting')
        elif DIR_PATHS and EXPORT_TYPE != 'DATABASE':
            subsystem_dir = str(unique_dir(data_dir + '/content/sub_systems/' + SYSTEM_NAME))
        else:
            print_and_exit('Missing database connection details and directory paths. Exiting.')
    else:
        print_and_exit('Missing system name. Exiting.')

    # Create data package directories:
    ensure_dirs(data_dir, subsystem_dir) 

    # Extract files from paths:
    if EXPORT_TYPE != 'DATABASE':
        capture_dirs(subsystem_dir, config_dir, DIR_PATHS, OVERWRITE)

    # Export database:
    if DB_NAME and DB_SCHEMA and JDBC_URL and EXPORT_TYPE != 'FILES':
        # Export database schema as xml:
        export_schema(class_path, MAX_JAVA_HEAP, subsystem_dir + '/documentation/', url,  DB_PASSWORD, DB_SCHEMA)
        add_row_count_to_schema_file(subsystem_dir, db_tables)

        # Copy schema data:
        copy_db_schema(subsystem_dir, DB_NAME, DB_SCHEMA, OVERWRITE, class_path, MAX_JAVA_HEAP, non_empty_tables, url, DB_PASSWORD, bin_dir, table_columns)
    else:
        print_and_exit('Data copied. Create system data package now if finished extracting all system data.') 







