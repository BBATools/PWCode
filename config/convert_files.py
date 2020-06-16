import os
import shutil
from common.xml_settings import XMLSettings
import xml.etree.ElementTree as ET
from pathlib import Path
import glob
import json
import subprocess
import csv
import petl as etl
from convert_files_defs import file_convert

# mime_type: (keep_original, temp_ext, norm_ext)
# 'pdf', 'pdf' --> convert to pdf and then to pdf/a
mime_to_norm = {
    'application/pdf': (False, None, 'pdf'),  # WAIT: Sjekke først om allerede er pdf/a? Sjekke i funksjon?
    'image/tiff': (False, 'pdf', 'pdf'),
    'image/jpeg': (False, 'pdf', 'pdf'),
    'image/png': (False, None, 'pdf'),
    'text/plain; charset=ISO-8859-1': (False, None, 'txt'),
    'text/plain; charset=UTF-8': (False, None, 'txt'),
    'text/plain; charset=windows-1252': (False, None, 'txt'),
    'application/xml': (False, None, 'txt'),  # TODO: Endre denne?
    'image/gif': (False, 'png', 'pdf'),  # WAIT: Sjekk om direkte til pdf/a mulig
    'application/vnd.ms-excel': (True, 'pdf', 'pdf'),
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': (True, 'pdf', 'pdf'),
    'text/html': (False, 'pdf', 'pdf'),  # TODO: Legg til undervarianter her (var opprinnelig 'startswith)
    'application/xhtml+xml; charset=UTF-8': (False, 'pdf', 'pdf'),
    'application/msword': (False, 'pdf', 'pdf'),
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': (False, 'pdf', 'pdf'),
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': (False, 'pdf', 'pdf'),
    'application/vnd.wordperfect': (False, None, 'pdf'),
    # WAIT: Abiword best å bruke først på rtf. Docbuilder klarer bare noen få ekstra som ikke abiword klarer (og sikkert en del motsatt)
    'application/rtf': (False, 'pdf', 'pdf'),
    'application/x-tika-msoffice': (False, None, None),  # Fjern garbage fil når norm_ext == None
    # 'application/vnd.ms-project': ('pdf'), # TODO: Har ikke ferdig kode for denne ennå
    'application/x-msdownload': (False, None, 'pdf')
}


