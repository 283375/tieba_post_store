import sys
import logging
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTabWidget,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
)

from ui import __vars, LogWindow, ThreadInfo, ThreadList, WorkDirectory

logger = logging.getLogger("main")
logger.setLevel(logging.DEBUG)


if __name__ == "__main__":
    app = __vars.app

    tab = QTabWidget()
    workDirectoryWidget = WorkDirectory.ChangeWorkDirectory()
    threadListWidget = ThreadList.ThreadListWidget()
    threadInfoWidget = ThreadInfo.ThreadInfoWidget()
    logWindowWidget = LogWindow.LogWindowWidget()

    workDirectoryWidget.workDirectory.SIGNAL_workDirectoryChanged.connect(
        threadListWidget.workDirectoryChanged
    )
    threadListWidget.threadSelected.connect(threadInfoWidget.updateLocalThread)

    class ActuallyNotAFilter(logging.Filter):
        def filter(self, record):
            logWindowWidget.addLogRecord(record)
            return True

    logger.addFilter(ActuallyNotAFilter())

    indexLowerWrapper = QWidget()
    indexLowerWrapper.layout = QHBoxLayout(indexLowerWrapper)
    indexLowerWrapper.layout.setStretch(0, 0)
    threadListWidget.setMaximumWidth(300)
    indexLowerWrapper.layout.addWidget(threadListWidget)
    indexLowerWrapper.layout.addWidget(threadInfoWidget)

    indexWrapper = QWidget()
    indexWrapper.layout = QVBoxLayout(indexWrapper)
    indexWrapper.layout.addWidget(workDirectoryWidget)
    indexWrapper.layout.addWidget(indexLowerWrapper)

    tab.addTab(indexWrapper, "Index")
    tab.addTab(logWindowWidget, "Log")

    centralWidget = QWidget()
    centralWidget.layout = QVBoxLayout(centralWidget)
    centralWidget.layout.addWidget(tab)

    mainWindow = QMainWindow()
    mainWindow.setCentralWidget(centralWidget)
    mainWindow.setWindowTitle("tieba_post_store")
    mainWindow.resize(800, 600)
    mainWindow.setStatusBar(__vars.statusBar)
    mainWindow.show()
    sys.exit(app.exec())
