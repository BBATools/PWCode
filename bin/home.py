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
import os
import webbrowser
import pickle
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from settings import COLORS


class HomeTab(ttk.Frame):
    """ A start-up screen with recent folder and useful links """

    def __init__(self, parent, app):
        super().__init__(parent, style="Home.TFrame", padding=[56, 12, 8, 8])
        ttk.Label(self, text=app.settings.name, style="Heading.TLabel").pack(
            side=tk.TOP, anchor=tk.W
        )
        ttk.Label(self, text=app.settings.desc, style="SubHeading.TLabel").pack(
            side=tk.TOP, anchor=tk.W
        )
        ttk.Label(self, text=app.settings.long_desc, style="Text.TLabel").pack(
            side=tk.TOP, anchor=tk.W
        )

        frame = ttk.Frame(self, style="Home.TFrame")
        frame.pack(fill=tk.BOTH, expand=1, pady=12)

        self.left_frame = ttk.Frame(frame, style="Home.TFrame")
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        self.right_frame = ttk.Frame(frame, style="Home.TFrame")
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=1, padx=(0, 56))

        self.show_start(app)
        self.show_help()

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

    def show_help(self):
        for widget in self.right_frame.winfo_children():
            widget.destroy()

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

    def make_entry(self, parent, app):
        entry = tk.Entry(parent,
                         font=app.font,
                         bg=COLORS.sidebar_bg,
                         fg=COLORS.fg,
                         bd=0,
                         insertbackground=COLORS.link,
                         insertofftime=0,
                         width=50,
                         highlightthickness=0
                         )

        return entry

    def subsystem_entry(self, app):
        system_frame.configure(text=' ' + system_title_entry.get() + ' ')

        # TODO: Lag sjekk på at tittel som kan bruks som navn på mappe på win og lin
        # TODO: Lag mappe hvis ikke finnes
        # Skriv til xml config fil i mappe
        # skriv path for config til environment variable -> gjøre før kjøring av selve eksport bare heller?

        subsystem_frame = ttk.LabelFrame(self.right_frame, style="Links.TFrame", text=" Subsystem ", relief=tk.GROOVE)
        subsystem_frame.pack(side=tk.TOP, anchor=tk.W, fill="both", expand="yes", pady=12)

        label = ttk.Label(subsystem_frame, text="Database Name:")
        label.pack(side=tk.LEFT, anchor=tk.N, padx=(12, 0), pady=6)

    def system_entry(self, app):
        global system_frame
        global system_title_entry

        for widget in self.right_frame.winfo_children():
            widget.destroy()

        LinksFrame(self.right_frame, "Export data", (),).pack(side=tk.TOP, anchor=tk.W, pady=12)

        system_frame = ttk.LabelFrame(self.right_frame, style="Links.TFrame", text=" New Data Project ", relief=tk.GROOVE)
        system_frame.pack(side=tk.TOP, anchor=tk.W, fill="both", expand="yes")

        system_title_label = ttk.Label(system_frame, text="System Name:")
        system_title_label.pack(side=tk.LEFT, anchor=tk.N, padx=(12, 0), pady=6)

        system_title_entry = self.make_entry(system_frame, app)
        system_title_entry.pack(side=tk.LEFT, anchor=tk.N, pady=6)
        system_title_entry.focus()

        subsystem_button = ttk.Button(system_frame, text='Cancel', style="Links.TButton", command=lambda: self.show_help())
        subsystem_button.pack(side=tk.RIGHT, anchor=tk.N, pady=6, padx=(0, 12))

        cancel_button = ttk.Button(system_frame, text='Add Subsystem', style="Entry.TButton", command=lambda: self.subsystem_entry(app))
        cancel_button.pack(side=tk.RIGHT, anchor=tk.N, pady=6, padx=(0, 12))


class LinksFrame(ttk.Frame):
    """ A container of links and label that packs vertically"""

    def __init__(self, parent, title, links=None):
        super().__init__(parent, style="Links.TFrame")
        ttk.Label(self, text=title, style="SubHeading.TLabel").pack(
            side=tk.TOP, anchor=tk.W, pady=4, padx=1
        )

        if links:
            for label, action in links:
                if action:
                    self.add_link(label, action)
                else:
                    self.add_label(label)

    def add_link(self, label, action):
        ttk.Button(self, text=label, style="Links.TButton", command=action).pack(side=tk.TOP, anchor=tk.W)

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
