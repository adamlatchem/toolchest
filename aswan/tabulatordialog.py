""" Tabulator Dialog is used to configure the available table columns for a
report."""
from PyQt5.QtWidgets import QDialog
from ui_tabulatordialog import Ui_TabulatorDialog
from tabulator import SyslogConfig, TcpDumpConfig, WeblogConfig, DelimitedTextFieldParser


class TabulatorDialog(QDialog):
    """ Setup the tabulator. """
    OPTIONS = {'Default':DelimitedTextFieldParser,
               'TcpDump': TcpDumpConfig,
               'WebLog': WeblogConfig,
               'SysLog': SyslogConfig}

    def __init__(self, application):
        super().__init__()

        self.dialog = Ui_TabulatorDialog()
        self.dialog.setupUi(self)
        self.application = application

        # Data binding
        self.dialog.comboBox.insertItems(0, list(self.OPTIONS.keys()))

        # Command binding
        self.dialog.buttonBox.accepted.connect(self.cmd_apply)
        self.dialog.buttonBox.rejected.connect(self.close)

    def cmd_apply(self):
        """ Handle Ok/Cancel. """
        option = self.dialog.comboBox.currentText()
        self.application.TABULATOR.config = self.OPTIONS[option]()
        self.application.TABULATOR.replay()
        self.application.REPORT.clear()
        self.close()
