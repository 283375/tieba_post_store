import logging

from PySide6.QtCore import QTranslator
from PySide6.QtWidgets import QMainWindow, QWidget, QTabWidget, QVBoxLayout

from ui import _vars
from ui.layouts import Index, FindInvalid, LogWindow

logger = logging.getLogger("root")
logger.setLevel(logging.DEBUG)

app = _vars.app

translator = QTranslator(app)
translator.load("./ui/lang/zh_CN.qm")
app.installTranslator(translator)


tab = QTabWidget()
indexWidget = Index.IndexWidget()
logWindowWidget = LogWindow.LogWindowWidget()
findInvalidWidget = FindInvalid.FindInvalid()

_vars.workDirectoryObject.dirScanValidResult.connect(
    indexWidget.threadListWidget.dirScanComplete
)
_vars.workDirectoryObject.dirScanResult.connect(findInvalidWidget.scanComplete)
indexWidget.threadListWidget.threadSelected.connect(indexWidget.updateLocalThread)


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
