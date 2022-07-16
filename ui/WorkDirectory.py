import logging

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QLabel,
    QFileDialog,
    QHBoxLayout,
)
from PySide6.QtCore import QDir, QObject, Signal, Slot

logger = logging.getLogger("main")


class WorkDirectory(QObject):
    workDirectory = QDir.currentPath()
    SIGNAL_workDirectoryChanged = Signal(str)

    def setWorkDirectory(self, dir: str):
        self.workDirectory = dir
        self.SIGNAL_workDirectoryChanged.emit(dir)
        logger.info(f"Work directory changed to {dir}")


class ChangeWorkDirectory(QWidget):
    workDirectory = WorkDirectory()

    def __init__(self):
        super().__init__()

        self.changeDirButton = QPushButton("Change")
        self.changeDirButton.setFixedWidth(100)
        self.changeDirButton.clicked.connect(self.openChangeDirDialog)

        self.changeDirDialog = QFileDialog()
        self.changeDirDialog.setFileMode(QFileDialog.Directory)
        self.changeDirDialog.setOption(QFileDialog.ShowDirsOnly)

        self.dirLabelWidget = QLabel("")
        self.dirLabelWidget.setText(self.workDirectory.workDirectory)
        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.changeDirButton)
        self.layout.addWidget(self.dirLabelWidget)

    def openChangeDirDialog(self):
        tempDir = self.workDirectory.workDirectory
        self.changeDirDialog.setDirectory(tempDir)
        if self.changeDirDialog.exec_():
            newDir = self.changeDirDialog.selectedFiles()[0]
            self.dirLabelWidget.setText(newDir)
            self.workDirectory.setWorkDirectory(newDir)
