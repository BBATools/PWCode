# Copyright(C) 2020 Morten Eek

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# from PIL import Image
import ocrmypdf
import subprocess
import os
import shutil
import sys
import signal
import zipfile
import re
import pathlib
# import img2pdf
# from pdfy import Pdfy
from functools import reduce
# import wand
# from wand.image import Image, Color
# from wand.image import Image
# from wand.exceptions import BlobError

# Dictionary of converter functions
converters = {}


def add_converter():
    # Decorator for adding functions to converter functions
    def _add_converter(func):
        converters[func.__name__] = func
        return func
    return _add_converter


def delete_file():
    # TODO: Fjern garbage files og oppdater i tsv at det er gjort
    return


def x2utf8(file_path, norm_path, tmp_path, file_type):
    # TODO: Sjekk om beholder extension alltid (ikke endre csv, xml mm)
    ok = False

    if file_type in ('text/plain; charset=windows-1252',
                     'text/plain; charset=ISO-8859-1'):
        # WAIT: Juster så mindre repetisjon under
        if file_type == 'text/plain; charset=windows-1252':
            command = ['iconv', '-f', 'windows-1252']
        elif file_type == 'text/plain; charset=ISO-8859-1':
            command = ['iconv', '-f', 'ISO-8859-1']

        command.extend(['-t', 'UTF8', file_path, '-o', tmp_path])
        run_shell_command(command)
    else:
        file_copy(file_path, tmp_path)

    if os.path.exists(tmp_path):
        repls = (
            ('‘', 'æ'),
            ('›', 'ø'),
            ('†', 'å'),
        )

        # WAIT: Legg inn validering av utf8 -> https://pypi.org/project/validate-utf8/
        file = open(norm_path, "w")
        with open(tmp_path, 'r') as file_r:
            for line in file_r:
                file.write(reduce(lambda a, kv: a.replace(*kv), repls, line))

        if os.path.exists(norm_path):
            ok = True

    return ok


def extract_nested_zip(zippedFile, toFolder):
    """ Extract a zip file including any nested zip files
        Delete the zip file(s) after extraction
    """
    # pathlib.Path(toFolder).mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zippedFile, 'r') as zfile:
        zfile.extractall(path=toFolder)
    os.remove(zippedFile)
    for root, dirs, files in os.walk(toFolder):
        for filename in files:
            if re.search(r'\.zip$', filename):
                fileSpec = os.path.join(root, filename)
                extract_nested_zip(fileSpec, root)


def kill(proc_id):
    os.kill(proc_id, signal.SIGINT)


def run_shell_command(command, cwd=None, timeout=30):
    # ok = False
    os.environ['PYTHONUNBUFFERED'] = "1"
    # cmd = [' '.join(command)]
    stdout = []
    stderr = []
    mix = []  # TODO: Fjern denne mm

    # print(''.join(cmd))
    # sys.stdout.flush()

    proc = subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )

    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        kill(proc.pid)

    # while proc.poll() is None:
    #     line = proc.stdout.readline()
    #     if line != "":
    #         stdout.append(line)
    #         mix.append(line)
    #         print(line, end='')

    #     line = proc.stderr.readline()
    #     if line != "":
    #         stderr.append(line)
    #         mix.append(line)
    #         print(line, end='')

    for line in proc.stdout:
        stdout.append(line.rstrip())

    for line in proc.stderr:
        stderr.append(line.rstrip())

    # print(stderr)
    return proc.returncode, stdout, stderr, mix


@add_converter()
def file_copy(source_file_path, tmp_file_path, norm_file_path, keep_original, tmp_dir, mime_type):
    # print('cp ' + src + ' ' + dst)
    # sys.stdout.flush()

    ok = False
    try:
        shutil.copyfile(source_file_path, norm_file_path)
        ok = True
    except Exception as e:
        print(e)
        ok = False
    return ok


# TODO: Hvordan kalle denne med python: tesseract my-image.png nytt filnavn pdf -> må bruke subprocess

@add_converter()
def image2norm(source_file_path, tmp_file_path, norm_file_path, keep_original, tmp_dir, mime_type):
    ok = False
    if mime_type == 'image/tiff':
        command = ['tiff2pdf', source_file_path, '-o', tmp_file_path]
        run_shell_command(command)
    else:
        print("'" + mime_type + "' not supported by 'image2norm'. Exiting.")  # TODO: Hente def navn auto mulig?
        # TODO: Return mer enn ok fra denne og andre slik at melding om hvilken type feil kan gis til brukes

    if os.path.exists(tmp_file_path):
        ok = pdf2pdfa(tmp_file_path, tmp_file_path, norm_file_path, keep_original, tmp_dir, mime_type)

    return ok


@add_converter()
def docbuilder2x(source_file_path, tmp_file_path, norm_file_path, keep_original, tmp_dir, mime_type):
    ok = False
    docbuilder_file = tmp_dir + "/x2x.docbuilder"
    docbuilder = None

    if mime_type in (
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ):
        docbuilder = [
            'builder.OpenFile("' + source_file_path + '", "");',
            'var ws;',
            'var sheets = Api.GetSheets();',
            'var arrayLength = sheets.length;',
            'for (var i = 0; i < arrayLength; i++) {ws = sheets[i];ws.SetPageOrientation("xlLandscape");}',
            'builder.SaveFile("pdf", "' + tmp_file_path + '");',
            'builder.CloseFile();',
        ]
    else:
        docbuilder = [
            'builder.OpenFile("' + source_file_path + '", "");',
            'builder.SaveFile("pdf", "' + tmp_file_path + '");',
            'builder.CloseFile();',
        ]

    with open(docbuilder_file, "w+") as file:
        file.write("\n".join(docbuilder))

    command = ['documentbuilder', docbuilder_file]
    run_shell_command(command)

    if os.path.exists(tmp_file_path):
        ok = pdf2pdfa(tmp_file_path, tmp_file_path, norm_file_path, keep_original, tmp_dir, mime_type)

    return ok


