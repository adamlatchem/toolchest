#!/usr/bin/env python
#
# Simple JSON editor that allows strings to be edited with embedded new lines
from __future__ import generators, unicode_literals, print_function
import sys
if sys.version_info[0] < 3:
    str = unicode
    import Tkinter as tkinter
    import ttk
    import tkSimpleDialog as simpledialog
    import tkFileDialog as filedialog
else:
    import tkinter
    import tkinter.ttk as ttk
    import tkinter.simpledialog as simpledialog
    import tkinter.filedialog as filedialog
import json
import os
import GUIApplication
import webbrowser


def augment(text, augmentation):
    if len(text):
        return text + ' : ' + augmentation
    return augmentation
    

class Model(object):
    def __init__(self):
        self.filename = "new.json"
        self.object = {}

    def load(self, sourcefile):
        if type(sourcefile) == str:
            sourcefile = open(sourcefile, 'r')
        self.filename = sourcefile.name
        json_text = sourcefile.read()
        sourcefile.close()
        self.loads(json_text)

    def loads(self, json_text):
        self.object = json.loads(json_text)

    def save(self, filename=None):
        if filename is None:
            filename = self.filename
        with open(filename, 'w') as file:
            json.dump(self.object, file, sort_keys=True, indent=4,
            separators=(',', ': '))
        self.filename = filename


