#!/usr/bin/env python3
r"""
The mightiest stream is held back by only the mightiest dam...
                       _
                      / \   _____      ____ _ _ __
                     / _ \ / __\ \ /\ / / _` | '_ \
                    / ___ \\__ \\ V  V / (_| | | | |
                   /_/   \_\___/ \_/\_/ \__,_|_| |_|

   __________      ___________      _____________      ___________________
 /         |      |         |      |           |      |  |   |   |   |  |
 |  File   |      | Convert |      |           |      -------------------
 |  Based  | ---> |   to    | ---> | Aggregate | ---> |  | G | U | I |  |
 |  Feed   |      |  Table  |      |           |      -------------------
 | <stdin> |      |         |      |           |      |  |   |   |   |  |
 -----------      -----------      -------------      -------------------

The file stream is a byte stream containing records. Each record contains
fields. The records are converted to a table including metadata and passed
to the aggregator. The aggregator groups records and updates the report
using key metadata provided by the proceeding tabulation process.
"""
import sys
from PyQt5.QtWidgets import QApplication
from aggregator import Aggregator
from mainwindow import MainWindow
from report import Report
from tabulator import Tabulator


if __name__ == '__main__':
    APPLICATION = QApplication(sys.argv)
    APPLICATION.TABULATOR = Tabulator()
    APPLICATION.AGGREGATOR = Aggregator(APPLICATION.TABULATOR)
    APPLICATION.REPORT = Report(APPLICATION.AGGREGATOR)
    GUI = MainWindow(APPLICATION)

    GUI.show()
    sys.exit(APPLICATION.exec_())
