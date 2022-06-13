import logging
from copy import deepcopy
from time import sleep

from PySide6.QtWidgets import (
    QListWidget,
    QListWidgetItem,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QCheckBox,
)
from PySide6.QtCore import Signal, Slot, Qt, QThread

# a = logging.LogRecord()


logger = logging.getLogger("main")


class FakeLoggingThread(QThread):
    def __init__(self, parent=None):
        super(FakeLoggingThread, self).__init__(parent)

    def run(self):
        for i in range(100000):
            logger.debug(f"debug message {i}")
            if i % 100 == 0:
                print(f"{i}/100000")

class LogWindowWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.logFormatter = logging.Formatter(
            "[%(asctime)s][%(levelname)s]<%(funcName)s() in %(module)s>: %(message)s",
            "%m-%d %H:%M:%S",
        )
        self.logRecords = []

        self.totalLabel = QLabel("共 0 条记录")
        self.displayCountLabel = QLabel("正显示 0 条记录")

        self.upperLabelWrapper = QWidget()
        self.upperLabelWrapper.layout = QHBoxLayout(self.upperLabelWrapper)
        self.upperLabelWrapper.layout.addWidget(self.totalLabel)
        self.upperLabelWrapper.layout.addWidget(self.displayCountLabel)

        self.listWidget = QListWidget(self)
        self.listWidget.setSelectionMode(QListWidget.ExtendedSelection)

        self.button = QPushButton("Start Fake Logging")
        self.button.clicked.connect(self.__startFakeLogging)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.upperLabelWrapper)
        self.layout.addWidget(self.listWidget)
        self.layout.addWidget(self.button)

    def __displayRecord(self, record):
        self.listWidget.addItem(QListWidgetItem(self.logFormatter.format(record)))
        self.updateDisplayRecordLabel()

    def addLogRecord(self, record):
        # print(record.__dict__)
        self.logRecords.append(record)
        self.__displayRecord(record)
        self.updateTotalLabel()

    def updateTotalLabel(self):
        self.totalLabel.setText(f"共 {len(self.logRecords)} 条记录")

    def updateDisplayRecordLabel(self):
        self.displayCountLabel.setText(f"正显示 {self.listWidget.count()} 条记录")

    @Slot()
    def __startFakeLogging(self):
        fakeLoggingThread = FakeLoggingThread(self)
        fakeLoggingThread.start()
