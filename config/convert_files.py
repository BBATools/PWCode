import shutil
import os
import xml.etree.ElementTree as ET
from pathlib import Path
import glob
import json
import subprocess
import csv
import petl as etl
from common.xml_settings import XMLSettings
from petl import extendheader, rename, appendtsv
from convert_files_defs import file_convert

# mime_type: (keep_original, function name, new file extension)
mime_to_norm = {
    'application/zip': (False, 'extract_nested_zip', None),  # TODO: Legg inn for denne
    'application/pdf': (False, 'pdf2pdfa', 'pdf'),
    'image/tiff': (False, 'image2norm', 'pdf'),
    'image/jpeg': (False, 'image2norm', 'pdf'),
    'image/png': (False, 'file_copy', 'png'),
    'text/plain; charset=ISO-8859-1': (False, 'x2utf8', 'txt'),
    'text/plain; charset=UTF-8': (False, 'x2utf8', 'txt'),
    'text/plain; charset=windows-1252': (False, 'x2utf8', 'txt'),
    'application/xml': (False, 'x2utf8', 'xml'),
    'image/gif': (False, 'image2norm', 'pdf'),
    'application/vnd.ms-excel': (True, 'docbuilder2x', 'pdf'),
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': (True, 'docbuilder2x', 'pdf'),
    'text/html': (False, 'html2pdf'),  # TODO: Legg til undervarianter her (var opprinnelig 'startswith)
    'application/xhtml+xml; charset=UTF-8': (False, 'wkhtmltopdf', 'pdf'),
    'application/msword': (False, 'docbuilder2x', 'pdf'),
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': (False, 'docbuilder2x', 'pdf'),
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': (False, 'docbuilder2x', 'pdf'),
    'application/vnd.wordperfect': (False, 'docbuilder2x', 'pdf'),  # TODO: Mulig denne må endres til libreoffice
    'application/rtf': (False, 'abi2x', 'pdf'),
    'application/x-tika-msoffice': (False, 'delete_file', None),  # TODO: Skriv funksjon ferdig
    # 'application/vnd.ms-project': ('pdf'), # TODO: Har ikke ferdig kode for denne ennå
    # WAIT: Gjøre hva med executables i linjene under? delete_file?
    'application/x-msdownload': (False, 'what?', None),  # executable on win
    'application/x-ms-installer': (False, 'what?', None),  # Installer on win
    'application/x-elf': (False, 'what?', None)  # executable on lin
}


def append_tsv_row(file_path, row):
    with open(file_path, 'a') as tsv_file:
        writer = csv.writer(
            tsv_file,
            delimiter='\t',
            quoting=csv.QUOTE_NONE,
            quotechar='',
            lineterminator='\n',
            escapechar='')
        writer.writerow(row)


def append_txt_file(file_path, msg):
    with open(file_path, 'a') as txt_file:
        txt_file.write(msg + '\n')


