import sys
import time
import logging
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QListWidget,
    QComboBox,
    QTabWidget,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
)
from PySide6.QtCore import QThread

from ui import WorkDirectory, ThreadList, ThreadInfo, LogWindow

logger = logging.getLogger("main")
logger.setLevel(logging.DEBUG)


if __name__ == "__main__":
    app = QApplication(sys.argv)

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

    window = QMainWindow()
    window.setCentralWidget(centralWidget)
    window.setWindowTitle("贴子存档")
    window.resize(800, 600)
    window.show()

    sys.exit(app.exec())
