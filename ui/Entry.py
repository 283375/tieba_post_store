import logging

from PySide6.QtWidgets import QMainWindow, QWidget, QTabWidget, QVBoxLayout

from ui import _vars, Index, LogWindow, FindInvalid
from ui.components import WorkDirectory, NewThread, ThreadList

logger = logging.getLogger("root")
logger.setLevel(logging.DEBUG)

app = _vars.app

tab = QTabWidget()
indexWidget = Index.IndexWidget()
logWindowWidget = LogWindow.LogWindowWidget()
findInvalidWidget = FindInvalid.FindInvalid()

_vars.workDirectoryInstance.dirChanged.connect(
    indexWidget.threadListWidget.workDirectoryChanged
)
_vars.signals.refreshWorkDirectory.connect(indexWidget.threadListWidget.refreshDirectory)
indexWidget.threadListWidget.listUpdated.connect(
    indexWidget.threadInfoStackedWidget.updateList
)
indexWidget.threadListWidget.selectedIndexChanged.connect(
    indexWidget.threadInfoStackedWidget.setCurrentIndex
)


class LogWindowForwardHandler(logging.Handler):
    def handle(self, record):
        logWindowWidget._model.appendLogRecord(record)
        return True


logger.addHandler(LogWindowForwardHandler())

tab.addTab(indexWidget, "Index")
tab.addTab(findInvalidWidget, "Find Invalid")
tab.addTab(logWindowWidget, "Log")

centralWidget = QWidget()
centralWidget.layout = QVBoxLayout(centralWidget)
centralWidget.layout.addWidget(tab)

mainWindow = QMainWindow()
mainWindow.setCentralWidget(centralWidget)
mainWindow.setWindowTitle("tieba_post_store")
mainWindow.resize(800, 600)
mainWindow.setStatusBar(_vars.statusBar)
