#!/usr/bin/env python
#
# REDIS Explorer GUI
#
import redis
import tkMessageBox
import GUIApplication
from   GUIApplication import tk

class RedisConnect(GUIApplication.GUIApplication):
    def __init__(self, root):
        super(RedisConnect, self).__init__(root, 'REDIS Connection')
        self.database_list = None
        self.explorer = None
        self.create_widgets(root)
        self.apply_style(root, 'white')

    def create_widgets(self, root):
        self.root.grid()

        self.connect_button = tk.Button(self.root, width=32)
        self.connect_button.config(
            text='Connect', command=self.cmd_connect)
        self.connect_button.grid(column=0, row=0, columnspan=2, sticky=tk.NSEW)
        self.host_label, self.host_entry = self.labelled_entry(
            'Host:', 'localhost', 0, 1
        )
        self.port_label, self.port_entry = self.labelled_entry(
             'Port:', '6379', 0, 2
        )
        self.password_label, self.password_entry = self.labelled_entry(
            'Password:', None, 0, 3
        )
        self.password_entry['show'] = '*'
        self.password_entry.focus_set()
        self.password_entry.bind("<Return>", self.cmd_connect)

        self.database_label = tk.Label(self.root, text='Database:')
        self.database_label.grid(column=0, row=4, sticky=tk.E)
        self.database_label.grid_remove()

        self.grid_weights(self.root, 1, 0)

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
            self.database_list = tk.OptionMenu(self.root,
                                               self.database, *databases)
            self.database_list.grid(column=1, row=4, sticky=tk.NSEW)
            self.database_label.grid()
            self.connect_button.config(text='Disconnect',
                                       command=self.cmd_disconnect)
            for w in [self.host_label, self.host_entry, self.port_label,
                      self.port_entry, self.password_label,
                      self.password_entry]:
                w.grid_remove()
        except Exception,e:
            self.show_error(e)
            self.cmd_disconnect()

    def cmd_disconnect(self):
        self.r = None
        self.connect_button.config(
            text='Connect', command=self.cmd_connect)
        for w in [self.host_label, self.host_entry, self.port_label,
                  self.port_entry, self.password_label, self.password_entry]:
            w.grid()
        if self.explorer:
            self.explorer.root.destroy()
            self.explorer = None
        if self.database_list:
            self.database_list.grid_remove()
        self.database_label.grid_remove()

    def cmd_change_db(self, var, two, mode):
        db = int(self.database.get()[2:])
        self.explorer.root.destroy()
        self.connect(db)

    def connect(self, db):
        host = self.host_entry.get()
        port = int(self.port_entry.get())
        self.r = redis.StrictRedis(
            host = host, 
            port = port, 
            db = db, 
            password = self.password_entry.get())
        self.r.client_setname('REDISExplorer')
        top_level = tk.Toplevel()
        self.explorer = RedisExplorer(
            top_level,
            'REDIS Explorer ' + host + ':' + str(port) + ' db' + str(db),
            self.r)


class RedisExplorer(GUIApplication.GUIApplication):
    def __init__(self, root, title, connection):
        super(RedisExplorer, self).__init__(root, title)
        self.r = connection
        self.create_widgets(root)
        self.apply_style(root, 'white')
        self.cmd_list_keys()

    def create_widgets(self, root):
        self.key_list, self.key_list_scrolled = self.create_scrolled(
            self.root, tk.Listbox, True, True)
        self.key_list_scrolled.grid(column=0, row=1, sticky=tk.NSEW)
        self.key_list.bind('<<ListboxSelect>>', self.cmd_select_key)

        self.object_frame = tk.Frame(root, bg='lightgrey')
        self.object_frame.grid(column=1, row=0, rowspan=2, sticky=tk.NSEW)

        self.object_delete = tk.Button(self.object_frame, width=10)
        self.object_delete.config(text='Delete', command=self.cmd_delete)
        self.object_delete.grid(column=1, row=0, sticky=tk.E)
        self.object_set_as = tk.Button(self.object_frame, width=10)
        self.object_set_as.config(text='Set As ...', command=self.cmd_set_as)
        self.object_set_as.grid(column=2, row=0, sticky=tk.E)
        self.object_set = tk.Button(self.object_frame, width=10)
        self.object_set.config(text='Set', command=self.cmd_set)
        self.object_set.grid(column=3, row=0, sticky=tk.E)

        self.key_label = tk.Label(self.object_frame, text='Key:',
            foreground='blue', height=2, anchor=tk.S)
        self.key_label.grid(column=0, row=1, sticky=tk.S + tk.W)
        self.key_entry = tk.Entry(self.object_frame)
        self.key_entry.grid(column=1, row=1, columnspan=4, sticky=tk.S + tk.EW)
        self.key_entry.config(state=tk.DISABLED)
        self.key_entry.bind("<Return>", self.cmd_set_as_phase_2)
        self.key_entry.bind("<FocusOut>", self.cmd_set_as_finally)
        self.key_entry.bind("<Button-1>", self.cmd_set_as)
        self.object_view, self.object_view_scrolled = self.create_scrolled(
            self.object_frame, tk.Text, True, True)

        self.object_view_scrolled.grid(
            column=0, row=2, columnspan=5, sticky=tk.NSEW)
        self.grid_weights(self.object_frame, [0, 1, 0, 0, 0, 0], [0, 0, 1])

        self.grid_weights(root, [0, 1], [0, 1])

    def cmd_list_keys(self):
        self.key_list.delete(0, self.key_list.size())
        self.key_list.insert(0, *(sorted(self.r.keys())))

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
        value = self.object_view.get(1.0, tk.END)[:-1]
        self.r.set(key, value)
        self.r.bgsave()

    def cmd_set_as(self, focusOutEvent=None):
        key = self.key_entry.get()
        self.old_key = key
        self.object_delete.config(state = tk.DISABLED)
        self.object_set.config(state = tk.DISABLED)
        self.key_entry.config(state = tk.NORMAL)
        self.object_set_as.config(text = 'YES, set as')
        self.object_set_as.config(command = self.cmd_set_as_phase_2)
        self.key_entry.focus_set()

    def cmd_set_as_phase_2(self):
        key = self.key_entry.get()
        value = self.object_view.get(1.0, tk.END)[:-1]
        self.r.set(key, value)
        self.r.bgsave()
        self.cmd_list_keys()
        self.old_key = key
        self.cmd_set_as_finally()

    def cmd_set_as_finally(self, focusOutEvent=None):
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

    def cmd_delete_finally(self, focusOutEvent=None):
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

    def key_index(self):
        selection = self.key_list.curselection()
        if len(selection) == 0:
            return -1
        index = int(selection[0])
        return index        


if __name__ == '__main__':
    GUIApplication.main(RedisConnect)
