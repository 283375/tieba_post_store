import os
import sys
import logging

from PySide6.QtWidgets import QApplication, QStatusBar
from PySide6.QtCore import QObject, QDir, QThread, Signal, Slot

from api.workDirectory import scanDirectory
from api.thread import LocalThread

logger = logging.getLogger("root")

app = QApplication(sys.argv)
statusBar = QStatusBar()


class ScanWorkDirectoryThread(QThread):
    scanningDir = Signal(str)
    scanResult = Signal(list)

    def __init__(self, parent=None):
        super(ScanWorkDirectoryThread, self).__init__(parent)

    def setDir(self, dir: str):
        self.dir = dir

    def run(self):
        if self.dir and os.access(self.dir, os.R_OK):
            results = []

            for dir, t in scanDirectory(self.dir):
                results.append((dir, t))
                self.scanningDir.emit(dir)

            self.scanResult.emit(results)


class WorkDirectoryObject(QObject):
    dir = QDir.currentPath()
    dirChanged = Signal(str)
    dirScanning = Signal(str)
    dirScanResult = Signal(list)
    dirScanValidResult = Signal(list)

    def __init__(self):
        super(WorkDirectoryObject, self).__init__()
        self.scanThread = ScanWorkDirectoryThread()
        self.scanThread.scanningDir.connect(lambda dir: self.dirScanning.emit(dir))
        self.scanThread.scanResult.connect(self.threadScanComplete)

        self.setWorkDirectory(QDir.currentPath())

    def setWorkDirectory(self, dir: str):
        self.dir = os.path.abspath(dir)
        self.dirChanged.emit(self.dir)
        logger.info(f"已将工作目录更改至 {self.dir}")
        self.scanThread.setDir(self.dir)
        self.scan()

    def scan(self):
        self.scanThread.run()

    @Slot(list)
    def threadScanComplete(self, result: list[tuple[str, LocalThread]]):
        self.dirScanResult.emit(result)
        self.dirScanValidResult.emit(
            [(dir, t) for dir, t in result if t is not None and t.isValid]
        )


workDirectoryObject = WorkDirectoryObject()
