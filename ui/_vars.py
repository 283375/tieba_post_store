import os
import sys
import logging

from PySide6.QtWidgets import QApplication, QStatusBar
from PySide6.QtCore import QObject, QDir, Signal

logger = logging.getLogger("root")

app = QApplication(sys.argv)
statusBar = QStatusBar()
logStatusBar = QStatusBar()
logStatusBar.setSizeGripEnabled(False)


class WorkDirectoryInstance(QObject):
    dir = QDir.currentPath()
    dirChanged = Signal(str)

    def setWorkDirectory(self, dir: str):
        self.dir = os.path.abspath(dir)
        self.dirChanged.emit(dir)
        logger.info(f"已将工作目录更改至 {dir}")


workDirectoryInstance = WorkDirectoryInstance()


class Signals(QObject):
    refreshWorkDirectory = Signal()


signals = Signals()
