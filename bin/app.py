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


import os, model, settings, theme, commands, threading
import tkinter as tk
from commander import Commander
from sidebar import SideBar
from editor import EditorFrame
from statusbar import StatusBar
from xmlrpc.server import SimpleXMLRPCServer
from tkinter import messagebox


class App:    
    """
    Tk Code application : builds the ui and exposes an api for business logic
    like a controller
    """
    
    def __init__(self, tmp_dir, port_file, icon_file):      
        self.model = model.PWCodeModel()  # observable data model
        self.model.add_observer(self)
        self.settings = settings.Settings(self.model)
        self.root = None 

        self.sidebar = None
        self.notebook = None
        self.statusbar = None
        self.commander = None

        self.tmp_dir = tmp_dir
        self.port_file = port_file   
        self.icon_file = icon_file
     

    def build_ui(self):
        """  builds the user interface """
        self.root = root = tk.Tk(className=self.settings.name.lower()) # --> StartupWMClass = pwcode
        root.protocol("WM_DELETE_WINDOW", self.quit_app)

        img = tk.Image('photo', file=self.icon_file)
        root.tk.call('wm','iconphoto',root._w,img)

        w = 1400 # width for the Tk root
        h = 900 # height for the Tk root
        ws = root.winfo_screenwidth() 
        hs = root.winfo_screenheight()

        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)

        root.geometry('%dx%d+%d+%d' % (w, h, x, y))

        style = theme.build_style(self.settings.colors)
        style.theme_use("pwcode")

        self.commander = Commander(self)

        # WAIT: Lag funksjon som leser ut dette auto fra commands.py
        root.bind("<Alt-x>", lambda x: self.run_command('show_commands'))        
        root.bind("<Control-q>", lambda x: self.run_command('quit_app'))       
        root.bind("<Control-o>", lambda x: self.run_command('open_file'))
        root.bind("<Control-O>", lambda x: self.run_command('open_folder'))  
        root.bind("<Control-n>", lambda x: self.run_command('new_file'))       
        root.bind("<Control-w>", lambda x: self.run_command('close_file'))       
        root.bind("<Control-s>", lambda x: self.run_command('save_file'))     
        root.bind("<Control-S>", lambda x: self.run_command('save_file_as')) 

        # TODO: Feil med def next_tab (keybinding virker)
        root.bind("<Control-Right>", lambda x: self.run_command('next_tab'))  
        root.bind("<Control-KP_Right>", lambda x: self.run_command('next_tab')) # on keypad
        root.bind("<Control-KP_6>", lambda x: self.run_command('next_tab'))  # on keypad with num lock     






        # horizontal layout for the sidebar to expand / collapse panels
        self.paned = paned = tk.ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=1)

        self.sidebar = SideBar(paned, self)
        paned.add(self.sidebar)

        self.editor_frame = EditorFrame(paned, self)
        paned.add(self.editor_frame)

        initial_status = ''
        self.statusbar = StatusBar(root, self, initial_status)
        self.statusbar.pack(fill=tk.X, side=tk.BOTTOM)   


    def quit_app(self):
        """ Exit program """
        unsaved = False
        for tab_name in self.editor_frame.notebook.tabs():
            if '!welcometab' not in str(tab_name): 
                text_editor = self.editor_frame.notebook.nametowidget(tab_name)
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
        if os.path.exists(self.port_file):
            os.remove(self.port_file)
        self.root.destroy() 


    def run(self, port):
        """ launch application and server """
        threading.Thread(target=self.start_rcp_server, args=(port,),daemon = True).start()

        if not self.root:
            self.build_ui()
        self.root.mainloop() 


    def focus(self):
        """ Focus existing frame """
        self.root.wm_state('iconic')        
        self.root.wm_state('normal')


    def start_rcp_server(self, port):
        server = SimpleXMLRPCServer(('localhost', int(port)),logRequests=False, allow_none=True)
        server.register_instance(self)
        server.serve_forever()


    def after(self, delay, command):
        """ proxy method to Tk.after() """
        self.root.after(delay, command)    


    def on_file_selected(self, file_obj):
        """ callback on file selection : set the window title """
        base_title = ''
        if file_obj:
            if file_obj.path.startswith(self.tmp_dir + '/Untitled-'):
                base_title = file_obj.basename + ' - '
            else:                
                base_title = file_obj.path + ' - '

        self.root.title(base_title + self.settings.name)


    def command_callable(self, name):
        """create a callable of a command """

        def _callback(*args, **kwargs):
            self.commander.run(name, *args, **kwargs)

        return _callback


    def run_command(self, name, *args, **kwargs):
        self.commander.run(name, *args, **kwargs)


    def select_file(self, file_obj, originator):
        """ set a file as selected """
        self.model.set_current_file(file_obj, originator)
  
