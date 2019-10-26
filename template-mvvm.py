#!/usr/bin/env python
#
# Template for MVVM applications.
#
from __future__ import generators, unicode_literals
import json
import sys
import GUIApplication
try:
    import tkinter
    import tkinter.ttk as ttk
    import tkinter.filedialog as filedialog
    import tkinter.simpledialog as simpledialog
except:
    import Tkinter as tkinter
    import ttk
    import tkFileDialog as filedialog
    import tkSimpleDialog as simpledialog


class Model(object):
    def __init__(self):
        self.filename = "new.json"
        self.object = {}

    def load(self, sourcefile):
        if isinstance(sourcefile, str):
            sourcefile = open(sourcefile, 'r')
        self.filename = sourcefile.name
        json_text = sourcefile.read()
        sourcefile.close()
        self.loads(json_text)

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
        self.bind_menu(cm, 'Add', command=self.cmd_add)
        self.bind_menu(cm, 'Delete', command=self.cmd_delete)
        self.bind_menu(cm, 'Move up', command=self.cmd_move_up)
        self.bind_menu(cm, 'Move down', command=self.cmd_move_down)
        self.view.treeview.bind('<<TreeviewSelect>>', self.on_treeview_select)
        self.view.treeview.bind('<Button-2>', self.on_show_menu)
        self.view.treeview.bind('<Button-1>', self.on_hide_menu)
        self.view.item_text.bind_class('KeyUp', '<Key>', self.on_item_keyup)
        self.view.item_text.bind('<Button-1>', self.on_hide_menu)
        self.view.root.bind('<FocusOut>', self.on_hide_menu)

        if len(sys.argv) > 1:
            self.model = Model()
            self.model.load(sys.argv[1])
            self.new_tree()
        else:
            self.cmd_new()

    def cmd_add(self):
        self.new_node(dict, 'object { ... }')

    def cmd_move_up(self):
        self.move_selected(-1)

    def cmd_move_down(self):
        self.move_selected(1)

    def cmd_delete(self):
        selected = self.selected()
        parent = self.view.treeview.parent(selected)
        if parent == '':
            return
        del self.item_type[selected]
        self.view.treeview.delete(selected)
        parent_type = self.item_type[parent]
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

    def on_item_keyup(self, event):
        if not self.item is None:
            text = self.view.item_text.get(1.0, tkinter.END)[:-1]
            type = self.item_type[self.item]
            self.view.treeview.item(self.item, text=text)
            self.view.cmd_dirty()

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
        elif type in (str, str):
            string = tree.item(node)['text']
            string = string.replace('\\', '\\\\')
            string = string.replace('"', '\\"')
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
        self.view.item_text.delete(1.0, tkinter.END)
        self.update_title()

    def new_node(self, type, text):
        parent_node = self.selected()
        if self.item_type[parent_node] == dict:
            key_name = simpledialog.askstring('Key name', 'Name:')
            if key_name is None or len(key_name) == 0:
                return
            parent_node = self.view.treeview.insert(
                parent_node, 'end', text=key_name)
            self.item_type[parent_node] = 'key'
        node = self.view.treeview.insert(parent_node, 'end', text=text)
        self.item_type[node] = type
        self.view.treeview.selection_set(node)
        self.view.treeview.see(node)
        self.view.cmd_dirty()
        return node

    def edit(self, item):
        type = self.item_type[item]
        text = self.view.treeview.item(item, 'text')
        self.view.item_text.delete(1.0, tkinter.END)
        self.view.item_text.insert(1.0, text)
        self.item = item

    def update_title(self):
        filename = self.model.filename[-50:]
        if filename != self.model.filename:
            filename = '... ' + filename
        self.view.title("Template " + filename)

    def menu_for_item(self, item):
        type = self.item_type[item]
        context_matrix = {
            'root'  : [0,0,2,0,0],
            dict    : [1,0,2,0,0],
            'key'   : [0,1,2,1,1],
        }
        menu = self.view.context_menu
        for i in range(5):
            state = context_matrix[type][i]
            if state == 0:
                menu.entryconfigure(i, state=tkinter.DISABLED)
            elif state == 1:
                menu.entryconfigure(i, state=tkinter.NORMAL)
            elif state == 3:
                parent = self.view.treeview.parent(item) 
                parent_type = self.item_type[parent]
                if parent_type == list:
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


class Template(GUIApplication.GUIApplication):
    def __init__(self, root):
        super(Template, self).__init__(root, 'Template')
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

        self.root.config(menu=self.menu)
        self.menu.add_cascade(label='File', menu=self.menu_file)

    def create_context_menu(self):
        menu = tkinter.Menu(self.root, tearoff=False)
        menu.add_command(label='Add')
        menu.add_command(label='Delete')
        menu.add_separator()
        menu.add_command(label='Move up')
        menu.add_command(label='Move down')

        self.context_menu = menu

    def create_widgets(self):
        self.create_menu()
        self.create_context_menu()

        self.treeview, self.treeview_scrolled = self.create_scrolled(
            self.root, ttk.Treeview, True, True)
        self.treeview_scrolled.grid(column=0, row=0, sticky=tkinter.NSEW)

        self.object_frame = tkinter.Frame(self.root, bg='lightgrey')
        self.object_frame.grid()
        self.object_frame.grid(column=1, row=0, sticky=tkinter.NSEW)

        self.item_text, self.item_text_scrolled = self.create_scrolled(
            self.object_frame, tkinter.Text, True, True)
        self.extend_bindtags(self.item_text)

        self.item_text_scrolled.grid(
            column=0, row=0, columnspan=2, sticky=tkinter.NSEW)

        self.grid_weights(self.object_frame, [1], [1])

        self.grid_weights(self.root, [0, 1], [1])


if __name__ == '__main__':
    GUIApplication.main(Template)
