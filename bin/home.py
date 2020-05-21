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

from console import ConsoleUi, Processing
from common.xml_settings import XMLSettings
import os
import webbrowser
import pickle
import shutil
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from settings import COLORS
from gui.dialog import multi_open


class HomeTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, style="Home.TFrame", padding=[56, 12, 8, 8])
        self.heading = ttk.Label(self, text=app.settings.name, style="Heading.TLabel")
        self.heading.pack(side=tk.TOP, anchor=tk.W)

        global subsystem_frames
        subsystem_frames = []
        self.system_dir = None
        self.system_dir_created = False

        frame = ttk.Frame(self, style="Home.TFrame")
        frame.pack(fill=tk.BOTH, expand=1, pady=12)
        frame.pack_propagate(False)

        self.left_frame = ttk.Frame(frame, style="Home.TFrame")
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        self.right_frame = ttk.Frame(frame, style="Home.TFrame")
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=1, padx=(0, 56))

        self.show_start(app)
        self.show_help(app)

    def open_home_url(self):
        webbrowser.open('https://github.com/BBATools/PWCode', new=2)

    def show_console(self, app):  # TODO: For test. Remove if send to new tab works better
        path = '/home/bba/bin/PWCode/config/sidepanel/export_data.py'
        app.model.open_file(path)

        tab_id = app.editor_frame.path2id[path]
        file_obj = app.editor_frame.id2path[tab_id]

        # file_obj = app.model.current_file
        # print(file_obj)
        if file_obj:
            self.console = ConsoleUi(self.right_frame, file_obj)
            self.processing = Processing(file_obj, app)
            # self.processing.show_message('run_file [Ctrl+Enter]\nkill_process [Ctrl+k]\n')
            # self.console.pack(side=tk.RIGHT, fill=tk.BOTH, expand=1)

    def show_help(self, app):
        self.subheading = ttk.Label(self, text=app.settings.desc, style="SubHeading.TLabel")
        self.subheading.pack(side=tk.TOP, anchor=tk.W, after=self.heading)
        self.description = ttk.Label(self, text=app.settings.long_desc, style="Text.TLabel")
        self.description.pack(side=tk.TOP, anchor=tk.W, after=self.subheading)

        for widget in self.right_frame.winfo_children():
            widget.destroy()

        subsystem_frames.clear()
        self.system_dir_created = False

        LinksFrame(
            self.right_frame,
            "Help",
            (
                ("GitHub repository", self.open_home_url),
            ),
        ).pack(side=tk.TOP, anchor=tk.W, pady=12)

    def show_start(self, app):
        LinksFrame(
            self.left_frame,
            "Start",
            (
                ("New Data Project", lambda: self.system_entry(app)),
                ("New File", app.command_callable("new_file")),
                ("Open File ...", app.command_callable("open_file")),
                ("Open Folder ...", app.command_callable("open_folder")),
            ),
        ).pack(side=tk.TOP, anchor=tk.W, pady=12)

        self.recent_links_frame = RecentLinksFrame(self.left_frame, app).pack(side=tk.TOP, anchor=tk.W, pady=12)
        # self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

    def system_entry_check(self, app):
        system_name = system_name_entry.get()
        if not system_name:
            msg = 'Missing system name'
            msg_label.config(text=msg)
            return
        else:
            msg_label.config(text='')

        self.system_dir = app.data_dir + system_name + '_'  # --> projects/[system_]
        system_dir = self.system_dir

        archive_format = 'tar'  # WAIT: Sjekk om posix også her?
        if shutil.which('wimcapture') is not None:
            archive_format = 'wim'

        archive = system_dir[:-1] + '/' + system_name + '.' + archive_format
        # TODO: Flere sjekker? Sjekke mot config xml fil og, eller bare?
        # TODO: Gjenbruke mappe hvis finnes og tom eller bare visse typer innhold?

        if os.path.isfile(archive):
            msg = "'" + archive + "' already exists"
            msg_label.config(text=msg)
            return

        if not self.system_dir_created:
            try:
                os.mkdir(system_dir)
                self.system_dir_created = True
            except OSError:
                msg = "Can't create destination directory '%s'" % (system_dir)
                msg_label.config(text=msg)
                return

        system_frame.configure(text=' ' + system_name + ' ')
        system_name_entry.configure(state=tk.DISABLED)

        # TODO: Lås tittel felt for redigering

        return 'ok'

    def system_entry(self, app):
        global system_frame
        global system_name_entry
        global msg_label

        self.subheading.pack_forget()
        self.description.pack_forget()

        for widget in self.right_frame.winfo_children():
            widget.destroy()

        export_frame = ttk.Frame(self.right_frame, style="SubHeading.TLabel")
        export_frame.pack(side=tk.TOP, anchor=tk.W, pady=12, fill=tk.X)
        export_label = ttk.Label(export_frame, text="Export data", style="SubHeading.TLabel")
        export_label.pack(side=tk.LEFT, anchor=tk.N, pady=4, padx=1, fill="both", expand="yes")
        msg_label = ttk.Label(export_frame, text="", style="Links.TButton")
        msg_label.pack(side=tk.LEFT, anchor=tk.E, pady=4, padx=(0, 12))

        system_frame = ttk.LabelFrame(self.right_frame, style="Links.TFrame", text=" New Data Project ", relief=tk.GROOVE)
        system_frame.pack(side=tk.TOP, anchor=tk.W, fill="both", expand=1)

        system_name_label = ttk.Label(system_frame, text="System Name:")
        system_name_label.pack(side=tk.LEFT, anchor=tk.N, padx=(8, 0), pady=(4, 24))

        system_name_entry = make_entry(system_frame, app, 59)
        system_name_entry.pack(side=tk.LEFT, anchor=tk.N, pady=(4, 24), padx=(4, 0))
        system_name_entry.focus()

        cancel_button = ttk.Button(system_frame, text='Discard', style="Links.TButton", command=lambda: self.show_help(app))
        cancel_button.pack(side=tk.RIGHT, anchor=tk.N, pady=4, padx=(0, 12))

        subsystem_button = ttk.Button(system_frame, text='Add Subsystem', style="Entry.TButton", command=lambda: self.subsystem_entry(app))
        subsystem_button.pack(side=tk.RIGHT, anchor=tk.N, pady=4, padx=(0, 12))

        # TODO: Lag def export_system(self, app):
        run_button = ttk.Button(system_frame, text='Run', style="Run.TButton", command=lambda: self.export_system(app))
        run_button.pack(side=tk.RIGHT, anchor=tk.N, pady=4, padx=(0, 12))

    def subsystem_entry(self, app):
        ok = None
        if len(subsystem_frames) == 0:
            ok = self.system_entry_check(app)
        else:
            ok = self.subsystem_entry_check(app)

        if ok:
            if len(subsystem_frames) == 0:
                system_frame.pack_forget()
                system_frame.pack(side=tk.TOP, anchor=tk.W, fill="both", expand=0, pady=(0, 12))

            subsystem_frame = SubSystem(self.right_frame, app, text=" New Subsystem ", relief=tk.GROOVE)
            subsystem_frame.pack(side=tk.TOP, anchor=tk.W, fill="both", expand=1, pady=12)
            subsystem_frames.append(subsystem_frame)

    def subsystem_entry_check(self, app):
        # TODO: # skriv path for config til environment variable -> gjøre før kjøring av selve eksport bare heller?
        config_path = self.system_dir + "/pwcode.xml"
        if os.path.isfile(config_path):
            os.remove(config_path)

        config = XMLSettings(config_path)
        config.put('name', system_name_entry.get())

        subsystem_names = []
        for subsystem in subsystem_frames:
            # subsystem_name = subsystem.db_name_entry.get().lower()
            subsystem_name = subsystem.db_name_entry.get().lower() + '_' + subsystem.db_schema_entry.get().lower()
            # TODO: Sjekk kobling eller at kan brukes som mappenavn her

            msg = None
            if len(subsystem_name) < 2:
                msg = 'Missing subsystem name'
            elif subsystem_name in subsystem_names:
                msg = 'Duplicate subsystem name'

            if msg:
                msg_label.config(text=msg)
                # WAIT: Slette system mappe hvis tom her? Også når cancel?
                return

            if not msg:
                msg_label.config(text='')

            subsystem_names.append(subsystem_name)
            subsystem.configure(text=' ' + subsystem_name + ' ')

            config.put('subsystems/' + subsystem_name + '/db_name', subsystem.db_name_entry.get().lower())
            config.put('subsystems/' + subsystem_name + '/schema_name', subsystem.db_schema_entry.get().lower())

            # TODO: Gjøre auto sjekker av jdbc-kobling her ?

        config.save()

        return 'ok'


