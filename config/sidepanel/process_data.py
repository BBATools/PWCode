import time
import os
import sys
import shutil
from pathlib import Path
from export_data_defs import print_and_exit, md5sum

""" SYSTEM """
ARCHIVE_PATH = '/home/bba/bin/PWCode/projects/test2.wim'
INTEGRITY_CHECK = True


def pretty_size(nbytes):
    suffixes = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB']
    i = 0
    while nbytes >= 1024 and i < len(suffixes)-1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[i])


def copy_file_progress(source, destination, prefix='Copy', suffix='done', decimals=1, length=50):
    with open(source, 'rb') as src, open(destination, 'wb') as dest:
        full_size = os.stat(source).st_size
        full = 0
        increment = 10485760
        tot_count = int(full_size/increment) + 1
        count = 0
        while full < full_size:
            count += 1
            chunk = src.read(increment)
            full += increment
            calc = full
            if calc + increment > full_size:
                calc += full_size - full
            dest.write(chunk)
            str_full = pretty_size(full)
            if count == tot_count:
                str_full = pretty_size(full_size)
            cust_bar = str_full + ' of ' + pretty_size(full_size)
#            cust_bar = None
            printProgressBar(count, tot_count, cust_bar, prefix=prefix, suffix=suffix, decimals=decimals, length=length)
            # progress.update(task_id, advance=len(chunk))
#            print(round(calc / full_size * 100, 1), '%\r')


# def copy_url(task_id: TaskID, url: str, path: str) -> None:
#     """Copy data from a url to a local file."""
#     response = urlopen(url)
#     # This will break if the response doesn't contain content length
#     progress.update(task_id, total=int(response.info()["Content-length"]))
#     with open('397.64-desktop.exe', 'rb') as f:
#         with open(path, "wb") as dest_file:
#             for data in iter(partial(response.read, 32768), b""):
#                 dest_file.write(data)
#                 progress.update(task_id, advance=len(data))

# Print iterations progress
def printProgressBar(iteration, total, cust_bar, prefix='', suffix='', decimals=1, length=100, fill='█', printEnd=""):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    if cust_bar:
        bar = cust_bar
    else:
        bar = fill * filledLength + '-' * (length - filledLength)

    # print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end=printEnd)
    print('\r%s %s %s%s%%%s %s' % (prefix, bar, '(', percent, ')', suffix), end=printEnd)


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


