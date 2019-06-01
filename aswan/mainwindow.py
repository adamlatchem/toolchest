""" MainWindow - the Main user interface code. """
import webbrowser
from PyQt5.QtCore import QSortFilterProxyModel, QTimer
from PyQt5.QtMultimedia import QSound
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QHeaderView, QMainWindow, qApp
from ui_mainwindow import Ui_MainWindow
from tabulatordialog import TabulatorDialog


class MainWindow(QMainWindow):
    """ The main GUI window. """
    def __init__(self, application):
        super().__init__()

        self.application = application
        self.tabulator_dialog = None
        self.sound = QSound('laser.wav')

        self.window = Ui_MainWindow()
        self.window.setupUi(self)

        self.setWindowIcon(QIcon('aswan-icon.png'))

        # Data binding
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.application.REPORT)
        self.window.treeView.setModel(self.proxy_model)

        # Command binding
        self.window.actionQuit.triggered.connect(qApp.quit)

        self.window.actionColumns.triggered.connect(self.cmd_view_columns)
        self.window.actionClear.triggered.connect(self.cmd_view_clear)
        self.window.actionFit_Columns_To_Contents.triggered.connect(
            self.cmd_view_fit_columns_to_contents)

        self.window.actionDocumentation.triggered.connect(self.cmd_help_documentation)

        # Start the report updates
        self.update()

    def cmd_view_columns(self):
        """ Configure the columns produced by the tabulator. """
        self.tabulator_dialog = TabulatorDialog(self.application)
        self.tabulator_dialog.show()

    def cmd_view_clear(self):
        """ Clear the report. """
        self.application.REPORT.clear()

    def cmd_view_fit_columns_to_contents(self):
        """ Fit report columns to visible rows. """
        self.window.treeView.header().resizeSections(QHeaderView.ResizeToContents)

    def cmd_help_documentation(self):
        """ Show documentation. """
        webbrowser.open_new('https://www.intrepiduniverse.com/')

    def update(self):
        """ Timer method to update the report in real time. """
        try:
            if self.window.actionRealtime.isChecked():
                table = self.application.REPORT.update()
                if table['rows']:
                    if self.window.actionAudible_Blink.isChecked():
                        self.sound.play()
        finally:
            QTimer.singleShot(100, self.update)