class SubSystem(ttk.LabelFrame):
    def __init__(self, parent, app, *args, **kwargs):
        super().__init__(parent, *args, **kwargs, style="Links.TFrame")

        self.frame1 = ttk.Frame(self, style="SubHeading.TLabel")
        self.frame1.pack(side=tk.TOP, anchor=tk.W, fill=tk.X)

        self.db_name_label = ttk.Label(self.frame1, text="DB Name:", width=8)
        self.db_name_label.pack(side=tk.LEFT, anchor=tk.N, padx=(8, 0), pady=(4, 3))
        self.db_name_entry = make_entry(self.frame1, app, 25)
        self.db_name_entry.pack(side=tk.LEFT, anchor=tk.N, pady=(4, 3))
        self.db_name_entry.focus()
        self.db_schema_label = ttk.Label(self.frame1, text="Schema Name:", width=8)
        self.db_schema_label.pack(side=tk.LEFT, anchor=tk.N, padx=(9, 0), pady=3)
        self.db_schema_entry = make_entry(self.frame1, app, 25)
        self.db_schema_entry.pack(side=tk.LEFT, anchor=tk.N, pady=3)
        self.cancel_button = ttk.Button(self.frame1, text='Discard', style="Links.TButton", command=lambda: self.subsystem_remove(parent))
        self.cancel_button.pack(side=tk.RIGHT, anchor=tk.N, pady=(3, 2), padx=(0, 12))
        self.folder_button = ttk.Button(self.frame1, text='Add Folder', style="Entry.TButton", command=lambda: self.choose_folder(app))
        self.folder_button.pack(side=tk.RIGHT, anchor=tk.N, pady=(3, 2), padx=(0, 12))

        self.frame2 = ttk.Frame(self, style="SubHeading.TLabel")
        self.frame2.pack(side=tk.TOP, anchor=tk.W, fill=tk.X)
        self.jdbc_url_label = ttk.Label(self.frame2, text="JDBC Url: ")
        self.jdbc_url_label.pack(side=tk.LEFT, anchor=tk.N, padx=(9, 0), pady=3)
        self.jdbc_url_entry = make_entry(self.frame2, app, 63)
        self.jdbc_url_entry.pack(side=tk.LEFT, anchor=tk.N, pady=3)

        self.frame3 = ttk.Frame(self, style="SubHeading.TLabel")
        self.frame3.pack(side=tk.TOP, anchor=tk.W, fill=tk.X)
        self.db_user_label = ttk.Label(self.frame3, text="DB User: ")
        self.db_user_label.pack(side=tk.LEFT, anchor=tk.N, padx=(8, 1), pady=3)
        self.db_user_entry = make_entry(self.frame3, app, 25)
        self.db_user_entry.pack(side=tk.LEFT, anchor=tk.N, pady=3)
        self.db_pwd_label = ttk.Label(self.frame3, text="DB Password:   ")
        self.db_pwd_label.pack(side=tk.LEFT, anchor=tk.N, padx=(10, 0), pady=3)
        self.db_pwd_entry = make_entry(self.frame3, app, 25)
        self.db_pwd_entry.pack(side=tk.LEFT, anchor=tk.N, pady=3)

        # self.frame4 = ttk.Frame(self, style="SubHeading.TLabel")
        # self.frame4.pack(side=tk.TOP, anchor=tk.W, fill=tk.X)
        # # TODO: Flytt denne linjen opp på system nivå
        # # TODO: Legg inn sjekk på at ikke duplikat folder --> i choose_folder kode?

        # self.memory_label = ttk.Label(self.frame4, text="Allocated memory:     ")
        # self.memory_label.pack(side=tk.LEFT, anchor=tk.N, padx=(8, 0), pady=3)
        # options = ['', '3 Gb', '4 Gb', '5 Gb', '6 Gb', '7 Gb', '8 Gb']
        # var = tk.StringVar()
        # var.set(options[1])
        # self.memory_option = ttk.OptionMenu(self.frame4, var, *options)
        # self.memory_option.pack(side=tk.LEFT, anchor=tk.N, pady=3, padx=(0, 84))

        # self.ddl_label = ttk.Label(self.frame4, text="DDL Generation:       ")
        # self.ddl_label.pack(side=tk.LEFT, anchor=tk.N, padx=(8, 0), pady=3)
        # options = ['', 'Native', 'SQL Workbench/J']
        # var = tk.StringVar()
        # var.set(options[1])
        # self.ddl_option = ttk.OptionMenu(self.frame4, var, *options)
        # self.ddl_option.pack(side=tk.LEFT, anchor=tk.N, pady=3)

        self.frame5 = ttk.Frame(self, style="SubHeading.TLabel")
        self.frame5.pack(side=tk.TOP, anchor=tk.W, fill=tk.X)

        options = ['', 'Exclude Tables (comma separated)', 'Include Tables (comma separated)']
        self.var = tk.StringVar()
        self.var.set(' '.join(options[1].split(' ')[:2]) + ':')
        self.var.trace("w", self.get_option)
        self.tables_option = ttk.OptionMenu(self.frame5, self.var, *options)
        self.tables_option.pack(side=tk.LEFT, anchor=tk.N, pady=3, padx=(8, 0))
        self.tables_entry = make_entry(self.frame5, app, 56)
        self.tables_entry.pack(side=tk.LEFT, anchor=tk.N, pady=3)

        self.frame6 = ttk.Frame(self, style="SubHeading.TLabel")
        self.frame6.pack(side=tk.TOP, anchor=tk.W, fill=tk.X)

        self.overwrite_label = ttk.Label(self.frame6, text="Overwrite Tables:")
        self.overwrite_label.pack(side=tk.LEFT, anchor=tk.N, padx=(8, 11), pady=(3, 4))
        self.overwrite_entry = make_entry(self.frame6, app, 56)
        self.overwrite_entry.pack(side=tk.LEFT, anchor=tk.N, pady=(3, 6))

        # self.folder_frame = ttk.Frame(self, style="SubHeading.TLabel")
        # self.folder_frame.pack(side=tk.TOP, anchor=tk.N, fill=tk.BOTH, expand=1)
        self.folder_list = LinksFrame(self)
        self.folder_list.pack(side=tk.TOP, anchor=tk.N, padx=(8, 0), pady=3, fill=tk.X)

    def choose_folder(self, app):
        path = multi_open(app.data_dir, mode='dir')
        self.folder_list.add_folder('Folder: ' + path, lambda p=path: app.command_callable("open_folder")(p), 68)

    def get_option(self, *args):
        value = ' '.join(self.var.get().split(' ')[:2]) + ':'
        if value.startswith('In'):
            value = value + ' '
        self.var.set(value)
        self.tables_option.configure(state=tk.NORMAL)  # Just for refreshing widget

    def subsystem_remove(self, parent):
        subsystem_frames.remove(self)
        self.destroy()

        if len(subsystem_frames) == 0:
            system_frame.pack_forget()
            system_frame.pack(side=tk.TOP, anchor=tk.W, fill="both", expand=1)


