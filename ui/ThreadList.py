from PySide6.QtWidgets import QListWidget, QListWidgetItem, QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Signal, Slot

from api.workDirectory import getSavedPosts
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
        threadList = getSavedPosts(workDirectory)
        self.clear()
        for thread in threadList:
            text = """<b>{title}</b> (ID: {id})
            <br>{authorDisplayName} (原名 {authorOrigName})
            <br>存档于 {dir}""".format(
                title=thread.threadInfo["title"],
                id=thread.threadInfo["id"],
                authorDisplayName=thread.threadInfo["author"]["displayName"],
                authorOrigName=thread.threadInfo["author"]["origName"],
                dir=thread.storeDir,
            )
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
        print("itemChanged")
        self.threadSelected.emit(item.localThread)
