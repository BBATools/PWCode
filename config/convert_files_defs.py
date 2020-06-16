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

import subprocess
import os
import shutil
import sys
import signal
import zipfile
import re
import glob
import pathlib
# TODO: Missing deps under ?
# from pgmagick.api import Image
# from pdfy import Pdfy
# from functools import reduce


def x2utf8(file_path, norm_path, tmp_path, file_type):
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
    cmd = [' '.join(command)]
    stdout = []
    stderr = []
    mix = []  # TODO: Fjern denne mm

    print(''.join(cmd))
    sys.stdout.flush()

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


def file_copy(src, dst):
    print('cp ' + src + ' ' + dst)
    sys.stdout.flush()

    ok = False
    try:
        # if os.path.isdir(dst):
        #     dst = os.path.join(dst, os.path.basename(src))
        shutil.copyfile(src, dst)
    except Exception as e:
        print(e)
        ok = False
    return ok


# TODO: Stopper opp med Exit code: 137 noen ganger -> fiks
def image2norm(image_path, norm_path):
    print('image2norm(python) ' + image_path + ' ' + norm_path)
    sys.stdout.flush()

    ok = False
    try:
        img = Image(image_path)
        img.write(norm_path)
        ok = True
    except Exception as e:
        print(e)
        ok = False
    return ok


