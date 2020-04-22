############### USER INPUT ###############
### SYSTEM ###
SYSTEM_NAME = 'test2' # Will also be the name of the generated data package
EXPORT_TYPE = 'BOTH' # DATABASE | FILES | BOTH
PACKAGE = False # Set to true when all export runs are done to package as a wim or tar file with checksum
# TODO: Lag kode for package valg

### FILES ###
SUB_NAME = 'dir1' # Name of subsystem. Not needed or used if a combined database/files export
# TODO: Test å bruke denne heller: https://stackoverflow.com/questions/49757063/truncate-path-in-python
# Extract all files from these directories:
DIR_PATHS =         [
#                            "path/to/extract/on/linux", 
                            "/home/bba/Downloads/python/",        
#                            "c:\path\on\windows"
                    ]

### DATABASE ###
DB_NAME = 'DOCULIVEHIST_DBO'
DB_SCHEMA = 'PUBLIC'
JDBC_URL = 'jdbc:h2:/home/bba/Desktop/DOCULIVEHIST_DBO_PUBLIC'
DB_USER = ''
DB_PASSWORD = ''
MAX_JAVA_HEAP = '-Xmx4g' # g=GB. Increase available memory as needed
DDL_GEN = 'PWCode'  # PWCode | SQLWB -> Choose between generators for 'create table'
# Copy all tables in schema except this:
SKIP_TABLES =       [         
#                            'EDOKFILES',
#                            'tabnavn',
                    ]
# Copy only these tables (overrides 'SKIP_TABLES') :
INCL_TABLES =       [
                            'EDOKFILES',
#                            'ALL',
                    ]
# Overwrite table rather than sync if exists in target:
OVERWRITE_TABLES =  [
                            'EDOKFILES',
#                            'OA_SAK',
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
    overwrite_tables = {} # Overwrite these instead of sync (if exists)
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
            capture_dirs(subsystem_dir, config_dir, DIR_PATHS)   

        # Export database schema:
        if DB_NAME and DB_SCHEMA and JDBC_URL and EXPORT_TYPE != 'FILES':
            export_db_schema(
                JDBC_URL, 
                bin_dir, 
                class_path, 
                MAX_JAVA_HEAP, 
                DB_USER, 
                DB_PASSWORD, 
                DB_NAME, 
                DB_SCHEMA, 
                subsystem_dir, 
                INCL_TABLES, 
                SKIP_TABLES, 
                OVERWRITE_TABLES, 
                DDL_GEN)
    else:
        print_and_exit('Missing system name. Exiting.')

    print_and_exit('All data copied. Create system data package now if finished extracting system data.') 






































