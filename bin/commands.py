# MIT License

# Original work Copyright (c) 2018 François Girault
# Modified work Copyright 2020 Morten Eek

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import gettext, webbrowser, os
from gettext import gettext as _
from common.gui_gtk import pwb_choose_file
from palette import PaletteFrame
from commander import command
import tkinter as tk
from tkinter import messagebox

# WAIT: Gjør konsekvent med app, self under

@command(title=_("Focus App"), description=_("Focus app"))
def focus_app(self):
    self.editor_frame.focus()


@command(title=_("Show Welcome"), description=_("Show welcome screen"))
def show_welcome(app):
    """ show welcome frame """
    app.editor_frame.show_welcome()


@command(
    title=_("Quit App"),
    category=_("APP"),
    description=_("Exit program"),
    shortcut=_("<Control-q>"),
)
def quit_app(app):
    """ Exit program """
    unsaved = False
    for tab_name in app.editor_frame.notebook.tabs():
        if '!welcometab' not in str(tab_name): 
            text_editor = app.editor_frame.notebook.nametowidget(tab_name)
            if text_editor.modified: 
                unsaved = True
                break

    if unsaved:
        confirm = messagebox.askyesno(
            message = 'You have unsaved changes. Are you sure you want to quit?',
            icon = 'question',
            title = 'Confirm Quit'
        )

        if unsaved and not confirm:
            return

    os.remove(app.port_file)
    app.root.destroy() 


@command(
    title=_("Show Commands"),
    category=_("APP"),
    description=_("Show available commands"),
    shortcut=_("<Alt-x"),
)
def show_commands(self):
    """ Show available commands """
    palette = PaletteFrame(self.editor_frame, self.commander)
    palette.show()  


@command(
    title=_("New File"),
    category=_("FILE"),
    description=_("Open new empty file"),
    shortcut=_("<Control-n>"),
)
def new_file(self):
    """ open new empty file """
    self.model.new_file(self.tmp_dir)        
     

@command(
    title=_("Open File"),
    category=_("FILE"),
    description=_("Open file from filesystem"),
    shortcut=_("<Control-o>"),
)
def open_file(self, path=None):
    """ Open file from filesystem  """
    if not path:
        path = pwb_choose_file()
    if path:       
        self.model.open_file(path)        


@command(
    title=_("Open Folder"),
    category=_("FILE"),
    description=_("Open folder from filesystem"),
    shortcut=_("<Control-Shift-o>"),
)
def open_folder(app, path=None):
    """" Open folder from filesystem  """
    if not path:
        path = pwb_choose_file('folder')
    if path:        
        app.model.open_folder(path)

@command(
    title=_("Open home url"),
    category=_("WEB"),
    description=_("Open home url in default browser"),
)
def open_home_url(self):
    """" Open home url in default browser  """
    # WAIT: Gjør URL til konfigvalg og/eller argument
    webbrowser.open('https://github.com/BBATools/PreservationWorkbench', new=2)


@command(
    title=_("Close file"),
    category=_("FILE"),
    description=_("Close file"),
    shortcut=_("<Control-W>"),
)
def close_file(app, originator=None):
    """ Close file """
    tab_name = app.editor_frame.notebook.select()
    if '!welcometab' not in str(tab_name): 
        cancel = False
        file_obj = app.model.current_file
        text_editor = app.editor_frame.notebook.nametowidget(tab_name)

        if text_editor.modified:  
            answer = tk.messagebox.askyesnocancel(
                title="Unsaved changes",
                message="Do you want to save changes you made to " + file_obj.basename + "?",
                default=messagebox.YES,
                parent=app.editor_frame)  

            if str(answer) == 'True':
                app.model.save_file(file_obj, None, originator)                  
            elif str(answer) == 'None':
                cancel = True    

        if not cancel:                                                 
            app.model.close_file(file_obj, originator)   


@command(   
    title=_("Save file"),
    category=_("FILE"),
    description=_("Save file"),
    shortcut=_("<Control-s>"),
)
def save_file(app, originator=None):
    """ Save file """
    tab_name = app.editor_frame.notebook.select()
    if '!welcometab' not in str(tab_name):     
        file_obj = app.model.current_file
        app.model.save_file(file_obj, None, originator)


@command(
    title=_("Save As..."),
    category=_("FILE"),
    description=_("Save As..."),
    shortcut=_("<Alt-s>"),
)
def save_file_as(app, originator=None):
    """ Save As... """
    tab_name = app.editor_frame.notebook.select()
    if '!welcometab' not in str(tab_name):      
        file_obj = app.model.current_file
        new_path = pwb_choose_file('save')
        app.model.save_file(file_obj, new_path, originator)  





       
