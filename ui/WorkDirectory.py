import logging

from PySide6.QtWidgets import (
    QWidget,
    QPushButton,
    QLabel,
    QFileDialog,
    QHBoxLayout,
)
from ._vars import workDirectoryInstance

logger = logging.getLogger("root")


class ChangeWorkDirectory(QWidget):
    def __init__(self):
        super().__init__()

        self.changeDirButton = QPushButton("更改工作目录")
        self.changeDirButton.setFixedWidth(100)
        self.changeDirButton.clicked.connect(self.openChangeDirDialog)

        self.changeDirDialog = QFileDialog()
        self.changeDirDialog.setFileMode(QFileDialog.Directory)
        self.changeDirDialog.setOption(QFileDialog.ShowDirsOnly)

        self.dirLabelWidget = QLabel("")
        self.dirLabelWidget.setText(workDirectoryInstance.dir)
        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.changeDirButton)
        self.layout.addWidget(self.dirLabelWidget)

    def openChangeDirDialog(self):
        tempDir = workDirectoryInstance.dir
        self.changeDirDialog.setDirectory(tempDir)
        if self.changeDirDialog.exec_():
            newDir = self.changeDirDialog.selectedFiles()[0]
            self.dirLabelWidget.setText(newDir)
            workDirectoryInstance.setWorkDirectory(newDir)
