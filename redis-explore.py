#!/usr/bin/env python
#
# REDIS Explorer GUI
#
import redis
try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk
import tkMessageBox

class Application(tk.Frame, object):
    def __init__(self, master):
        super(Application, self).__init__(master)
        self.grid()
        self.create_widgets(master)
        self.apply_style(master, 'white')
        self.cmd_disconnect()

    def connect(self, db):
        host = self.host_entry.get()
        port = int(self.port_entry.get())
        self.r = redis.StrictRedis(
            host = host, 
            port = port, 
            db = db, 
            password = self.password_entry.get())
        self.master.title("REDIS Explorer " + host + ":" + str(port))

    def apply_style(self, widget, bg):
        widget_class = widget.winfo_class()
        if widget_class == 'Entry' or widget_class == 'Text':
            widget.config(insertwidth = 4, insertofftime = '500', insertontime = '500')

        if widget_class == 'Entry':
            widget.config(disabledbackground = bg, disabledforeground = 'darkred')
        else:
            widget.config(highlightthickness = 0)
        widget.config(highlightbackground = bg, relief = tk.FLAT,borderwidth = 0)
        if widget_class == 'Frame':
            bg = widget['bg']
        widget.config(background = bg)

        for child in widget.winfo_children():
            self.apply_style(child, bg)

    def create_scrolled(self, master, cls, vertical, horizontal):
        outer = tk.Frame(master)
        outer.configure(background = master['background'])

        if vertical:
            vsb = tk.Scrollbar(outer, orient=tk.VERTICAL)
            vsb.pack(side = tk.RIGHT, fill = tk.Y)
        if horizontal:
            hsb = tk.Scrollbar(outer, orient=tk.HORIZONTAL)
            hsb.pack(side = tk.BOTTOM, fill = tk.X)

        inner = cls(outer)
        if cls == tk.Text:
            inner.configure(wrap=tk.NONE)
        if vertical:
            inner.config(yscrollcommand = vsb.set)
        if horizontal:
            inner.config(xscrollcommand = hsb.set)
        inner.pack(fill = tk.BOTH)

        if vertical:
            vsb.config(command = inner.yview)
        if horizontal:
            hsb.config(command = inner.xview)
        outer.pack()
        return inner, outer

    def labelled_entry(self, master, text, value, column, row):
        host_label = tk.Label(master, text = text)
        host_label.grid(column = column, row = row, sticky = tk.E)
        host_entry = tk.Entry(master)
        if value:
            host_entry.insert(0, value)
        host_entry.grid(column = column + 1, row = row)
        return (host_label, host_entry)

    def create_widgets(self, master):
        self.connection_frame = tk.Frame(master)
        self.connection_frame.grid()
        self.connection_frame.grid(column = 0, row = 0, sticky = tk.NSEW)

        self.connect_button = tk.Button(self.connection_frame, width=32)
        self.connect_button.grid(column = 0, row = 0, columnspan=2, sticky=tk.NSEW)
        self.host_label, self.host_entry = self.labelled_entry(
            self.connection_frame, 'Host:', 'localhost', 0, 1
        )
        self.port_label, self.port_entry = self.labelled_entry(
            self.connection_frame, 'Port:', '6379', 0, 2
        )
        self.password_label, self.password_entry = self.labelled_entry(
            self.connection_frame, 'Password:', None, 0, 3
        )
        self.password_entry['show'] = '*'
        self.password_entry.focus_set()
        self.password_entry.bind("<Return>", self.cmd_connect)
        self.database_label = tk.Label(self.connection_frame, text='Database:')
        self.database_label.grid(column = 0, row = 11, sticky = tk.E)
        self.database_label.grid_remove()
        self.database_list = None
        self.grid_weights(self.connection_frame, 1, 0)

        self.key_list, self.key_list_scrolled = self.create_scrolled(
            self.master, tk.Listbox, True, True)
        self.key_list_scrolled.grid(column = 0, row = 1, sticky = tk.NSEW)
        self.key_list.bind('<<ListboxSelect>>', self.cmd_select_key)

        self.object_frame = tk.Frame(master, bg='lightgrey')
        self.object_frame.grid()
        self.object_frame.grid(column = 1, row = 0, rowspan = 2, sticky = tk.NSEW)

        self.object_delete = tk.Button(self.object_frame, width=10)
        self.object_delete.config(text = 'Delete')
        self.object_delete.config(command = self.cmd_delete)
        self.object_delete.grid(column = 1, row = 0, sticky = tk.E)
        self.object_set_as = tk.Button(self.object_frame, width=10)
        self.object_set_as.config(text = 'Set As ...')
        self.object_set_as.config(command = self.cmd_set_as)
        self.object_set_as.grid(column = 2, row = 0, sticky = tk.E)
        self.object_set = tk.Button(self.object_frame, width=10)
        self.object_set.config(text = 'Set')
        self.object_set.config(command = self.cmd_set)
        self.object_set.grid(column = 3, row = 0, sticky = tk.E)

        self.key_label = tk.Label(self.object_frame, text='Key:', foreground='blue', height=4, anchor=tk.S, pady=4)
        self.key_label.grid(column = 0, row = 1, sticky = tk.S + tk.W)
        self.key_entry = tk.Entry(self.object_frame)
        self.key_entry.grid(column = 1, row = 1, columnspan=4, sticky=tk.S + tk.EW)
        self.key_entry.config(state = tk.DISABLED)
        self.key_entry.bind("<Return>", self.cmd_set_as_phase_2)
        self.key_entry.bind("<FocusOut>", self.cmd_set_as_finally)
        self.key_entry.bind("<Button-1>", self.cmd_set_as)
        self.object_view, self.object_view_scrolled = self.create_scrolled(
            self.object_frame, tk.Text, True, True)

        self.object_view_scrolled.grid(column = 0, row = 2, columnspan = 5, sticky = tk.NSEW)
        self.grid_weights(self.object_frame, [0, 1, 0, 0, 0, 0], [0, 0, 1])

        self.grid_weights(master, [0, 1], [0, 1])

    def cmd_connect(self, evt=None):
        try:
            self.connect(0)
            number_databases = int(self.r.config_get('databases')['databases'])
            databases = ['db' + str(d) for d in xrange(number_databases)]
            self.database = tk.StringVar()
            self.database.trace('w', self.cmd_change_db)
            self.database.set(databases[0])
            if self.database_list:
                self.database_list.destroy()
            self.database_list = tk.OptionMenu(self.connection_frame, self.database, *databases)
            self.database_list.grid(column = 1, row = 11, sticky=tk.NSEW)
            self.connect_button.config(text = 'Disconnect', command = self.cmd_disconnect)
            for w in [self.host_label, self.host_entry, self.port_label, self.port_entry, self.password_label, self.password_entry]:
                w.grid_remove()
            for w in [self.database_label, self.object_frame]:
                w.grid()
        except Exception,e:
            self.cmd_disconnect()
            self.show_error(e)

    def cmd_change_db(self, var, two, mode):
        db = int(self.database.get()[2:])
        self.connect(db)
        self.clear_select_key()
        self.cmd_list_keys()

    def cmd_list_keys(self):
        self.key_list.delete(0, self.key_list.size())
        self.key_list.insert(0, *(sorted(self.r.keys())))

    def cmd_disconnect(self):
        self.r = None
        self.clear_select_key()
        self.key_list.delete(0, self.key_list.size())
        if self.database_list:
            self.database_list.destroy()
        self.connect_button.config(text = 'Connect', command = self.cmd_connect)
        self.master.title("REDIS Explorer")
        for w in [self.host_label, self.host_entry, self.port_label, self.port_entry, self.password_label, self.password_entry]:
            w.grid()
        for w in [self.database_label, self.object_frame]:
            w.grid_remove()

    def cmd_select_key(self, evt):
        w = evt.widget
        index = self.key_index()
        if index == -1:
            return
        key = w.get(index)
        self.key_entry.config(state = tk.NORMAL)
        self.key_entry.delete(0, tk.END)
        self.key_entry.insert(0, key)
        self.key_entry.config(state = tk.DISABLED)
        value = self.r.get(key)
        self.object_view.delete(1.0, tk.END)
        self.object_view.insert(1.0, value)

    def cmd_set(self):
        key = self.key_entry.get()
        value = self.object_view.get(1.0, tk.END)
        self.r.set(key, value)
        self.r.bgsave()

    def cmd_set_as(self, evt = None):
        key = self.key_entry.get()
        self.old_key = key
        self.object_delete.config(state = tk.DISABLED)
        self.object_set.config(state = tk.DISABLED)
        self.key_entry.config(state = tk.NORMAL)
        self.object_set_as.config(text = 'YES, set as')
        self.object_set_as.config(command = self.cmd_set_as_phase_2)
        self.key_entry.focus_set()

    def cmd_set_as_phase_2(self, evt = None):
        key = self.key_entry.get()
        value = self.object_view.get(1.0, tk.END)
        self.r.set(key, value)
        self.r.bgsave()
        self.cmd_list_keys()
        self.old_key = key
        self.cmd_set_as_finally()

    def cmd_set_as_finally(self, evt = None):
        self.key_entry.delete(0, tk.END)
        self.key_entry.insert(0, self.old_key)
        self.key_entry.config(state = tk.DISABLED)
        self.object_delete.config(state = tk.NORMAL)
        self.object_set.config(state = tk.NORMAL)
        self.object_set_as.config(text = 'Set As ...')
        self.object_set_as.config(command = self.cmd_set_as)
        self.key_list.focus_set()

    def cmd_delete(self):
        self.old_key = self.key_entry.get()
        if len(self.old_key) == 0:
            return
        self.object_set_as.config(state = tk.DISABLED)
        self.object_set.config(state = tk.DISABLED)
        self.object_delete.config(text = 'YES, delete')
        self.object_delete.config(command = self.cmd_delete_phase_2)
        self.object_delete.focus_set()
        self.object_delete.bind("<FocusOut>", self.cmd_delete_finally)

    def cmd_delete_phase_2(self):
        self.r.delete(self.old_key)
        self.r.bgsave()
        self.cmd_list_keys()
        self.clear_select_key()
        self.cmd_delete_finally()

    def cmd_delete_finally(self, evt = None):
        self.object_set_as.config(state = tk.NORMAL)
        self.object_set.config(state = tk.NORMAL)
        self.object_delete.config(text = 'Delete')
        self.object_delete.config(command = self.cmd_delete)
        self.object_delete.unbind("<FocusOut>")

    def clear_select_key(self):
        self.key_entry.config(state = tk.NORMAL)
        self.key_entry.delete(0, tk.END)
        self.key_entry.config(state = tk.DISABLED)
        self.object_view.delete(1.0, tk.END)

    def show_error(self, exception):
        tkMessageBox.showerror(title='Error', message=exception.message)

    def key_index(self):
        selection = self.key_list.curselection()
        if len(selection) == 0:
            return -1
        index = int(selection[0])
        return index        

    def grid_weights(self, grid, column_weights, row_weights):
        columns, rows = grid.grid_size()
        if not type(column_weights) is list:
            column_weights = [column_weights]
        if not type(row_weights) is list:
            row_weights = [row_weights]
        for r, rw in zip(xrange(rows), row_weights):
            grid.rowconfigure(r, weight = rw)
        for c, cw in zip(xrange(columns), column_weights):
            grid.columnconfigure(c, weight = cw)
            
def main():
    root = tk.Tk()
    app = Application(root)
    app.mainloop()

if __name__ == '__main__':
    main()
