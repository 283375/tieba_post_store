from PySide6.QtWidgets import (
    QListWidget,
    QListWidgetItem,
    QWidget,
    QLabel,
    QVBoxLayout,
)
from PySide6.QtCore import Qt, Signal, Slot

from ._vars import app, statusBar
from api.workDirectory import scanDirectory
from api.thread import LocalThread, getLocalThreadInfo


class ThreadListWidget(QListWidget):
    threadSelected = Signal(LocalThread)

    def __init__(self):
        super().__init__()
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setSelectionRectVisible(True)
        self.setDragEnabled(False)
        self.setAcceptDrops(False)
        self.lastDirectory = None

        self.itemDoubleClicked.connect(self.__itemChanged)

    @Slot(str)
    def workDirectoryChanged(self, workDirectory):
        statusBar.showMessage(f"正在扫描 {workDirectory}")
        app.processEvents()

        savedThreads = [
            t for dir, t in scanDirectory(workDirectory) if type(t) == LocalThread
        ]

        statusBar.showMessage(
            f"在 {workDirectory} 中找到了 {len(savedThreads)} 个有效存档目录", 10000
        )

        self.clear()
        for i, thread in enumerate(savedThreads):
            info = getLocalThreadInfo(thread)
            text = f"""
            <b>{info["title"]}</b> (ID: {info["threadId"]})
            <br>楼主 {info["author"]["displayName"]}
            <br>存档于 {info["storeDir"]}"""

            label = QLabel(text)
            widget = QWidget()
            widget.layout = QVBoxLayout(widget)
            widget.layout.addWidget(label)
            item = QListWidgetItem()
            item.setData(Qt.UserRole, thread)
            if i == 0:
                item.setSelected(True)
                self.__itemChanged(item)
            self.addItem(item)
            item.setSizeHint(widget.sizeHint())
            self.setItemWidget(item, widget)
        self.lastDirectory = workDirectory

    @Slot()
    def refreshDirectory(self):
        self.workDirectoryChanged(self.lastDirectory)

    @Slot(QListWidgetItem)
    def __itemChanged(self, item: QListWidgetItem):
        self.threadSelected.emit(item.data(Qt.UserRole))
