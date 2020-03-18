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

import gettext, os
from gettext import gettext as _get
from gui.gtk import pwb_choose_file
from palette import PaletteFrame
from commander import command
import tkinter as tk
from tkinter import messagebox
from common.file import xdg_open_file
from vendor import filetype


def focus_app(app):
    app.editor_frame.focus()


@command(title=_get("Show Welcome"), description=_get("Show welcome screen"))
def show_welcome(app):
    """ show welcome frame """
    app.editor_frame.show_welcome()


@command(
    title=_get("Next Tab"),
    category=_get("APP"),
    description=_get("Next Tab"),
    shortcut=_get("<Control-Right>"),
)
def next_tab(app):
    """ Go to next tab """
    app.editor_frame.next_tab()

    # tab_name = app.editor_frame.notebook.select()
    # app.editor_frame.notebook.id2path[tab_id] = file_obj
    # app.editor_frame.notebook.select(tab_name)

# https://stackoverflow.com/questions/6687108/how-to-set-the-tab-order-in-a-tkinter-application
# TODO: Previous tab gjøres hvordan?        


@command(
    title=_get("Quit App"),
    category=_get("APP"),
    description=_get("Exit program"),
    shortcut=_get("<Control-q>"),
)
def quit_app(app):
    """ Exit program """
    app.quit_app()




@command(
    title=_get("Show Commands"),
    category=_get("APP"),
    description=_get("Show available commands"),
    shortcut=_get("<Alt-x>"),
)
def show_commands(app):
    """ Show available commands """
    palette = PaletteFrame(app.editor_frame, app.commander)
    palette.show()  


@command(
    title=_get("New File"),
    category=_get("FILE"),
    description=_get("Open new empty file"),
    shortcut=_get("<Control-n>"),
)
def new_file(app):
    """ open new empty file """
    app.model.new_file(app.tmp_dir)        
     

@command(
    title=_get("Open File"),
    category=_get("FILE"),
    description=_get("Open file from filesystem"),
    shortcut=_get("<Control-o>"),
)
def open_file(app, path=None):
    """ Open file from filesystem  """
    if not path:
        path = pwb_choose_file()
    if path:  
        kind = filetype.guess(path)
        if kind:
            xdg_open_file(path) # WAIT: Make Windows-version of xdg_open
        else:             
            app.model.open_file(path)        
  

@command(
    title=_get("Open Folder"),
    category=_get("FILE"),
    description=_get("Open folder from filesystem"),
    shortcut=_get("<Control-Shift-o>"),
)
def open_folder(app, path=None):
    """" Open folder from filesystem  """
    if not path:
        path = pwb_choose_file('folder')
    if path:        
        app.model.open_folder(path)


@command(
    title=_get("Close file"),
    category=_get("FILE"),
    description=_get("Close file"),
    shortcut=_get("<Control-W>"),
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
    title=_get("Save file"),
    category=_get("FILE"),
    description=_get("Save file"),
    shortcut=_get("<Control-s>"),
)
def save_file(app, originator=None):
    """ Save file """
    tab_name = app.editor_frame.notebook.select()
    if '!welcometab' not in str(tab_name):     
        file_obj = app.model.current_file
        app.model.save_file(file_obj, None, originator)


@command(
    title=_get("Save As..."),
    category=_get("FILE"),
    description=_get("Save As..."),
    shortcut=_get("<Alt-s>"),
)
def save_file_as(app, originator=None):
    """ Save As... """
    tab_name = app.editor_frame.notebook.select()
    if '!welcometab' not in str(tab_name):      
        file_obj = app.model.current_file
        new_path = pwb_choose_file('save')
        app.model.save_file(file_obj, new_path, originator)  





       
