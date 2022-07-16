from PySide6.QtWidgets import (
    QApplication,
    QListWidget,
    QListWidgetItem,
    QWidget,
    QLabel,
    QVBoxLayout,
)
from PySide6.QtCore import Signal, Slot

from .__vars import statusBar
from api.workDirectory import scanDirectory
from api.thread import LocalThread


class ThreadListWidget(QListWidget):
    threadSelected = Signal(LocalThread)

    def __init__(self):
        super().__init__()
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setSelectionRectVisible(True)
        self.setDragEnabled(False)
        self.setAcceptDrops(False)

        self.itemDoubleClicked.connect(self.__itemChanged)

    @Slot(str)
    def workDirectoryChanged(self, workDirectory):
        statusBar.showMessage(f"正在扫描 {workDirectory}")
        QApplication.instance().processEvents()

        savedThreads = [
            t
            for dir, t in scanDirectory(workDirectory)
            if t is not None and type(t) == LocalThread
        ]

        statusBar.showMessage(
            f"Found {len(savedThreads)} posts in {workDirectory}", 10000
        )

        self.clear()
        for thread in savedThreads:
            text = f"""
            <b>{thread.threadInfo["title"]}</b> (ID: {thread.threadInfo["id"]})
            <br>{thread.threadInfo["author"]["displayName"]} (原名 {thread.threadInfo["author"]["origName"]})
            <br>存档于 {thread.storeDir}"""

            label = QLabel(text)
            widget = QWidget()
            widget.layout = QVBoxLayout(widget)
            widget.layout.addWidget(label)
            item = QListWidgetItem()
            item.localThread = thread
            self.addItem(item)
            item.setSizeHint(widget.sizeHint())
            self.setItemWidget(item, widget)

    @Slot(QListWidgetItem)
    def __itemChanged(self, item):
        self.threadSelected.emit(item.localThread)
