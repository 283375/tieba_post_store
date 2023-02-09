from PySide6.QtCore import QMetaObject, QCoreApplication
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidgetAction,
    QHBoxLayout,
    QFormLayout,
)

from ui.components.DirectoryLineEdit import DirectoryLineEdit


class Ui_Settings(object):
    def setupUi(self, widget: QWidget):
        self.layout = QFormLayout(widget)

        self.BDUSS_Label = QLabel(widget)
        self.BDUSS_Field = QLineEdit(widget)

        self.layout.addRow(self.BDUSS_Label, self.BDUSS_Field)

        self.defaultStoreDir_Label = QLabel(widget)

        self.defaultStoreDir_FieldLayout = QHBoxLayout(widget)
        self.defaultStoreDir_Field = QLabel(widget)
        self.defaultStoreDir_FieldLayout.addWidget(self.defaultStoreDir_Label)
        self.defaultStoreDir_FieldChangeButton = QPushButton(widget)
        self.defaultStoreDir_FieldLayout.addWidget(self.defaultStoreDir_FieldChangeButton)

        self.layout.addRow(self.defaultStoreDir_Label, self.defaultStoreDir_FieldLayout)

        self.retranslateUi()

        QMetaObject.connectSlotsByName(widget)

    def retranslateUi(self, widget: QWidget = None):
        self.BDUSS_Label.setText(QCoreApplication.translate("Settings", "BDUSS_Label"))
        self.defaultStoreDir_Label.setText(
            QCoreApplication.translate("Settings", "defaultStoreDir_Label")
        )
        self.defaultStoreDir_FieldChangeButton.setText(
            QCoreApplication.translate("Settings", "defaultStoreDir_FieldChangeButton")
        )
