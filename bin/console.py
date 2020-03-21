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

import logging, threading, time, queue, datetime, sys
from text.tktextext import EnhancedText
from settings import COLORS
import tkinter as tk
from gui.scrollbar_autohide import AutoHideScrollbar


# class Processing(threading.Thread):
# Original her: https://github.com/beenje/tkinter-logging-text-widget/blob/master/main.py
class ConsoleUi:
    def __init__(self, frame, file_obj):
        self.frame = frame
        self.file_obj = file_obj
        self.text = EnhancedText(
            frame, 
            state='disabled',  # TODO: Denne som gjør at ikke shortcuts for copy mm virker?
            background=COLORS.bg, 
            # background=COLORS.text_bg,
            # background=COLORS.sidebar_bg,            
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
            # selectbackground=COLORS.sidebar_bg,
            # inactiveselectbackground = COLORS.sidebar_bg,
            # selectforeground=COLORS.text_fg,
            padx = 5,
            pady = 5,            
            height=10)

        self.text.pack(side="bottom", fill="both")
        self.text.pack_propagate(0)
        self.text.configure(font='TkFixedFont')
        self.text.tag_config('INFO', foreground='green')
        self.text.tag_config('DEBUG', foreground=COLORS.status_bg)
        self.text.tag_config('WARNING', foreground='blue')
        self.text.tag_config('ERROR', foreground='red')
        self.text.tag_config('CRITICAL', foreground='red', underline=1)
        
        # Create a logging handler using a queue
        self.log_queue = queue.Queue()
        self.queue_handler = QueueHandler(self.log_queue)
        # formatter = logging.Formatter('%(asctime)s: %(message)s')
        formatter = logging.Formatter('%(message)s')
        self.queue_handler.setFormatter(formatter)
        self.logger = logging.getLogger(self.file_obj.path)
        self.logger.setLevel('DEBUG')
        self.logger.addHandler(self.queue_handler)
        # Start polling messages from the queue
        self.frame.after(100, self.poll_log_queue)

        self.text.v_scrollbar = AutoHideScrollbar(
            self.text, 
            command = self.v_scrollbar_scroll,
            width = 10,               
            troughcolor = COLORS.bg, 
            buttoncolor = COLORS.bg,                
            thumbcolor = COLORS.status_bg, 
            )
        self.text["yscrollcommand"] = self.text.v_scrollbar.set 
        self.text.v_scrollbar.pack(side="right", fill="y")


    def v_scrollbar_scroll(self, *args):
        self.text.yview(*args)
        self.text.event_generate("<<VerticalScroll>>")           


    def display(self, record):
        msg = self.queue_handler.format(record)
        self.text.configure(state='normal')
        self.text.insert(tk.END, msg + '\n', record.levelname)
        # self.text.update_idletasks()
        self.text.configure(state='disabled')
        # Autoscroll to the bottom
        self.text.yview(tk.END)


    def poll_log_queue(self):
        # Check every 100ms if there is a new message in the queue to display
        while True:
            try:
                record = self.log_queue.get(block=False)
            except queue.Empty:
                break
            else:
                self.display(record)
        self.frame.after(100, self.poll_log_queue)


class Processing():
    def __init__(self, file_obj):
        self.file_obj = file_obj
        super().__init__()
        self.logger = logging.getLogger(self.file_obj.path)


    def show_message(self, message):
        def log_message(message):
            self.logger.log(logging.DEBUG, message)
        
        threading.Thread(target=log_message, args=(message,),daemon = True).start() 


    def run_file(self, file_obj):    
        def log_run(file_obj):
            from subprocess import Popen, PIPE, CalledProcessError

            self.logger.log(logging.INFO, 'Process started...')
            with Popen(["python3", file_obj.path], stdout=PIPE, bufsize=1, universal_newlines=True) as p:
                for line in p.stdout:
                    # print(line)
                    # TODO: Vil det gjøre forskjell hvis logger definert utenfor klassen?
                    self.logger.log(logging.INFO, line)
                    # print(line, end='') # process line here

            if p.returncode != 0:
                raise CalledProcessError(p.returncode, p.args)

            # print('test')
            # self.logger.log(logging.INFO, 'Process started...')
            # popen = subprocess.Popen(["python3", file_obj.path], stdout=subprocess.PIPE, universal_newlines=True)
            # for stdout_line in iter(popen.stdout.readline, ""):
            #     output =  yield stdout_line 
            #     self.logger.log(logging.INFO, output)
            # popen.stdout.close()
            # return_code = popen.wait()
            # if return_code:
            #     raise subprocess.CalledProcessError(return_code, cmd)

        threading.Thread(target=log_run, args=(file_obj,),daemon = True).start()              
    
    
    def run_file2(self, file_obj):
        def log_run(file_obj):
            import multiprocessing, sys, traceback, subprocess, selectors
            # from logging.handlers import RotatingFileHandler


            p = subprocess.Popen(
                ["python3", file_obj.path], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            sel = selectors.DefaultSelector()
            sel.register(p.stdout, selectors.EVENT_READ)
            sel.register(p.stderr, selectors.EVENT_READ)

            while True:
                for key, _ in sel.select():
                    # print(key.fileobj)
                    data = key.fileobj.read().decode()
                    if not data:
                        exit()
                    if key.fileobj is p.stdout:
                        # print('test')
                        self.logger.log(logging.INFO, data)
                        # print(data, end="")
                    else:
                        print(data, end="", file=sys.stderr) 

        threading.Thread(target=log_run, args=(file_obj,),daemon = True).start()                         



    def display_time(self):    
        def log_run():
            # self.logger.debug('Clock started') 
            self.logger.log(logging.INFO, 'Clock started')
            previous = -1
            while True:
                now = datetime.datetime.now()
                if previous != now.second:
                    previous = now.second
                    if now.second % 5 == 0:
                        level = logging.INFO
                    else:
                        level = logging.INFO
                    self.logger.log(level, now)
                self.logger.log(logging.INFO, 'test')
                time.sleep(0.2)

        
        threading.Thread(target=log_run,daemon = True).start()                  


class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(record)



