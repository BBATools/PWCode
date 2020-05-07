import os
import shutil
from pathlib import Path
from configparser import SafeConfigParser
from common.file import md5sum, copy_file_progress
from common.print import print_and_exit
from common.config import add_config_section


""" SYSTEM """
ARCHIVE_PATH = '/home/bba/bin/PWCode/projects/test2.wim'
INTEGRITY_CHECK = True


# Start execution:
if __name__ == "__main__":
    bin_dir = os.environ["pwcode_bin_dir"]  # Get PWCode executable path
    class_path = os.environ['CLASSPATH']  # Get Java jar path
    data_dir = os.environ["pwcode_data_dir"]  # Get PWCode data path (projects)
    config_dir = os.environ["pwcode_config_dir"]  # Get PWCode config path

    tmp_dir = config_dir + '/tmp'
    os.chdir(tmp_dir)  # Avoid littering from subprocesses

    system_dir = os.path.splitext(ARCHIVE_PATH)[0]
    Path(system_dir + '/mount').mkdir(parents=True, exist_ok=True)
    Path(system_dir + '/bak').mkdir(parents=True, exist_ok=True)

    system_name = os.path.basename(system_dir)
    md5sum_path = os.path.splitext(ARCHIVE_PATH)[0]+'_md5sum.txt'
    archive_bak_path = system_dir + '/bak/' + os.path.basename(ARCHIVE_PATH)
    md5sum_bak_path = system_dir + '/bak/' + os.path.basename(md5sum_path)

    if os.path.isfile(ARCHIVE_PATH):
        if INTEGRITY_CHECK:
            if not os.path.isfile(md5sum_path):
                print_and_exit("'" + os.path.basename(md5sum_path) + "' not in path. Exiting.")
            else:
                file = open(md5sum_path, "r")
                orig = file.read().replace('\n', '')
                check = md5sum(ARCHIVE_PATH)

                if check == orig:
                    print("Data verified by checksum.")  # TODO: Skriv til config_fil i system_mappe så ikke gjøres på nytt neste gang. Fjern sjekk på true/false da
                else:
                    print_and_exit("Checksum Mismatch. Check data integrity. Exiting.")

        if not os.path.isfile(md5sum_bak_path):
            shutil.copyfile(md5sum_path, md5sum_bak_path)

        if not os.path.isfile(archive_bak_path):
            print("\nBackup archive before processing...")
            copy_file_progress(ARCHIVE_PATH, archive_bak_path, prefix='Backup archive:', suffix='done', decimals=0, length=50)
            print("\nBackup complete.")

    else:
        print_and_exit("'" + ARCHIVE_PATH + "' is not a valid path. Exiting.")
