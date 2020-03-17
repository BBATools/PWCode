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

import webbrowser
import tkinter as tk
from tkinter import ttk
from collections import OrderedDict


class WelcomeTab(ttk.Frame):
    """ A start-up screen with recent folder and useful links """

    def __init__(self, parent, app):
        super().__init__(parent, style="Welcome.TFrame", padding=[56, 12, 8, 8])
        ttk.Label(self, text=app.settings.name, style="Heading.TLabel").pack(
            side=tk.TOP, anchor=tk.W
        )
        ttk.Label(self, text=app.settings.desc, style="SubHeading.TLabel").pack(
            side=tk.TOP, anchor=tk.W
        )
        ttk.Label(self, text=app.settings.long_desc, style="Text.TLabel").pack(
            side=tk.TOP, anchor=tk.W
        )        

        frame = ttk.Frame(self, style="Welcome.TFrame")
        frame.pack(fill=tk.BOTH, expand=1, pady=12)

        left_frame = ttk.Frame(frame, style="Welcome.TFrame")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        LinksFrame(
            left_frame,
            "Start",
            (
                ("New File", app.command_callable("new_file")),
                ("Open File ...", app.command_callable("open_file")),
                ("Open Folder ...", app.command_callable("open_folder")),
                # ("Clone git repository ...", None),
            ),
        ).pack(side=tk.TOP, anchor=tk.W, pady=12)

        self.recent_links_frame = RecentLinksFrame(left_frame, app).pack(side=tk.TOP, anchor=tk.W, pady=12)

        # LinksFrame(
        #     left_frame,
        #     "Help",
        #     (
        #         ("Product documentation", None),
        #         # ("Introductory videos", None),
        #         ("GitHub repository", None),
        #         # ("StackOverflow", None),
        #     ),
        # ).pack(side=tk.TOP, anchor=tk.W, pady=12)

        right_frame = ttk.Frame(frame, style="Welcome.TFrame")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=1)
        # ttk.Label(right_frame, text="Quick links", style="Links.TLabel").pack(
        #     side=tk.TOP, anchor=tk.W, pady=16, padx=1
        # )

        LinksFrame(
            right_frame,
            "Help",
            (
                # ("Product documentation", None),
                # ("Introductory videos", None),
                # ("GitHub repository", app.command_callable("open_home_url('https://github.com/BBATools/PreservationWorkbench')")),
                # ("GitHub repository", app.command_callable("open_home_url")),
                ("GitHub repository", self.open_home_url),                
                # ("StackOverflow", None),
            ),
        ).pack(side=tk.TOP, anchor=tk.W, pady=12)


    def open_home_url(self):
        webbrowser.open('https://github.com/BBATools/PWCode', new=2)


class LinksFrame(ttk.Frame):
    """ A container of links and label that packs vertically"""

    def __init__(self, parent, title, links=None):
        super().__init__(parent, style="Links.TFrame")
        ttk.Label(self, text=title, style="SubHeading.TLabel").pack(
            side=tk.TOP, anchor=tk.W, pady=4, padx=1
        )

        self.recent_links = OrderedDict() 

        if links:
            for label, action in links:
                if action:
                    self.add_link(label, action)
                else:                  
                    self.add_label(label)


    def update_recent_links(self, file_obj):  
        if file_obj.path in self.recent_links.keys():
            del self.recent_links[file_obj.path]
        self.recent_links.update({file_obj.path:file_obj})

        for widget in self.winfo_children():
            if isinstance(widget, ttk.Button):
                widget.destroy()   

        for path, file_obj in reversed(self.recent_links.items()):
            action = lambda p=path: self.app.command_callable("open_file")(p)  
            self.add_link(file_obj.basename,lambda p=path: self.app.command_callable("open_file")(p))                                                  


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


    def on_file_closed(self, file_obj):
        """model callback"""
        self.update_recent_links(file_obj)


    # def on_file_open(self, file_obj):
    #     """model callback"""
    #     if file_obj.path in self.recent_links.keys():
    #         link = self.recent_links[file_obj.path]
    #         link.destroy()
    #         del self.recent_links[file_obj.path]
  


