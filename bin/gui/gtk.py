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


import gi, os
gi.require_version('Gtk', '3.0') 
from gi.repository import Gtk, Gdk, GObject

# TODO: Legg inn mulighet for filter på wim og bytt så til denne i følgende filer:
# verify_make_copies.py
# process_files_pre.py
# verify_md5sum.py
# process_metadata_pre.py
# common/gui.py

def pwb_choose_file(mode = 'file'):
    win = Gtk.Window ()
    result= []
    file_action = Gtk.FileChooserAction.OPEN
    message = 'Open File'
    accept_action = Gtk.STOCK_OPEN

    if mode == 'folder':
        file_action = Gtk.FileChooserAction.SELECT_FOLDER
        message = 'Open Folder'
    elif mode == 'save':        
        file_action = Gtk.FileChooserAction.SAVE
        accept_action = Gtk.STOCK_SAVE
        message = 'Save As'        

    def run_dialog(_None):
        dialog = Gtk.FileChooserDialog(message, win,file_action,(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, accept_action, Gtk.ResponseType.OK)) 
        dialog.set_modal(True)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            if mode in ('folder','save') or os.path.isfile(dialog.get_filename()):  
                result.append(dialog.get_filename())
        else:
            result.append(None)

        dialog.destroy()
        Gtk.main_quit()

    Gdk.threads_add_idle(GObject.PRIORITY_DEFAULT, run_dialog, None)
    Gtk.main()
    return result[0]

    while Gtk.events_pending():
        Gtk.main_iteration()


