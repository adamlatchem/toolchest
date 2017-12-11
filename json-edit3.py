#!/usr/bin/env python3
#
# Simple JSON editor that allows strings to be edited with embedded new lines.
# The use of python3 and Qt5 provides superior handling of unicode compare with
# python2 and Tk.
#
from PyQt5.QtWidgets import QAction, QMenu, qApp, QTreeWidget, QWidget, QLabel
from PyQt5.QtWidgets import QGridLayout, QPlainTextEdit, QLineEdit, QMessageBox
from PyQt5.QtWidgets import QInputDialog, QFileDialog, QTreeWidgetItem
from PyQt5.QtGui     import QStandardItemModel
import json
import os
import sys
import GUIApplication3
from   GUIApplication3 import Qt


class Model(object):
    def __init__(self):
        self.filename = "new.json"
        self.object = {}
        self.item_type = {}

    def load(self, sourcefile):
        if isinstance(sourcefile, str):
            sourcefile = open(sourcefile, 'r')
        self.filename = sourcefile.name
        json_text = sourcefile.read()
        sourcefile.close()
        self.loads(json_text)

    def loads(self, json_text):
        self.object = json.loads(json_text)
        self.item_type = {}

    def save(self, filename=None):
        if filename is None:
            filename = self.filename
        with open(filename, 'w') as file:
            json.dump(self.object, file, sort_keys=True, indent=4,
            separators=(',', ': '))
        self.filename = filename

    def get_item_type(self, item):
        key = repr(item)
        if item is None:
            key = repr('root')
        return self.item_type[key]

    def set_item_type(self, item, type):
        key = repr(item)
        self.item_type[key] = type

    def del_item_type(self, item):
        key = repr(item)
        del self.item_type[key]


