from PySide6.QtCore import QMetaObject, QCoreApplication
from PySide6.QtWidgets import QWidget, QPushButton, QFileDialog, QLabel, QHBoxLayout


class Ui_WorkDirectory(object):
    def setupUi(self, widget: QWidget):
        if not widget.objectName():
            widget.setObjectName("WorkDirectory")

        self.layout = QHBoxLayout(widget)

        self.changeDirButton = QPushButton(widget)
        self.changeDirButton.setObjectName("changeDirButton")

        self.layout.addWidget(self.changeDirButton)

        self.changeDirFileDialog = QFileDialog(widget)
        self.changeDirFileDialog.setFileMode(QFileDialog.Directory)
        self.changeDirFileDialog.setOption(QFileDialog.ShowDirsOnly)

        self.dirLabel = QLabel(widget)

        self.layout.addWidget(self.dirLabel)

        self.retranslateUi(widget)

        QMetaObject.connectSlotsByName(widget)

    def retranslateUi(self, widget: QWidget = None):
        self.changeDirButton.setText(
            QCoreApplication.translate("WorkDirectory", "changeDirButton", None)
        )