class LinksFrame(ttk.Frame):
    """ A container of links and label that packs vertically"""

    def __init__(self, parent, title=None, links=None):
        super().__init__(parent, style="Links.TFrame")
        if title:
            self.title = ttk.Label(self, text=title, style="SubHeading.TLabel")
            self.title.pack(side=tk.TOP, anchor=tk.W, pady=4, padx=1)

        if links:
            for label, action in links:
                if action:
                    self.add_link(label, action)
                else:
                    self.add_label(label)

    def add_link(self, label, action):
        ttk.Button(self, text=label, style="Links.TButton", command=action).pack(side=tk.TOP, anchor=tk.W)

    def add_folder(self, label, action, width):
        folder_frame = ttk.Frame(self, style="SubHeading.TLabel")
        folder_frame.pack(side=tk.TOP, anchor=tk.W, fill=tk.X)

        folder = ttk.Button(folder_frame, text=label, style="SideBar.TButton", command=action, width=width)
        folder.pack(side=tk.LEFT, anchor=tk.N, pady=(1, 0))
        remove_button = ttk.Button(folder_frame, text='  x', style="SideBar.TButton", command=lambda: folder_frame.pack_forget())
        remove_button.pack(side=tk.LEFT, anchor=tk.N, pady=(1, 0))
        # ttk.Button(self, text=label, style="Entry.TButton", command=action).pack(side=tk.TOP, anchor=tk.W)

    def add_label(self, text):
        ttk.Label(self, text=text, style="Links.TLabel").pack(side=tk.TOP, anchor=tk.W)