def docbuilder2x(file_path, tmp_path, format, file_type, tmp_dir):
    ok = False
    docbuilder_file = tmp_dir + "x2x.docbuilder"
    docbuilder = None

    # TODO: Annet for rtf?
    if file_type in (
            'application/msword', 'application/rtf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ):
        docbuilder = [
            'builder.OpenFile("' + file_path + '", "");',
            'builder.SaveFile("' + format + '", "' + tmp_path + '");',
            'builder.CloseFile();',
        ]
    elif file_type in (
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ):
        docbuilder = [
            'builder.OpenFile("' + file_path + '", "");',
            'var ws;',
            'var sheets = Api.GetSheets();',
            'var arrayLength = sheets.length;',
            'for (var i = 0; i < arrayLength; i++) {ws = sheets[i];ws.SetPageOrientation("xlLandscape");}',
            'builder.SaveFile("' + format + '", "' + tmp_path + '");',
            'builder.CloseFile();',
        ]

    with open(docbuilder_file, "w+") as file:
        file.write("\n".join(docbuilder))

    command = ['documentbuilder', docbuilder_file]
    run_shell_command(command)

    if os.path.exists(tmp_path):
        ok = True

    return ok


def wkhtmltopdf(file_path, tmp_path):
    ok = False
    command = ['wkhtmltopdf', '-O', 'Landscape', file_path, tmp_path]
    run_shell_command(command)

    if os.path.exists(tmp_path):
        ok = True

    return ok


def abi2x(file_path, tmp_path, format, file_type):
    ok = False
    command = ['abiword', '--to=' + format]

    if file_type == 'application/rtf':
        command.append('--import-extension=rtf')

    command.extend(['-o', tmp_path, file_path])
    run_shell_command(command)

    if os.path.exists(tmp_path):
        ok = True

    return ok


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


# --> return ok= False bare da
# WAIT: Se for flere gs argumenter: https://superuser.com/questions/360216/use-ghostscript-but-tell-it-to-not-reprocess-images
def pdf2pdfa(pdf_path, pdfa_path):
    # because of a ghostscript bug, which does not allow parameters that are longer than 255 characters
    # we need to perform a directory changes, before we can actually return from the method
    ok = False

    # TODO: Test om det er noen av valgene under som førte til stooore filer (dEncode-valgene)
    if os.path.exists(pdf_path):
        cwd = os.getcwd()
        os.chdir(os.path.dirname(pdfa_path))
        ghostScriptExec = [
            'gs', '-dPDFA', '-dBATCH', '-dNOPAUSE',
            '-sProcessColorModel=DeviceRGB', '-sDEVICE=pdfwrite', '-dSAFER',
            '-sColorConversionStrategy=UseDeviceIndependentColor',
            '-dEmbedAllFonts=true', '-dPrinted=true',
            '-dPDFACompatibilityPolicy=1', '-dDetectDuplicateImages', '-r150',
            '-dFastWebView=true'
            # '-dColorConversionStrategy=/LeaveColorUnchanged',
            # '-dEncodeColorImages=false', '-dEncodeGrayImages=false',
            # '-dEncodeMonoImages=false', '-dPDFACompatibilityPolicy=1'
        ]

        command = ghostScriptExec + [
            '-sOutputFile=' + os.path.basename(pdfa_path), pdf_path
        ]
        run_shell_command(command)
        os.chdir(cwd)

    if os.path.exists(pdfa_path):
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


# file_full_path = folder + '/' + file_rel_path
# TODO: Feil at ikke file_rel_path er arg i def under
def file_convert(file_full_path, file_type, tmp_ext, norm_ext, folder, new_path, keep_original, tmp_dir):
    # TODO: Legg inn kode for keep_original argument
    normalized_file = 0  # Not converted
    file_name = os.path.basename(file_full_path)
    if tmp_ext:
        tmp_file_full_path = new_path + '.tmp.' + tmp_ext
    else:
        tmp_file_full_path = new_path + '.tmp.pwb'
    norm_folder_full_path = os.path.dirname(new_path)
    # norm_folder_full_path = norm_folder_full_path.replace('//', '/')
    norm_file_full_path = norm_folder_full_path + '/' + os.path.splitext(file_name)[0] + '.norm.' + norm_ext

    # TODO: Bør heller sjekke på annet enn at fil finnes slik at evt corrupt-file kan overskrives ved nytt forsøk
    if not os.path.isfile(norm_file_full_path):
        pathlib.Path(norm_folder_full_path).mkdir(parents=True, exist_ok=True)
        # print('Processing ' + norm_file_full_path) #TODO: Vises ikke i wb output
        norm_ok = False
        tmp_ok = False
        if (not os.path.isfile(tmp_file_full_path) or tmp_ext is None):
            if file_type in ('image/tiff', 'image/jpeg'):
                tmp_ok = image2norm(file_full_path, tmp_file_full_path)
            elif file_type == 'image/gif':
                norm_ok = image2norm(file_full_path, norm_file_full_path)
            elif file_type == 'application/pdf':
                norm_ok = pdf2pdfa(file_full_path, norm_file_full_path)
            elif file_type in ('text/plain; charset=windows-1252',
                               'text/plain; charset=ISO-8859-1',
                               'text/plain; charset=UTF-8', 'application/xml'):
                norm_ok = x2utf8(file_full_path, norm_file_full_path,
                                 tmp_file_full_path, file_type)

            elif file_type == 'image/png':
                norm_ok = file_copy(file_full_path, norm_file_full_path)
            elif file_type in (
                    'application/vnd.ms-excel',
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            ):
                if tmp_ext is None:
                    norm_ok = unoconv2x(file_full_path, norm_file_full_path,
                                        'pdf', file_type)
                else:
                    tmp_ok = docbuilder2x(file_full_path, tmp_file_full_path,
                                          'pdf', file_type, tmp_dir)
                # tmp_ok = unoconv2x(file_full_path, tmp_file_full_path,
                #                        'html', file_type)
            elif file_type.startswith('text/html'):
                tmp_ok = html2pdf(file_full_path, tmp_file_full_path)
            elif file_type == 'application/xhtml+xml; charset=UTF-8':
                tmp_ok = wkhtmltopdf(file_full_path, tmp_file_full_path)
            elif file_type in (
                    'application/msword',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                    'application/vnd.wordperfect'):
                # tmp_ok = docbuilder2x(file_full_path, tmp_file_full_path,'pdf', file_type)
                norm_ok = unoconv2x(file_full_path, norm_file_full_path, 'pdf',
                                    file_type)
            elif file_type == 'application/rtf':
                # TODO: Bør først prøve med abiword og så unoconv for de den ikke klarer -> eller omvendt hvis kan forhindre heng av LO
                # tmp_ok = docbuilder2x(file_full_path, tmp_file_full_path,
                #                       'pdf', file_type)
                norm_ok = unoconv2x(file_full_path, norm_file_full_path, 'pdf',
                                    file_type)
                # tmp_ok = abi2x(file_full_path, tmp_file_full_path, 'pdf',
                #                file_type)
            elif file_type == 'application/x-msdownload':  # TODO: Trengs denne?
                norm_ok = False
            elif (file_type == 'application/x-tika-msoffice'
                  and os.path.basename(file_full_path) == 'Thumbs.db'):
                norm_ok = False
            else:
                normalized_file = 3  # Conversion not supported

        if tmp_ok:
            if tmp_ext == 'pdf':
                norm_ok = pdf2pdfa(tmp_file_full_path, norm_file_full_path)
            elif tmp_ext == 'html':
                norm_ok = unoconv2x(tmp_file_full_path, norm_file_full_path,
                                    'pdf', file_type)
        elif os.path.exists(tmp_file_full_path):
            os.remove(tmp_file_full_path)

        if norm_ok and tmp_ok:
            os.remove(tmp_file_full_path)
        # TODO: Legg inn hvilken originalfiler som skal slettes

        # if os.path.isfile(norm_file_full_path):
        if glob.glob(os.path.splitext(norm_file_full_path)[0] + '.*'):
            if norm_ok:
                normalized_file = 1  # Converted now automatically
            else:
                normalized_file = 2  # Converted now manually
    else:
        normalized_file = 4  # Converted earlier

    return normalized_file, norm_file_full_path
