#!/usr/bin/env python
#
# Simple JSON editor that allows strings to be edited
# with embedded new lines
#
import ttk
import tkFileDialog
import tkSimpleDialog
import json
import os
import GUIApplication
from   GUIApplication import tk


class Model(object):
    def __init__(self):
        self.filename = "new.json"
        self.object = {}

    def load(self, file):
        if file:
            self.filename = file.name
            json_text = file.read()
            self.object = json.loads(json_text)
        else:
            self.object = {}

    def save(self, filename=None):
        if filename is None:
            filename = self.filename
        with open(filename, 'w') as file:
            json.dump(self.object, file)
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
        self.view.treeview.bind('<Button-3>', self.on_show_menu)
        self.view.treeview.bind('<Button-1>', self.on_hide_menu)
        self.view.parent_label.bind('<Button-1>', self.on_hide_menu)
        self.view.parent_name.bind('<Button-1>', self.on_hide_menu)
        self.view.item_text.bind_class('KeyUp', '<Key>', self.on_item_keyup)
        self.view.item_text.bind('<Button-1>', self.on_hide_menu)
        self.view.root.bind('<FocusOut>', self.on_hide_menu)

        self.cmd_new()

    def cmd_add_object(self):
        self.new_node(dict, 'object { ... }')

    def cmd_rename(self):
        name = tkSimpleDialog.askstring('Rename', 'Name:')
        if name is None or len(name) == 0:
            return
        selected = self.selected()
        self.view.treeview.item(selected, text=name)
        self.view.cmd_dirty()

    def cmd_add_array(self):
        self.new_node(list, 'array [ ... ]')

    def cmd_move_up(self):
        self.move_selected(-1)

    def cmd_move_down(self):
        self.move_selected(1)

    def cmd_add_string(self):
        self.new_node(str, '')

    def cmd_add_boolean(self):
        self.new_node(bool, 'False')

    def cmd_add_number(self):
        self.new_node(float, '0.0')

    def cmd_add_null(self):
        self.new_node(None, 'null')

    def cmd_delete(self):
        selected = self.selected()
        parent = self.view.treeview.parent(selected)
        del self.item_type[selected]
        self.view.treeview.delete(selected)
        parent_type = self.item_type[parent]
        if parent_type == 'key':
            del self.item_type[parent]
            self.view.treeview.delete(parent)
        self.view.cmd_dirty()

    def cmd_new(self):
        self.model = Model()
        self.view.cmd_dirty()
        self.new_tree()

    def cmd_open(self):
        file = tkFileDialog.askopenfile(
            filetypes=self.filetypes,
            title='Open JSON File',
            parent=self.view.root)
        if file:
            self.model = Model()
            self.model.load(file)
            file.close()
            self.view.cmd_clean()
            self.new_tree()

    def cmd_save(self):
        self.model.object = json.loads(self.tree_to_json())
        self.model.save()
        self.view.cmd_clean()
        self.update_title()

    def cmd_save_as(self):
        filename = tkFileDialog.asksaveasfilename(
            filetypes=self.filetypes,
            title='Save JSON As',
            parent=self.view.root)
        if filename:
            self.model.object = json.loads(self.tree_to_json())
            self.model.save(filename)
            self.view.cmd_clean()
            self.update_title()

    def on_item_keyup(self, event):
        if self.item <> None:
            text = self.view.item_text.get(1.0, tk.END)
            text = text[:-1]
            self.view.treeview.item(self.item, text=text)
            self.view.cmd_dirty()

    def on_treeview_select(self, event):
        selected = self.selected()
        if selected:
            self.edit(selected)

    def on_show_menu(self, event):
        menu = self.view.context_menu
        menu.post(event.x_root, event.y_root)
        item = self.event_to_item(event)
        self.menu_for_item(item)
        self.view.treeview.selection('set', item)

    def on_hide_menu(self, event):
        self.view.context_menu.unpost()

    def bind_menu(self, menu, entry, **kwargs):
        index = menu.index(entry)
        menu.entryconfig(index, **kwargs)

    def object_to_tree(self, obj, parent_node=''):
        if parent_node == '':
            self.view.treeview.delete(*self.view.treeview.get_children())
            self.item_type = {'':'root'}

        if isinstance(obj, dict):
            node = self.view.treeview.insert(
                parent_node, 'end', text='object { ... }')
            for key in sorted(obj):
                key_node = self.object_to_tree(key, node)
                self.item_type[key_node] = 'key'
                self.object_to_tree(obj[key], key_node)
        elif isinstance(obj, list):
            node = self.view.treeview.insert(
                parent_node, 'end', text='array [ ... ]')
            for item in obj:
                self.object_to_tree(item, node)
        else:
            if obj is None:
                text = 'null'
            else:
                text = str(obj)
            node = self.view.treeview.insert(parent_node, 'end', text=text)

        self.item_type[node] = type(obj)
        if obj is None:
            self.item_type[node] = 'null'
        return node

    def tree_to_json(self, node=''):
        type = self.item_type[node]
        tree = self.view.treeview
        if type == 'root':
            return self.tree_to_json(tree.get_children()[0])
        elif type == dict:
            inner = ''
            for key in tree.get_children(node):
                if len(inner):
                    inner += ', '
                value = self.tree_to_json(tree.get_children(key)[0])
                inner += '"' + tree.item(key)['text'] + '": ' + value
            return '{' + inner + '}'
        elif type == list:
            inner = ''
            for item in tree.get_children(node):
                if len(inner):
                    inner += ', '
                inner += self.tree_to_json(item)
            return '[' + inner + ']'
        elif type in (int, float):
            return tree.item(node)['text']
        elif type in (unicode, str):
            string = tree.item(node)['text']
            string = string.replace('\\', '\\\\')
            string = string.replace('\n', '\\n')
            string = string.replace('\t', '\\t')
            return '"' + string + '"'
        elif type == bool:
            return tree.item(node)['text'].lower()
        elif type == 'null':
            return 'null'
        else:
            raise Exception('unknown type ' + str(type))

    def new_tree(self):
        self.object_to_tree(self.model.object)
        self.item = None
        self.set_parent_name('')
        self.view.item_text.delete(1.0, tk.END)
        self.update_title()

    def new_node(self, type, text):
        parent_node = self.selected()
        if self.item_type[parent_node] == dict:
            key_name = tkSimpleDialog.askstring('Key name', 'Name:')
            if key_name is None or len(key_name) == 0:
                return
            parent_node = self.view.treeview.insert(
                parent_node, 'end', text=key_name)
            self.item_type[parent_node] = 'key'
        node = self.view.treeview.insert(parent_node, 'end', text=text)
        if type is None:
            type = 'null'
        self.item_type[node] = type
        self.view.treeview.selection('set', node)
        self.view.treeview.see(node)
        self.view.cmd_dirty()
        return node

    def edit(self, item):
        if self.item_type[item] not in ('key', dict, list):
            parent = self.view.treeview.parent(item)
            parent_text = self.view.treeview.item(parent, 'text')
            text = self.view.treeview.item(item, 'text')

            self.set_parent_name(parent_text)
            self.view.item_text.delete(1.0, tk.END)
            self.view.item_text.insert(1.0, text)

            self.item = item

    def set_parent_name(self, text):
        self.view.parent_name.configure(state=tk.NORMAL)
        self.view.parent_name.delete(0, tk.END)
        self.view.parent_name.insert(0, text)
        self.view.parent_name.configure(state=tk.DISABLED)

    def update_title(self):
        self.view.title("JSONEdit " + self.model.filename)

    def menu_for_item(self, item):
        type = self.item_type[item]
        menu_state = {
            'root'  : [0,0,0,0,0,0,0,0,0,2,0],
            'key'   : [0,1,0,0,0,0,0,0,0,2,1],
            dict    : [0,0,0,3,3,1,1,1,1,2,1],
            list    : [1,0,1,3,3,1,1,1,1,2,1],
            unicode : [0,0,0,3,3,0,0,0,0,2,1],
            int     : [0,0,0,3,3,0,0,0,0,2,1],
            float   : [0,0,0,3,3,0,0,0,0,2,1],
            bool    : [0,0,0,3,3,0,0,0,0,2,1],
            'null'  : [0,0,0,3,3,0,0,0,0,2,1],
        }
        menu = self.view.context_menu
        for i in xrange(11):
            state = menu_state[type][i]
            if state == 0:
                menu.entryconfigure(i, state=tk.DISABLED)
            elif state == 1:
                menu.entryconfigure(i, state=tk.NORMAL)
            elif state == 3:
                parent = self.view.treeview.parent(item) 
                parent_type = self.item_type[parent]
                if parent_type == list:
                    menu.entryconfigure(i, state=tk.NORMAL)
                else:
                    menu.entryconfigure(i, state=tk.DISABLED) 

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
        self.menu = tk.Menu(self.root)

        self.menu_file = tk.Menu(self.menu, tearoff=False)
        self.menu_file.add_command(label='New')
        self.menu_file.add_command(label='Open ...')
        self.menu_file.add_separator()
        self.menu_file.add_command(label='Save')
        self.menu_file.add_command(label='Save As ...')
        self.menu_file.add_separator()
        self.menu_file.add_command(label='Quit')

        self.root.config(menu=self.menu)
        self.menu.add_cascade(label='File', menu=self.menu_file)

    def create_context_menu(self):
        menu = tk.Menu(self.root, tearoff=False)
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

        self.treeview, self.treeview_scrolled = self.create_scrolled(
            self.root, ttk.Treeview, True, True)
        self.treeview_scrolled.grid(column=0, row=0, sticky=tk.NSEW)

        self.object_frame = tk.Frame(self.root, bg='lightgrey')
        self.object_frame.grid()
        self.object_frame.grid(column=1, row=0, sticky=tk.NSEW)

        self.parent_label = tk.Label(
            self.object_frame, text='Parent :', foreground='blue', anchor=tk.W)
        self.parent_label.grid(column=0, row=0)

        self.parent_name = tk.Entry(self.object_frame)
        self.parent_name.grid(column=1, row=0, sticky=tk.EW)
        self.parent_name.config(state=tk.DISABLED)

        self.item_text, self.item_text_scrolled = self.create_scrolled(
            self.object_frame, tk.Text, True, True)
        bindtags = list(self.item_text.bindtags())
        bindtags.insert(2, 'KeyUp')
        self.item_text.bindtags(tuple(bindtags))

        self.item_text_scrolled.grid(
            column=0, row=1, columnspan=2, sticky=tk.NSEW)

        self.grid_weights(self.object_frame, [0, 1], [0, 1])

        self.grid_weights(self.root, [0, 1], [1])


if __name__ == '__main__':
    GUIApplication.main(JSONEdit)