def wkhtmltopdf(file_path, tmp_path):
    ok = False
    command = ['wkhtmltopdf', '-O', 'Landscape', file_path, tmp_path]
    run_shell_command(command)

    if os.path.exists(tmp_path):
        ok = True

    return ok


@add_converter()
def abi2x(source_file_path, tmp_file_path, norm_file_path, keep_original, tmp_dir, mime_type):
    ok = False
    command = ['abiword', '--to=pdf', '--import-extension=rtf']

    command.extend(['-o', tmp_file_path, source_file_path])
    run_shell_command(command)

    if os.path.exists(tmp_file_path):
        ok = pdf2pdfa(tmp_file_path, tmp_file_path, norm_file_path, keep_original, tmp_dir, mime_type)

    return ok


# def libre2x(source_file_path, tmp_file_path, norm_file_path, keep_original, tmp_dir, mime_type):
    # TODO: Endre så bruker collabora online (er installert på laptop). Se notater om curl kommando i joplin
    # command = ["libreoffice", "--convert-to", "pdf", "--outdir", str(filein.parent), str(filein)]
    # run_shell_command(command)


def unoconv2x(file_path, norm_path, format, file_type):
    ok = False
    command = ['unoconv', '-f', format]

    if file_type in (
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ):
        if format == 'pdf':
            command.extend([
                '-d', 'spreadsheet', '-P', 'PaperOrientation=landscape',
                '-eSelectPdfVersion=1'
            ])
        elif format == 'html':
            command.extend(
                ['-d', 'spreadsheet', '-P', 'PaperOrientation=landscape'])
    elif file_type in ('application/msword', 'application/rtf'):
        command.extend(['-d', 'document', '-eSelectPdfVersion=1'])

    command.extend(['-o', '"' + norm_path + '"', '"' + file_path + '"'])
    run_shell_command(command)

    if os.path.exists(norm_path):
        ok = True

    return ok


@add_converter()
def pdf2pdfa(source_file_path, tmp_file_path, norm_file_path, keep_original, tmp_dir, mime_type):
    ok = False
    ocrmypdf.configure_logging(-1)
    result = ocrmypdf.ocr(source_file_path, norm_file_path, tesseract_timeout=0, progress_bar=False, skip_text=True)
    if str(result) == 'ExitCode.ok':
        ok = True

    return ok


def html2pdf(file_path, tmp_path):
    print('html2pdf(python) ' + file_path + ' ' + tmp_path)
    sys.stdout.flush()

    ok = False
    try:
        p = Pdfy()
        p.html_to_pdf(file_path, tmp_path)
        ok = True
    except Exception as e:
        print(e)
        ok = False
    return ok


def file_convert(source_file_path, mime_type, function, target_dir, keep_original, tmp_dir, norm_ext, count_str):
    source_file_name = os.path.basename(source_file_path)
    base_file_name = os.path.splitext(source_file_name)[0] + '.'
    tmp_file_path = tmp_dir + '/' + base_file_name + 'tmp.pwb'
    norm_file_path = target_dir + '/' + base_file_name + norm_ext
    normalized = {'result': None, 'norm_file_path': norm_file_path, 'error': None}

    if not os.path.isfile(norm_file_path):
        if function in converters:
            pathlib.Path(target_dir).mkdir(parents=True, exist_ok=True)

            # TODO: Dict som input til conversion functions? https://stackoverflow.com/questions/1769403/what-is-the-purpose-and-use-of-kwargs
            print(count_str + source_file_path + ' (' + mime_type + ')')
            ok = converters[function](source_file_path, tmp_file_path, norm_file_path, keep_original, tmp_dir, mime_type)

            if not ok:
                original_files = target_dir + '/original_documents/'
                pathlib.Path(original_files).mkdir(parents=True, exist_ok=True)
                file_copy(source_file_path, tmp_file_path, original_files + os.path.basename(source_file_path), keep_original, tmp_dir, mime_type)
                # TODO: Fjern igjen hvis senere konvertering ok?
                normalized['result'] = 0  # Conversion failed
                normalized['norm_file_path'] = None
            elif keep_original:
                corrupted_files = target_dir + '/corrupted_documents/'
                pathlib.Path(corrupted_files).mkdir(parents=True, exist_ok=True)
                file_copy(source_file_path, corrupted_files + os.path.basename(source_file_path))
                normalized['result'] = 1  # Converted successfully
            else:
                normalized['result'] = 1  # Converted successfully
            #     os.remove(source_file_path) # WAIT: Bare når kjørt som generell behandling av arkivpakke
        else:
            if function:
                normalized['result'] = None
                normalized['error'] = "Missing converter function '" + function + "' Exiting."  # TODO: Endre så ikke avluttes men gir FM til bruker til slutt
                normalized['norm_file_path'] = None
            else:
                normalized['result'] = 2  # Conversion not supported
                normalized['norm_file_path'] = None
    else:
        normalized['result'] = 3  # Converted earlier, or manually

    if os.path.isfile(tmp_file_path):
        os.remove(tmp_file_path)

    return normalized
