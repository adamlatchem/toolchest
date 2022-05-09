#!/usr/bin/env python
#
# Base class for a GUI Application using Tk
#
from __future__ import generators, print_function, unicode_literals
import sys
if sys.version_info[0] < 3:
    str = unicode
    import Tkinter as tkinter
    import tkMessageBox as messagebox
else:
    import tkinter
    import tkinter.messagebox as messagebox
import os
import platform
import traceback

oldhook = sys.excepthook


def exception_handler(exctype, exception, traceback):
    global oldhook
    print(traceback)
    messagebox.showerror(title='Error', message=str(exception))
    if oldhook:
        oldhook(exctype, exception, traceback)


sys.excepthook = exception_handler


def configure_if(widget, option, value):
    config = widget.config()
    if option in config:
        widget[option] = value


class GUIApplication(object):
    def __init__(self, root, title):
        self.root = root
        self._is_dirty = False
        self.title(title)
        self.root.grid()
        self.root.report_callback_exception = self.report_callback_exception
        self.root.protocol("WM_DELETE_WINDOW", self.cmd_quit)

    def title(self, title):
        self._title = title
        if self._is_dirty:
            title = title + '*'
        self.root.title(title)

    def apply_style(self, widget, bg):
        widget_class = widget.winfo_class()
        if widget_class == 'Menu':
            return

        configure_if(widget, 'insertwidth', 4)
        configure_if(widget, 'insertofftime', '500')
        configure_if(widget, 'insertontime', '500')
        configure_if(widget, 'disabledbackground', bg)
        configure_if(widget, 'disabledforeground', 'darkred')
        configure_if(widget, 'highlightthickness', 0)
        configure_if(widget, 'highlightbackground', bg)
        configure_if(widget, 'relief', tkinter.FLAT)
        configure_if(widget, 'borderwidth', 0)

        if widget_class == 'Frame':
            bg = widget['bg']

        configure_if(widget, 'background', bg)

        for child in widget.winfo_children():
            self.apply_style(child, bg)

    def create_scrolled(self, parent, cls, vertical, horizontal):
        outer = tkinter.Frame(parent)
        outer.configure(background=parent['background'])
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(0, weight=1)

        if vertical:
            vsb = tkinter.Scrollbar(outer, orient=tkinter.VERTICAL)
            vsb.grid(column=1, row=0, sticky=tkinter.NS)
        if horizontal:
            hsb = tkinter.Scrollbar(outer, orient=tkinter.HORIZONTAL)
            hsb.grid(column=0, row=1, sticky=tkinter.EW)

        inner = cls(outer)
        if cls == tkinter.Text:
            inner.configure(wrap=tkinter.NONE)
        if vertical:
            inner.config(yscrollcommand=vsb.set)
        if horizontal:
            inner.config(xscrollcommand=hsb.set)
        inner.grid(column=0, row=0, sticky=tkinter.NSEW)

        if vertical:
            vsb.config(command=inner.yview)
        if horizontal:
            hsb.config(command=inner.xview)
        return inner, outer

    def labelled_entry(self, text, value, column, row):
        host_label = tkinter.Label(self.root, text=text)
        host_label.grid(column=column, row=row, sticky=tkinter.E)
        host_entry = tkinter.Entry(self.root)
        if value:
            host_entry.insert(0, value)
        host_entry.grid(column=column + 1, row=row)
        return (host_label, host_entry)

    def extend_bindtags(self, widget):
        bindtags = list(widget.bindtags())
        bindtags.insert(2, 'KeyUp')
        widget.bindtags(tuple(bindtags))

    def show_error(self, exception):
        type, exception, traceback = sys.exc_info()
        exception_handler(type, exception, traceback)

    def grid_weights(self, grid, column_weights, row_weights):
        columns, rows = grid.grid_size()
        if not type(column_weights) is list:
            column_weights = [column_weights]
        if not type(row_weights) is list:
            row_weights = [row_weights]
        for r, rw in zip(range(rows), row_weights):
            grid.rowconfigure(r, weight=rw)
        for c, cw in zip(range(columns), column_weights):
            grid.columnconfigure(c, weight=cw)

    def report_callback_exception(self, type, value, tb):
        exception_handler(type, value, tb)

    def on_not_implemented(self, event=None):
        messagebox.showerror(title='Error', message='Not implemented.')

    def cmd_quit(self, force=False):
        if self._is_dirty:
            result = messagebox.askquestion(
                'Confirm Quit',
                'There are unsaved changes. Quit without saving?',
                icon='warning')
            if result != 'yes':
                return
        if force:
            self.root.destroy()
        else:
            self.root.quit()

    def cmd_dirty(self):
        if not self._is_dirty:
            self._is_dirty = True
            self.title(self._title)

    def cmd_clean(self):
        if self._is_dirty:
            self._is_dirty = False
            self.title(self._title)


def main(application_class):
    """ Call to start an application of type application_class """
    root = tkinter.Tk()

    if getattr(sys, 'frozen', False):
        bundle_dir = sys._MEIPASS
    else:
        bundle_dir = os.path.dirname(os.path.abspath(__file__))
    file, ext = os.path.splitext(sys.argv[0])
    file = os.path.basename(file)
    icon_file = os.path.join(bundle_dir, file + '.ico')
    if os.path.isfile(icon_file):
        try:
            root.iconbitmap(icon_file)
        except:
            pass

    app = application_class(root)

    if platform.system() == 'Darwin':
        # Focus window on Mac OS
        os.system(
            '''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Python" to true' ''')

    tkinter.mainloop()
