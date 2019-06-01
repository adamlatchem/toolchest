# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'tabulatordialog.ui'
#
# Created by: PyQt5 UI code generator 5.12.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_TabulatorDialog(object):
    def setupUi(self, TabulatorDialog):
        TabulatorDialog.setObjectName("TabulatorDialog")
        TabulatorDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        TabulatorDialog.resize(250, 400)
        TabulatorDialog.setMinimumSize(QtCore.QSize(128, 128))
        TabulatorDialog.setSizeGripEnabled(True)
        TabulatorDialog.setModal(True)
        self.verticalLayout = QtWidgets.QVBoxLayout(TabulatorDialog)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.toolBox = QtWidgets.QToolBox(TabulatorDialog)
        self.toolBox.setObjectName("toolBox")
        self.bufferPage = QtWidgets.QWidget()
        self.bufferPage.setGeometry(QtCore.QRect(0, 0, 250, 259))
        self.bufferPage.setObjectName("bufferPage")
        self.formLayout_3 = QtWidgets.QFormLayout(self.bufferPage)
        self.formLayout_3.setObjectName("formLayout_3")
        self.label_2 = QtWidgets.QLabel(self.bufferPage)
        self.label_2.setObjectName("label_2")
        self.formLayout_3.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_2)
        self.toolBox.addItem(self.bufferPage, "")
        self.recordPage = QtWidgets.QWidget()
        self.recordPage.setObjectName("recordPage")
        self.formLayout_2 = QtWidgets.QFormLayout(self.recordPage)
        self.formLayout_2.setObjectName("formLayout_2")
        self.label = QtWidgets.QLabel(self.recordPage)
        self.label.setObjectName("label")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.label)
        self.toolBox.addItem(self.recordPage, "")
        self.fieldPage = QtWidgets.QWidget()
        self.fieldPage.setGeometry(QtCore.QRect(0, 0, 250, 259))
        self.fieldPage.setObjectName("fieldPage")
        self.formLayout = QtWidgets.QFormLayout(self.fieldPage)
        self.formLayout.setObjectName("formLayout")
        self.toolBox.addItem(self.fieldPage, "")
        self.templatesPage = QtWidgets.QWidget()
        self.templatesPage.setObjectName("templatesPage")
        self.formLayout_4 = QtWidgets.QFormLayout(self.templatesPage)
        self.formLayout_4.setObjectName("formLayout_4")
        self.label_3 = QtWidgets.QLabel(self.templatesPage)
        self.label_3.setObjectName("label_3")
        self.formLayout_4.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_3)
        self.comboBox = QtWidgets.QComboBox(self.templatesPage)
        self.comboBox.setObjectName("comboBox")
        self.formLayout_4.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.comboBox)
        self.toolBox.addItem(self.templatesPage, "")
        self.verticalLayout.addWidget(self.toolBox)
        self.buttonBox = QtWidgets.QDialogButtonBox(TabulatorDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(TabulatorDialog)
        self.toolBox.setCurrentIndex(2)
        self.toolBox.layout().setSpacing(0)
        self.buttonBox.accepted.connect(TabulatorDialog.accept)
        self.buttonBox.rejected.connect(TabulatorDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(TabulatorDialog)

    def retranslateUi(self, TabulatorDialog):
        _translate = QtCore.QCoreApplication.translate
        TabulatorDialog.setWindowTitle(_translate("TabulatorDialog", "Columns"))
        self.label_2.setText(_translate("TabulatorDialog", "utils.get_buffer"))
        self.toolBox.setItemText(self.toolBox.indexOf(self.bufferPage), _translate("TabulatorDialog", "Buffer"))
        self.label.setText(_translate("TabulatorDialog", "DelimitedTextRecordParser"))
        self.toolBox.setItemText(self.toolBox.indexOf(self.recordPage), _translate("TabulatorDialog", "Record"))
        self.toolBox.setItemText(self.toolBox.indexOf(self.fieldPage), _translate("TabulatorDialog", "Field"))
        self.label_3.setText(_translate("TabulatorDialog", "Parser"))
        self.toolBox.setItemText(self.toolBox.indexOf(self.templatesPage), _translate("TabulatorDialog", "Templates"))




if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    TabulatorDialog = QtWidgets.QDialog()
    ui = Ui_TabulatorDialog()
    ui.setupUi(TabulatorDialog)
    TabulatorDialog.show()
    sys.exit(app.exec_())
