#!/usr/bin/python

from Tkinter import *
import tkFont
import ttk
import os
import subprocess
import threading
from tkFileDialog import askopenfilename
from tkMessageBox import showwarning
from tkFileDialog import asksaveasfilename
from tkFileDialog import askdirectory

class CustomText(Text):
    '''A text widget with a new method, highlight_pattern()

    example:

    text = CustomText()
    text.tag_configure("red", foreground="#ff0000")
    text.highlight_pattern("this should be red", "red")

    The highlight_pattern method is a simplified python
    version of the tcl code at http://wiki.tcl.tk/3246
    '''
    def __init__(self, *args, **kwargs):
        tk.Text.__init__(self, *args, **kwargs)

    def highlight_pattern(self, pattern, tag, start="1.0", end="end",
                          regexp=False):
        '''Apply the given tag to all text that matches the given pattern

        If 'regexp' is set to True, pattern will be treated as a regular
        expression.
        '''

        start = self.index(start)
        end = self.index(end)
        self.mark_set("matchStart", start)
        self.mark_set("matchEnd", start)
        self.mark_set("searchLimit", end)

        count = IntVar()
        while True:
            index = self.search(pattern, "matchEnd","searchLimit",
                                count=count, regexp=regexp)
            if index == "": break
            self.mark_set("matchStart", index)
            self.mark_set("matchEnd", "%s+%sc" % (index, count.get()))
            self.tag_add(tag, "matchStart", "matchEnd")

class RoomEditor(CustomText):

    def __init__(self, master, **options):
        Text.__init__(self, master, **options)

        self.config(
            wrap=WORD, # use word wrapping
            undo=True,
            width=100
            )

        self.filename = None # current document

    def _getfilename(self):
        return self._filename

    def _setfilename(self, filename):
        self._filename = filename
        title = os.path.basename(filename or "(new document)")
        root.title("CMIXIDE - " + title)

    filename = property(_getfilename, _setfilename)

    def edit_modified(self, value=None):
        # Python 2.5's implementation is broken
        return self.tk.call(self, "edit", "modified", value)

    modified = property(edit_modified, edit_modified)

    def load(self, filename):
        text = open(filename).read()
        self.delete(1.0, END)
        self.insert(END, text)
        self.mark_set(INSERT, 1.0)
        self.modified = False
        self.filename = filename
        title = os.path.basename(filename or "(new document)")
        root.title("CMIXIDE - " + title)

    def save(self, filename=None):
        if filename is None:
            filename = self.filename
        f = open(filename, "w")
        s = self.get(1.0, END)
        try:
            f.write(s.rstrip())
            f.write("\n")
        except UnicodeEncodeError:
            root.quit()
        finally:
            f.close()
        self.modified = False
        self.filename = filename

FILETYPES = [
    ("RTcmix Scores", "*.sco"), ("PYCMIX Files", "*.py"), ("All Files", "*")
    ]

class Cancel(Exception):
    pass

def open_as():
    f = askopenfilename(parent=root, filetypes=FILETYPES)
    if not f:
        raise Cancel
    try:
        editor.load(f)
    except IOError:
        showwarning("Open", "Cannot open the file.")
        raise Cancel
    editor.filename=f
    extension = f.split('.')[-1]
    global CMIX, PYCMIX, CMIXCMD
    if (extension == 'sco'):
        CMIXCMD = CMIX
    elif (extension == 'py'):
        CMIXCMD = PYCMIX

def save_as():
    f = asksaveasfilename(parent=root, defaultextension=".txt")
    if not f:
        raise Cancel
    try:
        editor.save(f)
    except IOError:
        showwarning("Save As", "Cannot save the file.")
        raise Cancel

def save():
    if editor.filename:
        try:
            editor.save(editor.filename)
        except IOError:
            showwarning("Save", "Cannot save the file.")
            raise Cancel
    else:
        save_as()

def save_if_modified():
    if not editor.modified:
        return
    if askyesnocancel("CMIXIDE", "Document modified. Save changes?"):
        save()

def askyesnocancel(title=None, message=None, **options):
    import tkMessageBox
    s = tkMessageBox.Message(
        title=title, message=message,
        icon=tkMessageBox.QUESTION,
        type=tkMessageBox.YESNOCANCEL,
        **options).show()
    if isinstance(s, bool):
        return s
    if s == "cancel":
        raise Cancel
    return s == "yes"

def file_new(event=None):
    try:
        save_if_modified()
        editor.clear()
    except Cancel:
        pass
    return "break" # don't propagate events

def file_open(event=None):
    try:
        save_if_modified()
        open_as()
    except Cancel:
        pass
    apply_tags()
    return "break"

def file_save(event=None):
    try:
        editor.save(sys.argv[1])
    except Cancel:
        pass
    except (IOError,IndexError):
        file_save_as()
    return "break"

def file_save_as(event=None):
    try:
        save_as()
    except Cancel:
        pass
    return "break"

def file_quit(event=None):
    halt_score()
    save_if_modified()
    root.quit()