class RecentLinksFrame(LinksFrame):
    """A frame display a list of last opened  in the model"""

    def __init__(self, parent, app):
        super().__init__(parent, "Open Recent")
        self.app = app

        app.model.add_observer(self)

        if os.path.exists(self.app.tmp_dir + "/recent_files.p"):
            self.app.recent_links = pickle.load(open(self.app.tmp_dir + "/recent_files.p", "rb"))
            self.update_recent_links(None)

    def update_recent_links(self, new_file_obj):
        if new_file_obj:
            if new_file_obj.path in self.app.recent_links.keys():
                del self.app.recent_links[new_file_obj.path]
            self.app.recent_links.update({new_file_obj.path: new_file_obj})

        for widget in self.winfo_children():
            if isinstance(widget, ttk.Button):
                widget.destroy()

        for path, file_obj in reversed(self.app.recent_links.items()):
            if os.path.isfile(file_obj.path):
                if 'PWCode/bin/tmp/Untitled-' in file_obj.path:
                    if os.path.getsize(file_obj.path) == 0:
                        os.remove(file_obj.path)
                    continue

                if file_obj in self.app.model.openfiles:
                    continue

                self.add_link(file_obj.basename, lambda p=path: self.app.command_callable("open_file")(p))

    def on_file_closed(self, file_obj):
        """model callback"""
        self.update_recent_links(file_obj)

    def on_file_open(self, file_obj):
        """model callback"""
        self.update_recent_links(None)


def make_entry(parent, app, width):
    entry = tk.Entry(parent,
                     font=app.font,
                     bg=COLORS.sidebar_bg,
                     disabledbackground=COLORS.sidebar_bg,
                     fg=COLORS.fg,
                     disabledforeground=COLORS.sidebar_fg,
                     bd=0,
                     insertbackground=COLORS.link,
                     insertofftime=0,
                     width=width,
                     highlightthickness=0,
                     )

    return entry