def convert_folder(project_dir, folder, ext_option, tmp_dir, tika=False):
    # TODO: Bør den være convert folders heller? Hvordan best når flere ift brukervennlighet, messages
    base_source_dir = folder.text
    base_target_dir = project_dir + '/' + folder.tag
    tsv_source_path = base_target_dir + '.tsv'
    txt_target_path = base_target_dir + '_result.txt'
    tsv_target_path = base_target_dir + '_processed.tsv'
    json_tmp_dir = base_target_dir + '_tmp'
    first_run = True
    converted_now = False
    errors = False

    Path(base_target_dir).mkdir(parents=True, exist_ok=True)

    # TODO: Viser mime direkte om er pdf/a eller må en sjekke mot ekstra felt i de to under?

    if not os.path.isfile(tsv_source_path):
        if tika:
            # TODO: Må tilpasse tsv under for tilfelle tika. Bare testet med siegried så langt
            run_tika(tsv_source_path, base_source_dir, json_tmp_dir)
        else:
            run_siegfried(base_source_dir, project_dir, tsv_source_path)
    else:
        first_run = False

    table = etl.fromtsv(tsv_source_path)
    row_count = etl.nrows(table)
    file_count = sum([len(files) for r, d, files in os.walk(base_source_dir)])

    # WAIT: Sjekk i forkant om garbage files som skal slettes?
    if row_count == 0:
        print('No files to convert. Exiting.')
        return 'error'
    elif file_count != row_count:
        print("Files listed in '" + tsv_source_path + "' doesn't match files on disk. Exiting.")
        return 'error'
    else:
        print('Converting files..')

    # WAIT: Legg inn sjekk på filstørrelse før og etter konvertering

    if first_run:
        table = etl.rename(table, {'filename': 'source_file_path', 'filesize': 'file_size', 'mime': 'mime_type'}, strict=False)
        table = etl.addfield(table, 'norm_file_path', None)
        table = etl.addfield(table, 'result', None)

    header = etl.header(table)
    append_tsv_row(tsv_target_path, header)

    if os.path.isfile(txt_target_path):
        os.remove(txt_target_path)

    data = etl.dicts(table)
    for row in data:
        source_file_path = row['source_file_path']
        mime_type = row['mime_type']
        result = None
        if not first_run:
            result = row['result']

        if mime_type not in mime_to_norm.keys():
            result = 'Conversion not supported'
            append_txt_file(txt_target_path, result + ': ' + source_file_path + ' (' + mime_type + ')')
        else:
            keep_original = mime_to_norm[mime_type][0]
            function = mime_to_norm[mime_type][1]

            norm_ext = mime_to_norm[mime_type][2]
            if ext_option:
                norm_ext = '.norm.' + norm_ext

            target_dir = os.path.dirname(source_file_path.replace(base_source_dir, base_target_dir))
            normalized = file_convert(source_file_path, mime_type, function, target_dir, keep_original, tmp_dir, norm_ext)

            if normalized['error'] is not None:
                print(normalized['error'])
                return 'error'

            if normalized['result'] == 0:
                errors = True
                result = 'Conversion failed'
                append_txt_file(txt_target_path, result + ': ' + source_file_path + ' (' + mime_type + ')')
            elif normalized['result'] == 1:
                result = 'Converted successfully'
                converted_now = True
            elif normalized['result'] == 2:
                errors = True
                result = 'Conversion not supported'
                append_txt_file(txt_target_path, result + ': ' + source_file_path + ' (' + mime_type + ')')
            elif normalized['result'] == 3:
                if result != 'Converted successfully':
                    result = 'Manually converted'
                    converted_now = True

        row['norm_file_path'] = normalized['norm_file_path']
        row['result'] = result
        append_tsv_row(tsv_target_path, list(row.values()))

    shutil.move(tsv_target_path, tsv_source_path)

    if converted_now:
        if errors:
            print("\nNot all files were converted. See '" + txt_target_path + "' for details.")
        else:
            print('\nAll files converted succcessfully.')
    else:
        print('No new files converted')


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


def run_tika(tsv_path, base_source_dir, tmp_dir):
    Path(tmp_dir).mkdir(parents=True, exist_ok=True)

    json_path = tmp_dir + '/merged.json'
    tika_path = '~/bin/tika/tika-app.jar'  # WAIT: Som configvalg hvor heller?
    # if not os.path.isfile(tsv_path):
    # TODO: Endre så bruker bundlet java
    # TODO: Legg inn switch for om hente ut metadata også (bruke tika da). Bruke hva ellers?
    print('Identifying file types and extracting metadata...')
    subprocess.run(  # TODO: Denne blir ikke avsluttet ved ctrl-k -> fix (kill prosess gruppe?)
        'java -jar ' + tika_path + ' -J -m -i ' + base_source_dir + ' -o ' + tmp_dir,
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


def run_siegfried(base_source_dir, project_dir, tsv_path):
    if os.path.exists(tsv_path):
        return

    print('Identifying file types...')

    csv_path = project_dir + 'tmp.csv'
    subprocess.run(
        'sf -z -csv ' + base_source_dir + ' > ' + csv_path,
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
    tmp_dir = config_dir + 'tmp'
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
