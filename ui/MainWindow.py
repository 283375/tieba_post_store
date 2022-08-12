import logging

from PySide6.QtWidgets import QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt

from . import _vars, WorkDirectory, ThreadList, NewThread, ThreadInfo, LogWindow

logger = logging.getLogger("root")
logger.setLevel(logging.DEBUG)

app = _vars.app

tab = QTabWidget()
workDirectoryWidget = WorkDirectory.ChangeWorkDirectory()
threadListWidget = ThreadList.ThreadListWidget()
threadInfoStackedWidget = ThreadList.ThreadInfoStackedWidget()
newThreadWidget = NewThread.NewThreadEntryWidget()
logWindowWidget = LogWindow.LogWindowWidget()

_vars.workDirectoryInstance.dirChanged.connect(threadListWidget.workDirectoryChanged)
_vars.signals.refreshWorkDirectory.connect(threadListWidget.refreshDirectory)
threadListWidget.listUpdated.connect(threadInfoStackedWidget.updateList)
threadListWidget.selectedIndexChanged.connect(threadInfoStackedWidget.setCurrentIndex)


class LogWindowForwardHandler(logging.Handler):
    def handle(self, record):
        logWindowWidget._model.appendLogRecord(record)
        return True


logger.addHandler(LogWindowForwardHandler())

threadListWidget.setMaximumWidth(300)
newThreadWidget.setMaximumWidth(200)
listWrapper = QWidget()
listWrapper.setMaximumWidth(300)
listWrapper.layout = QVBoxLayout(listWrapper)
listWrapper.layout.setAlignment(Qt.AlignVCenter | Qt.AlignTop)
listWrapper.layout.addWidget(threadListWidget)
listWrapper.layout.addWidget(newThreadWidget)

indexLowerWrapper = QHBoxLayout()
indexLowerWrapper.setStretch(0, 0)
indexLowerWrapper.addWidget(listWrapper)
indexLowerWrapper.addWidget(threadInfoStackedWidget)

indexWrapper = QWidget()
indexWrapper.layout = QVBoxLayout(indexWrapper)
indexWrapper.layout.addWidget(workDirectoryWidget)
indexWrapper.layout.addLayout(indexLowerWrapper)

tab.addTab(indexWrapper, "Index")
tab.addTab(logWindowWidget, "Log")

centralWidget = QWidget()
centralWidget.layout = QVBoxLayout(centralWidget)
centralWidget.layout.addWidget(tab)

mainWindow = QMainWindow()
mainWindow.setCentralWidget(centralWidget)
mainWindow.setWindowTitle("tieba_post_store")
mainWindow.resize(800, 600)
mainWindow.setStatusBar(_vars.statusBar)
