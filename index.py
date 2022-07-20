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

from ui import LogWindow, ThreadInfo, ThreadList, WorkDirectory, __vars

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

    logStatusBar = __vars.logStatusBar
    class LogForwardHandler(logging.Handler):
        def __init__(self, level=logging.DEBUG):
            super().__init__(level)
            self.formatter = logging.Formatter(
                "[%(asctime)s][%(levelname)s]: %(message)s",
                "%m-%d %H:%M:%S",
            )

        def handle(self, record):
            logWindowWidget.addLogRecord(record)
            if record.levelno >= logging.INFO:
                logStatusBar.showMessage(self.format(record))
                app.processEvents()
            return True

        def format(self, record) -> str:
            return self.formatter.format(record)

    logger.addHandler(LogForwardHandler())

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
    centralWidget.layout.addWidget(__vars.logStatusBar)

    mainWindow = QMainWindow()
    mainWindow.setCentralWidget(centralWidget)
    mainWindow.setWindowTitle("tieba_post_store")
    mainWindow.resize(800, 600)
    mainWindow.setStatusBar(__vars.statusBar)
    mainWindow.show()
    sys.exit(app.exec())
