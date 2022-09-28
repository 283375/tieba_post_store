from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt, Slot

from api.thread import LocalThread
from ui.components import WorkDirectory, NewThread, ThreadList, ThreadInfo


class IndexWidget(QWidget):
    def __init__(self, parent=None):
        super(IndexWidget, self).__init__(parent)

        emptyThreadInfoWidget = QWidget()
        emptyThreadInfoWidget.layout = QVBoxLayout(emptyThreadInfoWidget)
        emptyThreadInfoWidget.layout.addWidget(QLabel("未选择任何存档"))

        self.workDirectoryWidget = WorkDirectory.WorkDirectory()
        self.threadListWidget = ThreadList.ThreadListWidget()
        self.threadInfoWidget = emptyThreadInfoWidget
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
        self.indexLowerWrapper.addWidget(self.threadInfoWidget)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.workDirectoryWidget)
        self.layout.addLayout(self.indexLowerWrapper)

    @Slot()
    def updateLocalThread(self, lt: LocalThread):
        newWidget = ThreadInfo.ThreadInfo()
        newWidget.retranslateUi()
        newWidget.updateLabels(lt)
        self.indexLowerWrapper.removeWidget(self.threadInfoWidget)
        self.threadInfoWidget.close()
        oldWidget = self.threadInfoWidget
        self.threadInfoWidget = newWidget
        self.indexLowerWrapper.addWidget(self.threadInfoWidget)
        self.threadInfoWidget.show()
        oldWidget.deleteLater()
