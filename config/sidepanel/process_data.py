# import shutil
import os
from export_data_defs import print_and_exit, md5sum

""" SYSTEM """
ARCHIVE_PATH = '/home/bba/bin/PWCode/projects/test2.wim'
INTEGRITY_CHECK = True

# Start execution:
if __name__ == "__main__":
    bin_dir = os.environ["pwcode_bin_dir"]  # Get PWCode executable path
    class_path = os.environ['CLASSPATH']  # Get Java jar path
    data_dir = os.environ["pwcode_data_dir"]  # Get PWCode data path (projects)
    config_dir = os.environ["pwcode_config_dir"]  # Get PWCode config path
    # subsystem_dir = None
    tmp_dir = config_dir + '/tmp'

    os.chdir(tmp_dir)  # Avoid littering from subprocesses

    if os.path.isfile(ARCHIVE_PATH):
        if INTEGRITY_CHECK:
            md5sum_file = os.path.splitext(ARCHIVE_PATH)[0]+'_md5sum.txt'
            if not os.path.isfile(md5sum_file):
                print_and_exit("'" + os.path.basename(md5sum_file) + "' not in path. Exiting.")
            else:
                file = open(md5sum_file, "r")
                orig = file.read().replace('\n', '')
                check = md5sum(ARCHIVE_PATH)

                if check == orig:
                    message = "'Checksum Matches'"
                else:
                    message = "'Checksum Mismatch'"

                print(message)
    else:
        print_and_exit("'" + ARCHIVE_PATH + "' is not a valid path. Exiting.")
