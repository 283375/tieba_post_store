import logging

from PySide6.QtCore import QTranslator
from PySide6.QtWidgets import QMainWindow, QWidget, QTabWidget, QVBoxLayout

from ui import sharedVars
from ui.layouts import Index, FindInvalid, LogWindow
from ui.resources import main_qrc

logger = logging.getLogger("root")
logger.setLevel(logging.DEBUG)

app = sharedVars.app

translator = QTranslator(app)
translator.load(":/lang/zh_CN.qm")
app.installTranslator(translator)


tab = QTabWidget()
indexWidget = Index.IndexWidget()
logWindowWidget = LogWindow.Layout_LogWindow()
findInvalidWidget = FindInvalid.Layout_FindInvalid()

sharedVars.workDirectoryObject.dirScanValidResult.connect(
    indexWidget.threadListWidget.dirScanComplete
)
sharedVars.workDirectoryObject.dirScanResult.connect(findInvalidWidget.scanComplete)
indexWidget.threadListWidget.threadSelected.connect(indexWidget.updateLocalThread)

# All widgets are now initialized and connected to the signals,
# so we could now run a scan, emit the result to the widgets.
sharedVars.workDirectoryObject.scan()


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
mainWindow.setStatusBar(sharedVars.statusBar)