def convert_folder(project_dir, folder, ext_option, tmp_dir, tika=False):
    source_dir = folder.text
    target_dir = project_dir + '/' + folder.tag
    tsv_path = target_dir + '.tsv'
    json_tmp_dir = target_dir + '_tmp'

    Path(target_dir).mkdir(parents=True, exist_ok=True)

    print('Identifying file types...')
    if tika:
        run_tika(tsv_path, source_dir, json_tmp_dir)
    else:
        run_siegfried(source_dir, project_dir, tsv_path)

    print('Converting files..')

    table = etl.fromcsv(
        tsv_path,
        delimiter='\t',
        skipinitialspace=True,
        quoting=csv.QUOTE_NONE,
        quotechar='',
        escapechar=''
    )

    row_count = etl.nrows(table)
    file_count = sum([len(files) for r, d, files in os.walk(source_dir)])

    # WAIT: Sjekk iforkant om garbage files som skal slettes?
    if file_count != row_count:
        print("Files listed in '" + tsv_path + "' doesn't match files on disk. Exiting.")
        return 'error'

    conversion_failed = []
    conversion_not_supported = []

    # WAIT: Legg inn sjekk på filstørrelse før og etter konvertering
    table = etl.values(table, 'filename', 'filesize', 'mime')
    for row in list(table):
        file_path = row[0]
        mime_type = row[2]
        supported = True

        if mime_type not in mime_to_norm.keys():
            supported = False
            conversion_not_supported.append(file_path + ' (' + mime_type + ')')
            print('Mime type not supported: ' + mime_type)
            # TODO: Legg til i conversion not supported
            continue

        keep_original = mime_to_norm[mime_type][0]  # TODO: Ha som arg til file_convert?
        tmp_ext = mime_to_norm[mime_type][1]
        norm_ext = mime_to_norm[mime_type][2]

        new_path = file_path.replace(source_dir, target_dir)
        # new_path = os.path.relpath(file_path, target_dir)
        # print(file_path)

        # print(new_path)

        # TODO: Hvorfor er det bare to av filene som printes her?

        # TODO: Generer file_rel_path først og bruk som arg i linje under
        # status, norm_file_path = file_convert(file_path, mime_type, tmp_ext, norm_ext, target_dir, file_rel_path)
        # status, norm_file_path = file_convert(file_path, mime_type, None, norm_ext)

        # normalized = (0, '')
        # def file_convert(file_full_path, file_type, tmp_ext, norm_ext, folder, file_rel_path, keep_original):
        normalized = file_convert(file_path, mime_type, tmp_ext, norm_ext, target_dir, new_path, keep_original, tmp_dir)

        # if mime_type == 'application/pdf':
        #     # normalized = file_convert(file_path, mime_type, None, norm_ext)
        # elif mime_type in ('image/tiff', 'image/jpeg'):
        #     normalized = file_convert(file_path, mime_type, 'pdf', norm_ext)
        #     # TODO: Oppdatere tsv her eller i funksjon?
        # elif mime_type == 'image/png':
        #     normalized = file_convert(file_path, mime_type, None, norm_ext)
        # elif mime_type in ('text/plain; charset=ISO-8859-1',
        #                    'text/plain; charset=UTF-8',
        #                    'text/plain; charset=windows-1252',
        #                    'application/xml'):
        #     normalized = file_convert(file_path, mime_type, None, norm_ext)
        # elif mime_type == 'image/gif':
        #     normalized = file_convert(file_path, mime_type, None, norm_ext)
        # elif mime_type in (
        #         'application/vnd.ms-excel',
        #         'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        # ):
        #     norm_ext = 'pdf'
        #     keep_original = True
        #     next_file_rel_path = str(row['next_file_rel_path'])
        #     if (next_file_rel_path == 'embedded file'):
        #         normalized = file_convert(file_path, mime_type, None, norm_ext)
        #     else:
        #         normalized = file_convert(file_path, mime_type, 'pdf', norm_ext)
        # elif mime_type.startswith('text/html'):
        #     normalized = file_convert(file_path, mime_type, 'pdf', norm_ext)
        # elif mime_type == 'application/xhtml+xml; charset=UTF-8':  # TODO: Slå sammen med den over?
        #     normalized = file_convert(file_path, mime_type, 'pdf', norm_ext)
        # elif mime_type in (
        #         'application/msword',
        #         'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        #         'application/vnd.wordperfect'):
        #     normalized = file_convert(file_path, mime_type, None, norm_ext)
        # elif mime_type == 'application/rtf':
        #     # WAIT: Abiword best å bruke først. Docbuilder klarer bare noen få ekstra som ikke abiword klarer (og sikkert en del motsatt)
        #     normalized = file_convert(file_path, mime_type, 'pdf', norm_ext)
        # elif (
        #         mime_type == 'application/x-tika-msoffice'
        #         and os.path.basename(file_path) == 'Thumbs.db'
        # ):  # TODO: Gjør på bedre måte så unngår problem hvis krasj før tsv skrives
        #     normalized = file_convert(file_path, mime_type, None, norm_ext)
        # # TODO: Hvis zip, bare sjekk at pakket ut riktig og angi så som ok (husk distinksjon med zip i zip)
        # # elif mime_type== 'application/zip':
        # #     normalized = file_convert(file_path, mime_type,
        # #                               'pdf', 'pdf')

        # elif mime_type == 'application/x-msdownload':
        #     normalized = file_convert(file_path, mime_type, None, norm_ext)
        # # elif mime_type== 'application/vnd.ms-project':
        # #     norm_ext = 'pdf'
        # #     normalized = file_convert(file_path, mime_type,
        # #                               None, norm_ext, in_zip)
        # else:
        #     normalized = file_convert(file_path, mime_type, None, 'pwb')


def flatten_dir(destination, tsv_log=None):
    all_files = []
    first_loop_pass = True

    for root, _dirs, files in os.walk(destination):
        if first_loop_pass:
            first_loop_pass = False
            continue
        for filepath in files:
            all_files.append(os.path.join(root, filepath))

    for filepath in all_files:
        filename = os.path.basename(filepath)
        file_ext = Path(filename).suffix
        file_base = os.path.splitext(filename)[0]
        uniq = 1
        new_path = destination + "/%s%d%s" % (file_base, uniq, file_ext)

        while os.path.exists(new_path):
            new_path = destination + "/%s%d%s" % (file_base, uniq, file_ext)
            uniq += 1
        shutil.move(filepath, new_path)


def reduce_item(key, value):
    # Reduction Condition 1
    if type(value) is list:
        i = 0
        for sub_item in value:
            reduce_item(str(i), sub_item)
            i = i + 1
    # Reduction Condition 2
    elif type(value) is dict:
        sub_keys = value.keys()
        for sub_key in sub_keys:
            reduce_item(str(sub_key).replace(":", "_").replace("-", "_"), value[sub_key])
    # Base Condition
    else:
        reduced_item[str(key)] = str(value)