class ViewModel(object):
    def __init__(self, view):
        self.filetypes = (('JSON files', '*.json'),
                           ('All files', '*.*'))
        self.item = None
        self.view = view

        cm = self.view.context_menu

        self.bind_menu(view.menu_file, 'New', command=self.cmd_new)
        self.bind_menu(view.menu_file, 'Open ...', command=self.cmd_open)
        self.bind_menu(view.menu_file, 'Save', command=self.cmd_save)
        self.bind_menu(view.menu_file, 'Save As ...', command=self.cmd_save_as)
        self.bind_menu(view.menu_file, 'Quit', command=view.cmd_quit)
        self.bind_menu(view.menu_help, 'Documentation', command=self.cmd_documentation)
        self.bind_menu(cm, 'Add object', command=self.cmd_add_object)
        self.bind_menu(cm, 'Rename', command=self.cmd_rename)
        self.bind_menu(cm, 'Add array', command=self.cmd_add_array)
        self.bind_menu(cm, 'Move up', command=self.cmd_move_up)
        self.bind_menu(cm, 'Move down', command=self.cmd_move_down)
        self.bind_menu(cm, 'Add string', command=self.cmd_add_string)
        self.bind_menu(cm, 'Add boolean', command=self.cmd_add_boolean)
        self.bind_menu(cm, 'Add number', command=self.cmd_add_number)
        self.bind_menu(cm, 'Add null', command=self.cmd_add_null)
        self.bind_menu(cm, 'Delete', command=self.cmd_delete)
        self.view.treeview.bind('<<TreeviewSelect>>', self.on_treeview_select)
        self.view.treeview.bind('<Button-2>', self.on_show_menu)
        self.view.treeview.bind('<Button-3>', self.on_show_menu)
        self.view.treeview.bind('<Button-1>', self.on_treeview_button)
        self.view.parent_label.bind('<Button-1>', self.on_hide_menu)
        self.view.parent_name.bind('<Button-1>', self.on_hide_menu)
        self.view.item_text.bind_class('KeyUp', '<Key>', self.on_item_keyup)
        self.view.item_text.bind('<Button-1>', self.on_hide_menu)
        self.view.root.bind('<FocusOut>', self.on_hide_menu)

        if len(sys.argv) > 1:
            self.model = Model()
            self.model.load(str(sys.argv[1]))
            self.new_tree()
        else:
            self.cmd_new()

    def cmd_add_object(self):
        self.new_node({})

    def cmd_rename(self):
        name = simpledialog.askstring('Rename', 'Name:')
        if not name:
            return
        selected = self.selected()
        old_value = self.view.treeview.item(selected, 'values')
        new_text = name + self.view.treeview.item(selected, 'text')[len(old_value[0]):]
        self.view.treeview.item(selected, text=new_text, values=(name, old_value[1]))
        self.view.cmd_dirty()

    def cmd_add_array(self):
        self.new_node([])

    def cmd_move_up(self):
        self.move_selected(-1)

    def cmd_move_down(self):
        self.move_selected(1)

    def cmd_add_string(self):
        self.new_node('')

    def cmd_add_boolean(self):
        self.new_node(True)

    def cmd_add_number(self):
        self.new_node(0.0)

    def cmd_add_null(self):
        self.new_node(None)

    def cmd_delete(self):
        selected = self.selected()
        parent = self.view.treeview.parent(selected)
        if parent == '':
            return
        del self.item_type[selected]
        self.view.treeview.delete(selected)
        self.view.cmd_dirty()

    def cmd_new(self):
        self.model = Model()
        self.view.cmd_dirty()
        self.new_tree()

    def cmd_open(self):
        file = filedialog.askopenfile(
            filetypes=self.filetypes,
            title='Open JSON File',
            parent=self.view.root)
        if file:
            self.model = Model()
            self.model.load(file)
            self.view.cmd_clean()
            self.new_tree()

    def cmd_save(self):
        self.model.loads(self.tree_to_json())
        self.model.save()
        self.view.cmd_clean()
        self.update_title()

    def cmd_save_as(self):
        filename = filedialog.asksaveasfilename(
            filetypes=self.filetypes,
            title='Save JSON As',
            parent=self.view.root)
        if filename:
            self.model.loads(self.tree_to_json())
            self.model.save(filename)
            self.view.cmd_clean()
            self.update_title()

    def cmd_documentation(self):
        webbrowser.open_new('https://www.intrepiduniverse.com/projects/jsonEditor.html')

    def on_item_keyup(self, event):
        if not self.item is None:
            text = self.view.item_text.get(1.0, tkinter.END)[:-1]
            type = self.item_type[self.item]
            if type == bool:
                cast = lambda x : x.lower().strip() in ['true', '1', 't', 'y', 'yes']
            elif type in (int, float):
                def to_number(text):
                    try:
                        return type(text)
                    except ValueError:
                        return 0
                cast = to_number
            else:
                cast = lambda x : str(x)
            value = str(cast(text))
            values = self.view.treeview.item(self.item, 'values')
            self.view.treeview.item(self.item, text=augment(values[0], value), values=(values[0], value))
            self.view.cmd_dirty()

    def on_treeview_button(self, event):
        self.on_hide_menu(event)
        if self.view.treeview.identify_region(event.x, event.y) == "separator":
            return "break"

    def on_treeview_select(self, event):
        selected = self.selected()
        if selected:
            self.edit(selected)

    def on_show_menu(self, event):
        if self.view.root.focus_get() is None:
            return
        item = self.event_to_item(event)
        self.menu_for_item(item)
        self.view.treeview.selection_set(item)
        self.view.context_menu.post(event.x_root, event.y_root)

    def on_hide_menu(self, event):
        self.view.context_menu.unpost()

    def bind_menu(self, menu, entry, **kwargs):
        index = menu.index(entry)
        menu.entryconfig(index, **kwargs)

    def object_to_tree(self, obj, container_id='', key_id=None):
        if container_id == '':
            self.view.treeview.delete(*self.view.treeview.get_children())
            key_id = self.view.treeview.insert(container_id, 'end', text='root')
            self.item_type = {'': 'root', key_id: dict}

        key_item = self.view.treeview.item(key_id)
        key_text = key_item['text']
        if isinstance(obj, dict):
            self.view.treeview.item(key_id, text=augment(key_text, '{ ... }'), values=(key_text, dict))
            self.item_type[key_id] = dict
            for key in sorted(obj):
                inner_key_id = self.view.treeview.insert(key_id, 'end', text=key)
                self.object_to_tree(obj[key], key_item, inner_key_id)
        elif isinstance(obj, list):
            self.view.treeview.item(key_id, text=augment(key_text, '[ ,,, ]'), values=(key_text, list))
            self.item_type[key_id] = list
            for item in obj:
                inner_key_id = self.view.treeview.insert(key_id, 'end', text='')
                self.object_to_tree(item, key_item, inner_key_id)
        else:
            if obj is None:
                value_text = '<null>'
            elif type(obj) in (bool, int, float):
                value_text = str(obj)
            else:
                obj = str(obj)
                value_text = str(obj)
            self.view.treeview.item(key_id, text=augment(key_text, value_text), values=(key_text, value_text))
            self.item_type[key_id] = type(obj)
            if obj is None:
                self.item_type[key_id] = 'null'

    def tree_to_json(self, node_id=''):
        if not node_id:
            node_id = self.view.treeview.get_children()[0] 
        type = self.item_type[node_id]
        tree = self.view.treeview
        if type == dict:
            inner = ''
            for key_id in tree.get_children(node_id):
                if inner:
                    inner += ', '
                value = str(self.tree_to_json(key_id))
                inner += '"' + str(tree.item(key_id)['values'][0]) + '": ' + value
            return '{' + inner + '}'
        elif type == list:
            inner = ''
            for key_id in tree.get_children(node_id):
                if inner:
                    inner += ', '
                inner += str(self.tree_to_json(key_id))
            return '[' + inner + ']'
        elif type in (int, float):
            return tree.item(node_id)['values'][1]
        elif type == bool:
            return tree.item(node_id)['values'][1].lower()
        elif type == 'null':
            return 'null'
        else:
            string = str(tree.item(node_id)['values'][1])
            string = string.replace('\\', '\\\\')
            string = string.replace('"', '\\"')
            string = string.replace('\n', '\\n')
            string = string.replace('\t', '\\t')
            return '"' + string + '"'

    def new_tree(self):
        self.object_to_tree(self.model.object)
        self.item = None
        self.set_parent_name('')
        self.view.item_text.delete(1.0, tkinter.END)
        self.update_title()

    def new_node(self, value):
        container_id = self.selected()
        if self.item_type[container_id] == dict:
            key = str(simpledialog.askstring('Key name', 'Name:'))
            if not key:
                return
            for child_id in self.view.treeview.get_children(container_id):
                if key == self.view.treeview.item(child_id, 'values')[0]:
                    raise Exception('Key already exists : ' + key)
            key_id = self.view.treeview.insert(container_id, 'end', text=key)
            self.object_to_tree(value, container_id, key_id)
        elif self.item_type[container_id] == list:
            key_id = self.view.treeview.insert(container_id, 'end', text='')
            self.object_to_tree(value, container_id, key_id)
        self.view.treeview.selection_set(key_id)
        self.view.treeview.see(key_id)
        self.view.cmd_dirty()

    def edit(self, item_id):
        type = self.item_type[item_id]
        if type not in (dict, list, 'null'):
            values = self.view.treeview.item(item_id, 'values')
            value_text = self.view.treeview.item(item_id, 'text').replace(values[0] + ' : ', '')

            self.set_parent_name(str(type) + ' ' + values[0])
            self.view.item_text.delete(1.0, tkinter.END)
            self.view.item_text.insert(1.0, value_text)

            self.item = item_id

    def set_parent_name(self, text):
        self.view.parent_name.configure(state=tkinter.NORMAL)
        self.view.parent_name.delete(0, tkinter.END)
        self.view.parent_name.insert(0, text)
        self.view.parent_name.configure(state=tkinter.DISABLED)

    def update_title(self):
        filename = self.model.filename[-50:]
        if filename != self.model.filename:
            filename = '... ' + filename
        self.view.title("JSONEdit " + filename)

    def menu_for_item(self, item_id):
        type = self.item_type[item_id]
        context_matrix = {
            'root'  : [0,0,0,0,0,0,0,0,0,2,0],
            dict    : [1,4,1,3,3,1,1,1,1,2,1],
            list    : [1,4,1,3,3,1,1,1,1,2,1],
            str     : [0,4,0,3,3,0,0,0,0,2,1],
            int     : [0,4,0,3,3,0,0,0,0,2,1],
            float   : [0,4,0,3,3,0,0,0,0,2,1],
            bool    : [0,4,0,3,3,0,0,0,0,2,1],
            'null'  : [0,4,0,3,3,0,0,0,0,2,1],
        }
        menu = self.view.context_menu
        for i in range(len(context_matrix[type])):
            state = context_matrix[type][i]
            parent = self.view.treeview.parent(item_id)
            parent_type = self.item_type[parent]
            if state == 0:
                menu.entryconfigure(i, state=tkinter.DISABLED)
            elif state == 1:
                menu.entryconfigure(i, state=tkinter.NORMAL)
            elif state == 3:
                if parent_type == list:
                    menu.entryconfigure(i, state=tkinter.NORMAL)
                else:
                    menu.entryconfigure(i, state=tkinter.DISABLED) 
            elif state == 4:
                if parent_type == dict:
                    menu.entryconfigure(i, state=tkinter.NORMAL)
                else:
                    menu.entryconfigure(i, state=tkinter.DISABLED) 

    def move_selected(self, offset):
        selected = self.selected()
        parent = self.view.treeview.parent(selected)
        index = self.view.treeview.index(selected)
        index = index + offset
        self.view.treeview.move(selected, parent, index)
        self.view.cmd_dirty()

    def selected(self):
        selection = self.view.treeview.selection()
        if len(selection) == 1:
            return selection[0]
        return None

    def event_to_item(self, event):
        return self.view.treeview.identify('item', event.x, event.y)


