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

import os, pathlib
import tkinter as tk
from settings import COLORS
from welcome import WelcomeTab
from vendor.tktextext import EnhancedText
from gui.scrollbar import PWScrollbar 
from gui.scrollbar_autohide import AutoHideScrollbar

# pylint: disable=too-many-ancestors


# class EditorFrame(ScrollableNotebook):
class EditorFrame(tk.ttk.Frame):
    """ A container for the notebook, including bottom console """

    def __init__(
        self, 
        parent, 
        app,
        ):
        super().__init__(parent)
        
        self.app = app
        app.model.add_observer(self)
        self.notebook = tk.ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=tk.YES)
        self.path2id = {}
        self.id2path = {}
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        self.welcome_id = None


    def focus(self):
        self.lift() 


    def show_welcome(self):
        """ show a welcome tab at the first notebook position """
        if not self.welcome_id:
            if self.notebook.index("end"):
                self.notebook.insert(0, WelcomeTab(self, self.app), text="Welcome")
            else:
                self.notebook.add(WelcomeTab(self, self.app), text="Welcome")
            self.welcome_id = self.notebook.tabs()[0]

        self.notebook.select(self.welcome_id)


    def on_file_open(self, file_obj):
        """open the file object in a tab """
        # check if not already opened
        if file_obj in self.id2path.values():
            self.on_file_selected(file_obj)
            return

        editor = TextEditorFrame(self.notebook, file_obj)
        tab_id = self.notebook.select()

        if tab_id:
            pos = self.notebook.index(tab_id)

            pos = pos + 1
            if not pos < self.notebook.index("end"):
                pos = "end"
            self.notebook.insert(pos, editor, text=file_obj.basename)

            if pos == "end":
                pos = -1
            tab_id = self.notebook.tabs()[pos]
        else:
            self.notebook.add(editor, text=file_obj.basename)
            tab_id = self.notebook.tabs()[-1]

        # fill cache and indices
        self.path2id[file_obj.path] = tab_id
        self.id2path[tab_id] = file_obj

        self.notebook.select(tab_id)


    def on_file_selected(self, file_obj):
        """select an opened file"""
        if file_obj:
            tab_id = self.notebook.select()
            if tab_id not in self.id2path or self.id2path[tab_id] is not file_obj:
                self.notebook.select(self.path2id[file_obj.path])


    def on_file_closed(self, file_obj):
        """remove the tab associated with the file object"""
        tab_id = self.path2id[file_obj.path]
        self.notebook.forget(tab_id)
        del self.path2id[file_obj.path]
        del self.id2path[tab_id]      


    def on_file_save(self, file_obj, new_path = None):
        """ save editor content to file """
        # WAIT: Print any errors to status line?
        pathlib.Path(self.app.tmp_dir).mkdir(parents=True, exist_ok=True) # TODO: Flytte til commands?        
        original_path = file_obj.path
        path = original_path
        if new_path:
            path = new_path

        tab_name = self.notebook.select()
        if tab_name:
            text_editor = self.notebook.nametowidget(tab_name)
            content = text_editor.get_content()

            try:               
                with open(path, 'w') as file:
                    file.write(content)   
            except:
                pass   
            finally:
                text_editor.modified = False

                if new_path:
                    self.app.model.close_file(file_obj)
                    self.app.model.open_file(new_path)

                    if original_path.startswith(self.app.tmp_dir + '/Untitled-'):
                        if os.path.isfile(original_path):
                            os.remove(original_path)
     

    def on_tab_changed(self, event):
        """tell the model the current file has changed"""
        tab_id = self.notebook.select()
        if tab_id in self.id2path:
            self.app.select_file(self.id2path[tab_id], self)


class TextEditorFrame(tk.ttk.Frame):
    """ A frame that contains a text editor """

    def __init__(
        self, 
        parent, 
        file_obj=None,
        vertical_scrollbar=True,
        ):
        super().__init__(parent)

        self.text = EnhancedText(
            self,
            background=COLORS.text_bg,
            foreground="#eeeeee",
            insertbackground=COLORS.status_bg,
            # insertbackground="#eeeeee",
            borderwidth=0,
            highlightthickness=0,
            relief=tk.FLAT,
            takefocus=1,
            insertofftime =0, #Disable blinking cursor
            insertwidth = 2,
            spacing1 = 0,
            spacing3 = 0,
            inactiveselectbackground = COLORS.status_bg,
            padx = 5,
            pady = 5,
        )

        if vertical_scrollbar:
            self.text.v_scrollbar = AutoHideScrollbar(
                self.text, 
                command = self.v_scrollbar_scroll,
                width = 10, 
                troughcolor = COLORS.sidebar_bg, 
                troughoutline = COLORS.sidebar_bg,
                buttoncolor = COLORS.sidebar_bg,
                thumbcolor = COLORS.status_bg, 
                )
            self.text["yscrollcommand"] = self.text.v_scrollbar.set 
            self.text.v_scrollbar.pack(side="right", fill="y")

        self.text.pack(expand=tk.YES, fill=tk.BOTH)
        self.set_file_obj(file_obj) 
        self.modified = False    

        self.text.bind("<<TextChange>>", self.unsaved_text, True) 


    def unsaved_text(self, event):
        self.modified = True


    def get_content(self):
        return self.text.get(0.0, tk.END)  


    def set_file_obj(self, file_obj):
        self.file_obj = file_obj
        if file_obj:
            self.text.delete("0.0", tk.END)
            if file_obj.content != 'empty_buffer':
                self.text.insert(tk.END, file_obj.content)  
            self.text.focus_set()                              

    def v_scrollbar_scroll(self, *args):
        self.text.yview(*args)
        self.text.event_generate("<<VerticalScroll>>")   

      