def json_to_tsv(json_path, tsv_path):
    node = ''
    fp = open(json_path, 'r')
    json_value = fp.read()
    raw_data = json.loads(json_value)
    fp.close()

    try:
        data_to_be_processed = raw_data[node]
    except Exception:
        data_to_be_processed = raw_data

    processed_data = []
    header = []
    for item in data_to_be_processed:
        global reduced_item
        reduced_item = {}
        reduce_item(node, item)
        header += reduced_item.keys()
        processed_data.append(reduced_item)

    header = list(set(header))
    header.sort()

    with open(tsv_path, 'w+') as f:
        writer = csv.DictWriter(f, header, delimiter='\t')
        writer.writeheader()
        for row in processed_data:
            writer.writerow(row)


def flattenjson(b, prefix='', delim='/', val=None):
    if val is None:
        val = {}

    if isinstance(b, dict):
        for j in b.keys():
            flattenjson(b[j], prefix + delim + j, delim, val)
    elif isinstance(b, list):
        get = b
        for j in range(len(get)):
            key = str(j)

            # If the nested data contains its own key, use that as the header instead.
            if isinstance(get[j], dict):
                if 'key' in get[j]:
                    key = get[j]['key']

            flattenjson(get[j], prefix + delim + key, delim, val)
    else:
        val[prefix] = b

    return val


def merge_json_files(tmp_dir, json_path):
    glob_data = []
    for file in glob.glob(tmp_dir + '/*.json'):
        with open(file) as json_file:
            data = json.load(json_file)
            i = 0
            while i < len(data):
                glob_data.append(data[i])
                i += 1

    with open(json_path, 'w') as f:
        json.dump(glob_data, f, indent=4)


def run_tika(tsv_path, source_dir, tmp_dir):
    Path(tmp_dir).mkdir(parents=True, exist_ok=True)

    json_path = tmp_dir + '/merged.json'
    tika_path = '~/bin/tika/tika-app.jar'  # WAIT: Som configvalg hvor heller?
    if not os.path.isfile(tsv_path):  # TODO: Endre så bruker bundlet java
        # TODO: Legg inn switch for om hente ut metadata også (bruke tika da). Bruke hva ellers?
        subprocess.run(  # TODO: Denne blir ikke avsluttet ved ctrl-k -> fix (kill prosess gruppe?)
            'java -jar ' + tika_path + ' -J -m -i ' + source_dir + ' -o ' + tmp_dir,
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            shell=True,
        )

    # Flatten dir hierarchy:
    flatten_dir(tmp_dir)

    # Merge Tika-generated files:
    if not os.path.isfile(json_path):
        merge_json_files(tmp_dir, json_path)

    if not os.path.isfile(tsv_path):
        json_to_tsv(json_path, tsv_path)

    if os.path.isfile(tsv_path):
        shutil.rmtree(tmp_dir)


def run_siegfried(source_dir, project_dir, tsv_path):
    if os.path.exists(tsv_path):
        return

    csv_path = project_dir + 'tmp.csv'
    subprocess.run(
        'sf -z -csv ' + source_dir + ' > ' + csv_path,
        stderr=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        shell=True,
    )

    with open(csv_path, 'r') as csvin, open(tsv_path, 'w') as tsvout:
        csvin = csv.reader(csvin)
        tsvout = csv.writer(tsvout, delimiter='\t')
        for row in csvin:
            tsvout.writerow(row)

    if os.path.exists(csv_path):
        os.remove(csv_path)


def main():
    config_dir = os.environ['pwcode_config_dir']
    tmp_dir = config_dir + '/tmp'
    data_dir = os.environ['pwcode_data_dir']
    tmp_config_path = config_dir + '/tmp/convert_files.xml'
    tmp_config = XMLSettings(tmp_config_path)

    if not os.path.isfile(tmp_config_path):
        print('No config file found. Exiting.')
        return

    project_name = tmp_config.get('name')
    project_dir = data_dir + project_name

    if not os.path.isdir(project_dir):
        print('No project folder found. Exiting.')
        return

    config_path = project_dir + '/convert_files.xml'
    if not os.path.isfile(config_path):
        shutil.copyfile(tmp_config_path, config_path)

    config = XMLSettings(config_path)

    ext_option = config.get('options/ext')
    if ext_option == 'none':
        ext_option = ''

    tree = ET.parse(config_path)
    folders = list(tree.find('folders'))

    for folder in folders:
        if not os.path.isdir(folder.text):
            print("'" + folder.text + "' is not a valid path. Exiting.")
            return

    for folder in folders:
        result = convert_folder(project_dir, folder, ext_option, tmp_dir)
        if result == 'error':
            return


if __name__ == '__main__':
    main()