def pycmix_score_thread(fn):
    try:
        sub = subprocess.Popen([CMIXCMD,"-f",editor.filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except TypeError:
        return "break"
    proc.append(sub)
    output.config(state=NORMAL)
    output.delete(1.0, END)
    while sub:
        out = sub.stdout.read(1)
        if out == '' and sub.poll() != None:
            break
        if out != '':
            output.insert(END,out)
            sys.stdout.flush()
    output.config(state=DISABLED)
    editor.focus_set()

def run_score(event=None):
    save_if_modified()
    threading.Thread(target=pycmix_score_thread,args=(editor.filename,)).start()

def halt_score(event=None):
    for s in proc:
        try:
            s.terminate()
        except OSError:
            pass

#TODO: put CMIX and PYCMIX in a class
def read_defaults(bindir):
    global CMIX, PYCMIX
    CMIX = bindir+"/CMIX"
    PYCMIX = bindir+"/PYCMIX"
    if not os.path.exists(CMIX):
        showwarning("CMIXIDE", "Could not find CMIX binary")
        try:
           with open(bindir) as f:
                content = f.readlines()
                output.config(state=NORMAL)
                output.insert(END,content)
                output.config(state=DISABLED)
        except IOError:
            output.config(state=NORMAL)
            output.insert(END,"Could not find CMIX and PYCMIX\n")
            output.config(state=DISABLED)
            f = askdirectory(parent=root,title="Select RTcmix bin directory")
            if not f:
                raise Cancel
            try:
                read_defaults(f)
            except IOError:
                showwarning("Open Directory", "Cannot open the directory.")
                raise Cancel
    else:
        output.config(state=NORMAL)
        output.insert(END,"CMIX binary found!\n")
        output.config(state=DISABLED)

def read_tags ():
    global rtcmix_tags, inst_tags
    try:
        rtcmix_tags = open("gui/rtcmix.tags")
    except IOError:
        output.config(state=NORMAL)
        output.insert(END,"rtcmix.tags file doesn\'t exist -- don't worry about this yet though")
        output.config(state=DISABLED)

    try:
        inst_tags = open("gui/inst.tags")
    except IOError:
        output.config(state=NORMAL)
        output.insert(END,"rtcmix.tags file doesn\'t exist -- don't worry about this yet though")
        output.config(state=DISABLED)


def apply_tags (event=None):
    for t in rtcmix_tags:
        editor.highlight_pattern(t.split('\n')[0], "rtcmix-keywords")
    for t in inst_tags:
        editor.highlight_pattern(t.split('\n')[0], "instrument-keywords")


####################################################
proc = []
lines = []
root = Tk()
root.title("CMIXIDE")
root.option_add('*tearOff', False)
menubar = Menu(root)
root.config(menu = menubar)
file_menu = Menu(menubar)
edit_menu = Menu(menubar)
help_menu = Menu(menubar)

menubar.add_cascade(menu = file_menu, label = 'File')
menubar.add_cascade(menu = edit_menu, label = 'Edit')
menubar.add_cascade(menu = help_menu, label = 'Help')

file_menu.add_command(label = 'New', command=file_new)
file_menu.add_command(label = 'Open', command=file_open)
file_menu.add_command(label = 'Save', command=file_save)
file_menu.add_command(label = 'Save As...', command=file_save_as)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=file_quit)

edit_menu.add_cascade(label = "Coming Soon!")
help_menu.add_cascade(label = "NO HELP FOR YOU!")

editor = RoomEditor(root)
xscroll = ttk.Scrollbar(root, orient = HORIZONTAL, command = editor.xview)
yscroll = ttk.Scrollbar(root, orient = VERTICAL, command = editor.yview)
editor.config(xscrollcommand = xscroll.set, yscrollcommand = yscroll.set)
editor.grid(row = 1, column = 0, columnspan=3, sticky='nsew')
xscroll.grid(row = 2, column = 0, columnspan=3, sticky = 'ew')
yscroll.grid(row = 1, column = 3, sticky = 'ns')
run_button = ttk.Button(text="Play Scorefile",command=run_score)
stop_button = ttk.Button(text="Stop Playback",command=halt_score)
stop_button.grid(row=3,column=2)
run_button.grid(row=3,column=0,sticky='w')
console_label = Label(text="PYCMIX Console Output")
console_label.grid(row=3,column=1)
output = RoomEditor(root,height=10,state=DISABLED)
xscroll2 = ttk.Scrollbar(root, orient = HORIZONTAL, command = output.xview)
yscroll2 = ttk.Scrollbar(root, orient = VERTICAL, command = output.yview)
output.config(xscrollcommand = xscroll2.set, yscrollcommand = yscroll2.set)
output.grid(row = 4, column = 0, columnspan=3, sticky='nsew')
xscroll2.grid(row = 5, column = 0, columnspan=3, sticky = 'ew')
yscroll2.grid(row = 4, column = 3, sticky = 'ns')
ttk.Sizegrip(root).grid(row=5,column=3)

editor.focus_set()
bold_font = tkFont.Font(editor, editor.cget("font"))
bold_font.configure(weight="bold")
editor.tag_configure("rtcmix-keywords", foreground='dark blue')
editor.tag_configure("instrument-keywords", foreground='dark green', font=bold_font)

root.rowconfigure(1,weight=1)
root.columnconfigure(1,weight=1)
try:
    editor.load(sys.argv[1])
except (IndexError, IOError):
    pass

editor.bind("<Control-n>", file_new)
editor.bind("<Control-o>", file_open)
editor.bind("<Control-s>", file_save)
editor.bind("<Control-Shift-S>", file_save_as)
editor.bind("<Control-r>", run_score)
editor.bind("<Control-q>", file_quit)
editor.bind("<Control-w>", file_quit)
editor.bind("<Command-n>", file_new)
editor.bind("<Command-o>", file_open)
editor.bind("<Command-s>", file_save)
editor.bind("<Command-Shift-S>", file_save_as)
editor.bind("<Command-r>", run_score)
editor.bind("<Command-q>", file_quit)
editor.bind("<Command-w>", file_quit)
editor.bind("<Control-Shift-T>", apply_tags)
root.protocol("WM_DELETE_WINDOW", file_quit) # window close button

CMIX = ""
PYCMIX = ""
read_defaults(os.path.dirname(sys.argv[0]))
CMIXCMD = CMIX
rtcmix_tags = []
inst_tags = []
read_tags()
mainloop()
