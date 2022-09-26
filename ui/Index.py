from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt

from ui.components import WorkDirectory, NewThread, ThreadList


class IndexWidget(QWidget):
    def __init__(self, parent=None):
        super(IndexWidget, self).__init__(parent)

        self.workDirectoryWidget = WorkDirectory.ChangeWorkDirectory()
        self.threadListWidget = ThreadList.ThreadListWidget()
        self.threadInfoStackedWidget = ThreadList.ThreadInfoStackedWidget()
        self.newThreadWidget = NewThread.NewThreadEntryWidget()

        self.threadListWidget.setMaximumWidth(300)
        self.newThreadWidget.setMaximumWidth(200)
        self.listWrapper = QWidget()
        self.listWrapper.setMaximumWidth(300)
        self.listWrapper.layout = QVBoxLayout(self.listWrapper)
        self.listWrapper.layout.setAlignment(Qt.AlignVCenter | Qt.AlignTop)
        self.listWrapper.layout.addWidget(self.threadListWidget)
        self.listWrapper.layout.addWidget(self.newThreadWidget)

        self.indexLowerWrapper = QHBoxLayout()
        self.indexLowerWrapper.setStretch(0, 0)
        self.indexLowerWrapper.addWidget(self.listWrapper)
        self.indexLowerWrapper.addWidget(self.threadInfoStackedWidget)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.workDirectoryWidget)
        self.layout.addLayout(self.indexLowerWrapper)