class ViewModel(object):
    def __init__(self, view):
        self.filetypes = 'JSON files (*.json);;All files (*)'
        self.item = None
        self.view = view

        self.bind_menu(view.new_action, self.cmd_new)
        self.bind_menu(view.open_action, self.cmd_open)
        self.bind_menu(view.save_action, self.cmd_save)
        self.bind_menu(view.save_as_action, self.cmd_save_as)
        self.bind_menu(view.quit_action, view.cmd_quit)

        self.bind_menu(self.view.add_object_action, self.cmd_add_object)
        self.bind_menu(self.view.rename_action, self.cmd_rename)
        self.bind_menu(self.view.add_array_action, self.cmd_add_array)
        self.bind_menu(self.view.move_up_action, self.cmd_move_up)
        self.bind_menu(self.view.move_down_action, self.cmd_move_down)
        self.bind_menu(self.view.add_string_action, self.cmd_add_string)
        self.bind_menu(self.view.add_boolean_action, self.cmd_add_boolean)
        self.bind_menu(self.view.add_number_action, self.cmd_add_number)
        self.bind_menu(self.view.add_null_action, self.cmd_add_null)
        self.bind_menu(self.view.delete_action, self.cmd_delete)

        self.view.treeview.clicked.connect(self.on_treeview_select)
        self.view.treeview.setContextMenuPolicy(Qt.CustomContextMenu)
        self.view.treeview.customContextMenuRequested.connect(self.on_show_menu)
        self.view.item_text.textChanged.connect(self.on_item_keyup)

        if len(sys.argv) > 1:
            self.model = Model()
            self.model.load(sys.argv[1])
            self.new_tree()
        else:
            self.cmd_new()

    def cmd_add_object(self):
        self.new_node(dict, 'object { ... }')

    def cmd_rename(self):
        name = QInputDialog.getText(self.view.main, 'Rename', 'Name:')
        if not name[1]:
            return
        selected = self.selected()
        selected.setData(0, 0, name[0])
        self.edit(selected)
        self.view.cmd_dirty()

    def cmd_add_array(self):
        self.new_node(list, 'array [ ... ]')

    def cmd_move_up(self):
        self.move_selected(-1)

    def cmd_move_down(self):
        self.move_selected(1)

    def cmd_add_string(self):
        self.new_node(str, 'text')

    def cmd_add_boolean(self):
        self.new_node(bool, 'true')

    def cmd_add_number(self):
        self.new_node(float, '0.0')

    def cmd_add_null(self):
        self.new_node(None, 'null')

    def cmd_delete(self):
        selected = self.selected()
        parent = selected.parent()
        if parent is None:
            return
        self.model.del_item_type(selected)
        parent.removeChild(selected)
        parent_type = self.model.get_item_type(parent)
        if parent_type == 'key':
            self.model.del_item_type(parent)
            parent.parent().removeChild(parent)
        self.view.treeview.setCurrentItem(None)
        self.set_parent_name('')
        self.item = None
        self.view.item_text.setPlainText('')
        self.view.cmd_dirty()

    def cmd_new(self):
        self.model = Model()
        self.view.cmd_dirty()
        self.new_tree()

    def cmd_open(self):
        file = QFileDialog.getOpenFileName(
            None,
            'Open JSON File',
            '.',
            self.filetypes)
        if file:
            self.model = Model()
            file = open(file[0], 'r')
            self.model.load(file)
            self.view.cmd_clean()
            self.new_tree()

    def cmd_save(self):
        self.model.loads(self.tree_to_json())
        self.model.save()
        self.view.cmd_clean()
        self.update_title()

    def cmd_save_as(self):
        filename = QFileDialog.getSaveFileName(
            self.view.main,
            'Save JSON As',
            '.',
            self.filetypes)
        if filename:
            self.model.loads(self.tree_to_json())
            self.model.save(filename[0])
            self.view.cmd_clean()
            self.update_title()

    def on_item_keyup(self):
        if self.item != None:
            text = self.view.item_text.toPlainText()
            old_text = self.item.data(0, 0)
            if text == old_text:
                return
            type = self.model.get_item_type(self.item)
            if type == bool:
                text = text.lower()
            elif type in (int, float):
                try:
                    type(text)
                except:
                    text = '0'
            text = type(text)
            self.item.setData(0, 0, text)
            self.view.cmd_dirty()

    def on_treeview_select(self, event):
        selected = self.selected()
        if selected:
            self.edit(selected)

    def on_show_menu(self, position):
        item = self.event_to_item(position)
        if item is None:
            return
        self.menu_for_item(position, item)

    def on_hide_menu(self, event):
        self.view.context_menu.unpost()

    def bind_menu(self, action, command):
        action.triggered.connect(command)

    def object_to_tree(self, obj, parent_node):
        if parent_node == 'root':
            self.view.treeview.clear()
            self.model.set_item_type('root', 'root')
            parent_node = self.view.treeview.invisibleRootItem()

        if isinstance(obj, dict):
            node = QTreeWidgetItem(['object { ... }'])
            parent_node.addChild(node)
            for key in sorted(obj):
                key_node = self.object_to_tree(key, node)
                self.model.set_item_type(key_node, 'key')
                self.object_to_tree(obj[key], key_node)
        elif isinstance(obj, list):
            node = QTreeWidgetItem(['array [ ... ]'])
            parent_node.addChild(node)
            for item in obj:
                self.object_to_tree(item, node)
        else:
            if obj is None:
                text = 'null'
            else:
                text = str(obj)
            node = QTreeWidgetItem([text])
            parent_node.addChild(node)

        self.model.set_item_type(node, type(obj))
        if obj is None:
            self.model.set_item_type(node, 'null')
        return node

    def tree_to_json(self, node='root'):
        type = self.model.get_item_type(node)
        tree = self.view.treeview
        if type == 'root':
            return self.tree_to_json(tree.invisibleRootItem().child(0))
        elif type == dict:
            inner = ''
            for i in range(node.childCount()):
                key = node.child(i)
                if len(inner):
                    inner += ', '
                value = self.tree_to_json(key.child(0))
                inner += '"' + key.data(0, 0) + '": ' + value
            return '{' + inner + '}'
        elif type == list:
            inner = ''
            for i in range(node.childCount()):
                item = node.child(i)
                if len(inner):
                    inner += ', '
                inner += self.tree_to_json(item)
            return '[' + inner + ']'
        elif type in (int, float):
            return node.data(0, 0)
        elif type == str:
            string = node.data(0, 0)
            string = string.replace('\\', '\\\\')
            string = string.replace('"', '\\"')
            string = string.replace('\n', '\\n')
            string = string.replace('\t', '\\t')
            return '"' + string + '"'
        elif type == bool:
            return node.data(0, 0).lower()
        elif type == 'null':
            return 'null'
        else:
            raise Exception('unknown type ' + str(type))

    def new_tree(self):
        self.object_to_tree(self.model.object, 'root')
        self.item = None
        self.set_parent_name('')
        self.view.item_text.setPlainText('')
        self.update_title()

    def new_node(self, type, text):
        parent_node = self.selected()
        if self.model.get_item_type(parent_node) == dict:
            key_name = QInputDialog.getText(self.view.main, 'Key name', 'Name:')
            if not key_name[1]:
                return
            node = QTreeWidgetItem([key_name[0]])
            parent_node = parent_node.addChild(node)
            parent_node = node
            self.model.set_item_type(parent_node, 'key')
        node = QTreeWidgetItem([text])
        parent_node.addChild(node)
        if type is None:
            type = 'null'
        self.model.set_item_type(node, type)
        self.view.treeview.setCurrentItem(node)
        self.view.cmd_dirty()
        return node

    def edit(self, item):
        type = self.model.get_item_type(item)
        if type == 'key':
            self.edit(item.child(0))
        elif type not in (dict, list, 'null'):
            parent = item.parent()
            parent_text = parent.data(0, 0)
            text = item.data(0, 0)

            self.set_parent_name(parent_text)

            # Due to order of textChanged signal set this now
            self.item = item
            self.view.item_text.setPlainText(text)

    def set_parent_name(self, text):
        self.view.parent_name.setText(text)

    def update_title(self):
        filename = self.model.filename[-50:]
        if filename != self.model.filename:
            filename = '... ' + filename
        self.view.title("JSONEdit " + filename)

    def menu_for_item(self, position, item):
        menu = self.view.context_menu
        actions = menu.actions()

        type = self.model.get_item_type(item)
        context_matrix = {
            'key'   : [0,1,0,0,0,0,0,0,0,2,1],
            dict    : [1,0,1,3,3,1,1,1,1,2,4],
            list    : [1,0,1,3,3,1,1,1,1,2,1],
            str     : [0,0,0,3,3,0,0,0,0,2,1],
            int     : [0,0,0,3,3,0,0,0,0,2,1],
            float   : [0,0,0,3,3,0,0,0,0,2,1],
            bool    : [0,0,0,3,3,0,0,0,0,2,1],
            'null'  : [0,0,0,3,3,0,0,0,0,2,1],
        }

        for i in range(len(actions)):
            state = context_matrix[type][i]
            if state == 0:
                actions[i].setEnabled(False)
            elif state == 1:
                actions[i].setEnabled(True)
            elif state == 3:
                parent = item.parent()
                parent_type = self.model.get_item_type(parent)
                if parent_type == list:
                    actions[i].setEnabled(True)
                else:
                    actions[i].setEnabled(False)
            elif state == 4:
                parent = item.parent()
                if parent is None:
                    actions[i].setEnabled(False)
                else:
                    actions[i].setEnabled(True)

        menu.exec_(self.view.treeview.viewport().mapToGlobal(position))

    def move_selected(self, offset):
        selected = self.selected()
        parent = selected.parent()
        index = parent.indexOfChild(selected)
        index = index + offset
        if index < 0 or index > parent.childCount() - 1:
            return
        parent.removeChild(selected)
        parent.insertChild(index, selected)
        self.view.cmd_dirty()

    def selected(self):
        selection = self.view.treeview.selectedItems()
        if len(selection) == 1:
            return selection[0]
        return None

    def event_to_item(self, position):
        return self.view.treeview.itemAt(position);