class JSONEdit(GUIApplication.GUIApplication):
    def __init__(self, root):
        super(JSONEdit, self).__init__(root, 'JSONEdit')
        self.create_widgets()
        self.apply_style(root, 'white')
        self.viewmodel = ViewModel(self)

    def create_menu(self):
        self.menu = tkinter.Menu(self.root)

        self.menu_file = tkinter.Menu(self.menu, tearoff=False)
        self.menu_file.add_command(label='New')
        self.menu_file.add_command(label='Open ...')
        self.menu_file.add_separator()
        self.menu_file.add_command(label='Save')
        self.menu_file.add_command(label='Save As ...')
        self.menu_file.add_separator()
        self.menu_file.add_command(label='Quit')

        self.menu_help = tkinter.Menu(self.menu, tearoff=False)
        self.menu_help.add_command(label='Version 1.0.0', state=tkinter.DISABLED)
        self.menu_help.add_command(label='Documentation')

        self.root.config(menu=self.menu)
        self.menu.add_cascade(label='File', menu=self.menu_file)
        self.menu.add_cascade(label='Help', menu=self.menu_help)

    def create_context_menu(self):
        menu = tkinter.Menu(self.root, tearoff=False)
        menu.add_command(label='Add object')
        menu.add_command(label='Rename')
        menu.add_command(label='Add array')
        menu.add_command(label='Move up')
        menu.add_command(label='Move down')
        menu.add_command(label='Add string')
        menu.add_command(label='Add boolean')
        menu.add_command(label='Add number')
        menu.add_command(label='Add null')
        menu.add_separator()
        menu.add_command(label='Delete')

        self.context_menu = menu

    def create_widgets(self):
        self.create_menu()
        self.create_context_menu()

        self.pane = tkinter.PanedWindow(self.root, orient=tkinter.HORIZONTAL, sashwidth=4, showhandle=True)
        self.pane.pack(fill=tkinter.BOTH, expand=True)

        self.treeview, self.treeview_scrolled = self.create_scrolled(
            self.root, ttk.Treeview, True, True)
        self.pane.add(self.treeview_scrolled)
        self.treeview.heading('#0', text='Document Tree')

        self.object_frame = tkinter.Frame(self.pane, bg='lightgrey')
        self.object_frame.grid()
        self.pane.add(self.object_frame)

        self.parent_label = tkinter.Label(
            self.object_frame, text='Key :', foreground='blue', anchor=tkinter.W)
        self.parent_label.grid(column=0, row=0)

        self.parent_name = tkinter.Entry(self.object_frame)
        self.parent_name.grid(column=1, row=0, sticky=tkinter.EW)
        self.parent_name.config(state=tkinter.DISABLED)

        self.item_text, self.item_text_scrolled = self.create_scrolled(
            self.object_frame, tkinter.Text, True, True)
        self.extend_bindtags(self.item_text)

        self.item_text_scrolled.grid(
            column=0, row=1, columnspan=2, sticky=tkinter.NSEW)

        self.grid_weights(self.object_frame, [0, 1], [0, 1])

        self.grid_weights(self.root, [0, 1], [1])


if __name__ == '__main__':
    GUIApplication.main(JSONEdit)
