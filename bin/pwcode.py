#!/usr/bin/python3

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


import os, sys, psutil, xmlrpc.client, socket, fileinput
# sys.path.insert(0, '.') # Look for modules here fist
from app import App


def is_running(script): # WAIT: Bare sjekke om får kontakt med serverproxy heller?
    for p in psutil.process_iter():
        if p.name() == script: 
            if len(p.cmdline())>1 and script in p.cmdline()[1] and p.pid !=os.getpid():
                return str(p.pid)


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


def start_client(port_file):
    port=open(port_file, 'r').read()
    app = xmlrpc.client.ServerProxy('http://localhost:' + port)
    open_files_from_arg(sys.argv, app)
    app.focus()


def start_server(tmp_dir, port_file):  
    app = App(tmp_dir, port_file)
    app.build_ui()
    open_files_from_tmp(app)
    app.run_command('show_welcome')
    open_files_from_arg(sys.argv, app)                  
    port = find_free_port()
    with open(app.port_file, 'w') as file:
        file.write(str(port))    
    app.run(port)


def fix_desktop_file(bin_dir):
    desktop_file = os.path.abspath(os.path.join(bin_dir, '..', 'PWCode.desktop')) 
    icon_file = os.path.join(bin_dir, 'img/arkimint_fin_32px.png')       
    for line in fileinput.input(desktop_file, inplace = 1): 
        if line.startswith('Icon='):
            line = 'Icon=' + icon_file
        print(line.strip())


# TODO: Se for hvordan endre prosessnavn fra python i windows (ie rename bundlet python.exe til pwcode.exe)
# https://superuser.com/questions/427642/is-it-possible-to-set-the-process-name-with-pythonw
if __name__ == "__main__":
    bin_dir = os.path.abspath(os.path.dirname(__file__))
    tmp_dir = os.path.join(bin_dir, 'tmp')
    port_file = tmp_dir + '/port' 

    server = is_running(os.path.basename(__file__))
    if server:
        start_client(port_file)
    else:
        start_server(tmp_dir, port_file)  

    fix_desktop_file(bin_dir)                  
 