class JSONEdit(GUIApplication3.GUIApplication):
    def __init__(self):
        super().__init__('JSONEdit')
        self.create_widgets()
        self.viewmodel = ViewModel(self)

    def menu_action(self, menu, label):
        action = QAction(label, self.main)
        menu.addAction(action)
        return action

    def create_menu(self):
        self.menu = self.main.menuBar()

        self.menu_file = self.menu.addMenu('&File')
        self.new_action = self.menu_action(self.menu_file, 'New')
        self.open_action = self.menu_action(self.menu_file, 'Open ...')
        self.menu_file.addSeparator()
        self.save_action = self.menu_action(self.menu_file, 'Save')
        self.save_as_action = self.menu_action(self.menu_file, 'Save As ...')
        self.menu_file.addSeparator()
        self.quit_action = self.menu_action(self.menu_file, 'Close JSONEdit')
        self.quit_action.triggered.connect(qApp.quit)
        self.menu_file.addAction(self.quit_action)

    def create_context_menu(self):
        menu = QMenu(self.main)

        self.add_object_action = self.menu_action(menu, 'Add object')
        self.rename_action = self.menu_action(menu, 'Rename')
        self.add_array_action = self.menu_action(menu, 'Add array')
        self.move_up_action = self.menu_action(menu, 'Move up')
        self.move_down_action = self.menu_action(menu, 'Move down')
        self.add_string_action = self.menu_action(menu, 'Add string')
        self.add_boolean_action = self.menu_action(menu, 'Add boolean')
        self.add_number_action = self.menu_action(menu, 'Add number')
        self.add_null_action = self.menu_action(menu, 'Add null')
        menu.addSeparator()
        self.delete_action = self.menu_action(menu, 'Delete')

        self.context_menu = menu

    def create_widgets(self):
        self.create_menu()
        self.create_context_menu()

        self.treeview = QTreeWidget()
        self.treeview.setHeaderHidden(True)
        self.layout.addWidget(self.treeview, 0, 0)

        self.object_frame = QWidget()
        self.object_frame_layout = QGridLayout(self.object_frame)
        self.object_frame_layout.setContentsMargins(0, 0, 0, 0)
        self.object_frame.setLayout(self.object_frame_layout)
        self.layout.addWidget(self.object_frame, 0, 1)

        self.parent_label = QLabel('Key :')
        self.object_frame_layout.addWidget(self.parent_label, 0, 0)

        self.parent_name = QLineEdit(self.object_frame)
        self.parent_name.setReadOnly(True)
        self.object_frame_layout.addWidget(self.parent_name, 0, 1)

        self.item_text = QPlainTextEdit()
        self.object_frame_layout.addWidget(self.item_text, 1, 0, 1, 2)


if __name__ == '__main__':
    GUIApplication3.main(JSONEdit)
