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
from PySide6.QtCore import Qt

from ui import LogWindow, ThreadInfo, ThreadList, NewThread, WorkDirectory, _vars

logger = logging.getLogger("main")
logger.setLevel(logging.DEBUG)


if __name__ == "__main__":
    app = _vars.app

    tab = QTabWidget()
    workDirectoryWidget = WorkDirectory.ChangeWorkDirectory()
    threadListWidget = ThreadList.ThreadListWidget()
    newThreadWidget = NewThread.NewThreadWidget()
    threadInfoWidget = ThreadInfo.ThreadInfoWidget()
    logWindowWidget = LogWindow.LogWindowWidget()

    _vars.workDirectoryInstance.dirChanged.connect(threadListWidget.workDirectoryChanged)
    _vars.signals.refreshWorkDirectory.connect(threadListWidget.refreshDirectory)
    threadListWidget.threadSelected.connect(threadInfoWidget.updateLocalThread)

    class LogForwardHandler(logging.Handler):
        def __init__(self, level=logging.DEBUG):
            super().__init__(level)
            self.formatter = logging.Formatter(
                "[%(asctime)s][%(levelname)s]: %(message)s",
                "%m-%d %H:%M:%S",
            )

        def handle(self, record):
            logWindowWidget._model.appendLogRecord(record)
            if record.levelno >= logging.INFO:
                _vars.logStatusBar.showMessage(f"最新日志: {self.format(record)}")
                app.processEvents()
            return True

        def format(self, record) -> str:
            return self.formatter.format(record)

    logger.addHandler(LogForwardHandler())

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
    indexLowerWrapper.addWidget(threadInfoWidget)

    indexWrapper = QWidget()
    indexWrapper.layout = QVBoxLayout(indexWrapper)
    indexWrapper.layout.addWidget(workDirectoryWidget)
    indexWrapper.layout.addLayout(indexLowerWrapper)

    tab.addTab(indexWrapper, "Index")
    tab.addTab(logWindowWidget, "Log")

    centralWidget = QWidget()
    centralWidget.layout = QVBoxLayout(centralWidget)
    centralWidget.layout.addWidget(tab)
    centralWidget.layout.addWidget(_vars.logStatusBar)

    mainWindow = QMainWindow()
    mainWindow.setCentralWidget(centralWidget)
    mainWindow.setWindowTitle("tieba_post_store")
    mainWindow.resize(800, 600)
    mainWindow.setStatusBar(_vars.statusBar)
    mainWindow.show()
    sys.exit(app.exec())
