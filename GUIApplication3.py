#!/usr/bin/env python3
#
# Base class for a GUI Application using PyQt5
#
from PyQt5.QtWidgets import QApplication, QMessageBox, QWidget, QGridLayout
from PyQt5.QtWidgets import QLabel, QPlainTextEdit, QMainWindow, QScrollArea
from PyQt5.QtCore    import Qt
import traceback
import sys


class GUIApplication(object):
    def __init__(self, title):
        self.app = QApplication(sys.argv)
        self.main = QMainWindow()
        self.central = QWidget()
        self.main.setCentralWidget(self.central)
        self._is_dirty = False
        self.title(title)
        self.layout = QGridLayout(self.central)
        self.main.resize(640, 480)
        self.main.show()

        self.old_hook = sys.excepthook
        sys.excepthook = self.exception_handler

    def exception_handler(self, exctype, exception, traceback):
        print(traceback)
        if self.old_hook:
            self.old_hook(exctype, exception, traceback)
        QMessageBox.warning(self.main, 'Error', repr(exception))

    def title(self, title):
        self._title = title
        if self._is_dirty:
            title = title + '*'
        self.main.setWindowTitle(title)

    def create_scrolled(self, cls, vertical, horizontal):
        outer = QScrollArea()

        if vertical:
            outer.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        else:
            outer.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        if horizontal:
            outer.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        else:
            outer.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        inner = cls(outer)
        outer.setWidget(inner)
        outer.setWidgetResizable(True)

        return inner, outer

    def labelled_entry(self, text, value, column, row):
        host_label = QLabel(text, self.central)
        self.layout.addWidget(host_label, row, column)
        host_entry = QPlainTextEdit(self.central)
        if value:
            host_entry.setPlainText(value)
        self.layout.addWidget(host_entry, row, column+1)
        return (host_label, host_entry)

    def show_error(self, exception):
        type, exception, traceback = sys.exc_info()
        exception_handler(type, exception, traceback)

    def on_not_implemented(self, event=None):
        QMessageBox.warning(self.main, 'Error', 'Not implemented.')

    def cmd_quit(self, force=False):
        if self._is_dirty:
            result = QMessageBox.question(
                self.main,
                'Confirm Quit',
                'There are unsaved changes. Quit without saving?')
            if result != QMessageBox.Yes:
                return
        if force:
            QApplication.quit()
        else:
            QApplication.quit()

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
    app = application_class()
    sys.exit(app.app.exec_())

def test():
    """ For development and testing """
    class TestApp(GUIApplication):
        def __init__(self):
            super().__init__('test')
            self.create_widgets()
            self.on_not_implemented('hello')
            raise Exception('test exception')

        def create_widgets(self):
            self.labelled_entry('labelled_entry','enter your text',0,0)
            s = self.create_scrolled(QPlainTextEdit, True, True)
            self.layout.addWidget(s[1], 1, 0)


    main(TestApp)
