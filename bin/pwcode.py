#!/usr/bin/python3 
# Don't change shebang

# GPL3 License

# Copyright (C) 2020 Morten Eek

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import os, sys, xmlrpc.client, socket, fileinput 
from pathlib import Path
from app import App

def find_free_port():
    s = socket.socket()
    s.bind(('', 0))  
    return s.getsockname()[1]   


def open_files_from_arg(args, app):
    if len(args) > 1:
        for file in sys.argv[1:]:
            if os.path.isfile(file):
                app.run_command('open_file', file)


def open_files_from_tmp(app):
    for r, d, f in os.walk(app.tmp_dir):
        for file in f:
            if 'Untitled-' in file:
                app.run_command('open_file', app.tmp_dir + '/' + file)    


def start_client(tmp_dir, port_file, icon_file, python_path, data_dir):
    server = True
    if os.path.isfile(port_file):
        port=open(port_file, 'r').read()
        if port:
            try:
                app = xmlrpc.client.ServerProxy('http://localhost:' + port)
                open_files_from_arg(sys.argv, app)
                app.focus()
                server = False
            except ConnectionRefusedError: 
                pass
    
    if server:
        start_server(tmp_dir, port_file, icon_file, python_path, data_dir)            


def start_server(tmp_dir, port_file, icon_file, python_path, data_dir):  
    app = App(tmp_dir, port_file, icon_file, python_path, data_dir)
    app.build_ui()
    open_files_from_tmp(app)
    app.run_command('show_welcome')
    open_files_from_arg(sys.argv, app)                  
    port = find_free_port()
    with open(app.port_file, 'w') as file:
        file.write(str(port))    
    app.run(port)


def fix_desktop_file(bin_dir, icon_file, desktop_file):
    desktop_file_path = os.path.abspath(os.path.join(bin_dir, '..', desktop_file))        
    for line in fileinput.input(desktop_file_path, inplace = 1): 
        if line.startswith('Icon='):
            line = 'Icon=' + icon_file
        print(line.strip())


# WAIT: Kan legge tilbake psutil-kode da den trengs av jdbc
if __name__ == "__main__":
    self_path = Path(__file__).resolve()
    bin_dir = str(self_path.parents[1]) + '/bin'
    data_dir = str(self_path.parents[1]) + '/_DATA/'
    python_path = 'python3'
    pwcode_icon_file = os.path.join(bin_dir, 'img/arkimint_fin_32px.gif')  # WAIT: Replace icon
    # pwcode_icon_file = os.path.join(bin_dir, 'img/Pw.gif')
    sqlwb_icon_file = os.path.join(bin_dir, 'img/sqlwb.png') 
    python_icon_file = os.path.join(bin_dir, 'img/python.png') 
    tmp_dir = os.path.join(bin_dir, 'tmp')
    port_file = tmp_dir + '/port' 

    if os.name == "posix":
        python_path = os.path.join(bin_dir, 'vendor/linux/python/opt/python3.8/bin/python3.8')
        fix_desktop_file(bin_dir, pwcode_icon_file, 'PWCode.desktop')  
        fix_desktop_file(bin_dir, sqlwb_icon_file, 'SQLWB.desktop') 
        fix_desktop_file(bin_dir, python_icon_file, 'Python.desktop')   

    start_client(tmp_dir, port_file, pwcode_icon_file, python_path, data_dir) 

                
 


