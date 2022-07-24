import time
import logging

from PySide6.QtWidgets import (
    QListView,
    QWidget,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QVBoxLayout,
    QHBoxLayout,
)
from PySide6.QtCore import Qt, QAbstractListModel

from typing import List, Dict, Union
from PySide6.QtCore import QModelIndex, QPersistentModelIndex, QByteArray

logger = logging.getLogger("main")

previewFormatter = logging.Formatter(
    "[%(asctime)s][%(levelname)s][%(funcName)s() in %(module)s>> %(message)s",
    "%m-%d %H:%M:%S",
)
saveFormatter = logging.Formatter(
    "[%(asctime)s][%(levelno)s:%(levelname)s][%(funcName)s() in %(module)s>> %(message)s",
    "%Y-%m-%d %H:%M:%S",
)


class LogRecordAbstractListModel(QAbstractListModel):
    __logRecordList = []
    LogRecordRole = 20

    def __init__(self, parent=None):
        super(LogRecordAbstractListModel, self).__init__(parent)

    def rowCount(self, parent=None) -> int:
        return len(self.__logRecordList)

    def roleNames(self) -> Dict[int, QByteArray]:
        return {**super().roleNames(), self.LogRecordRole: QByteArray(b"LogRecord")}

    def data(
        self,
        index: Union[QModelIndex, QPersistentModelIndex],
        role: int = Qt.DisplayRole,
    ):
        if not index.isValid() or index.row() >= self.rowCount():
            return None
        return self.__logRecordList[index.row()].get(role)

    def appendLogRecord(self, record: logging.LogRecord):
        _lastRow = self.rowCount()
        self.beginInsertRows(QModelIndex(), _lastRow, _lastRow)
        self.__logRecordList.append(
            {
                Qt.DisplayRole: previewFormatter.format(record),
                self.LogRecordRole: record,
            }
        )
        self.endInsertRows()

    def _getAllLogRecords(self):
        return [rObj[self.LogRecordRole] for rObj in self.__logRecordList]


class LogWindowWidget(QWidget):
    def __init__(self, parent=None):
        super(LogWindowWidget, self).__init__(parent)
        self.fileDialog = QFileDialog()
        self.buttonWrapper = QHBoxLayout()
        self.exportSelectionButton = QPushButton("导出选中日志")
        self.exportAllButton = QPushButton("导出所有日志")
        self.exportSelectionButton.clicked.connect(self.exportSelection)
        self.exportAllButton.clicked.connect(self.exportAll)
        self.buttonWrapper.addWidget(self.exportSelectionButton)
        self.buttonWrapper.addWidget(self.exportAllButton)

        self._view = QListView(self)
        self._view.setAcceptDrops(False)
        self._view.setDragEnabled(False)
        self._view.setSelectionMode(QListView.ExtendedSelection)

        self._model = LogRecordAbstractListModel()
        self._model.rowsInserted.connect(self._view.scrollToBottom)
        self._view.setModel(self._model)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self._view)
        self.layout.addLayout(self.buttonWrapper)

    def getSaveFilename(self, __time: time.struct_time = None):
        _time = __time or time.localtime()
        timeStr = time.strftime("%Y%m%d-%H%M%S", _time)
        filename = f"tieba_post_store_{timeStr}.log"
        return self.fileDialog.getSaveFileName(self, "选择导出文件路径", filename)

    def _writeLogToFile(self, filename, logs: List[logging.LogRecord]) -> None:
        humanReadable = [saveFormatter.format(r) for r in logs]
        details = [str(r.__dict__) for r in logs]

        with open(filename, "w", encoding="utf-8") as f:
            f.write("----- Human readable -----\n")
            [f.write(f"{_}\n") for _ in humanReadable]
            f.write("\n----- Details -----\n")
            [f.write(f"{_}\n") for _ in details]

    def exportAll(self):
        if records := self._model._getAllLogRecords():
            if filename := self.getSaveFilename()[0]:
                self._writeLogToFile(filename, records)
        else:
            QMessageBox.warning(self, "导不出来", "没有日志可供导出")

    def exportSelection(self):
        if records := [
            self._model.data(i, self._model.LogRecordRole)
            for i in self._view.selectedIndexes()
        ]:
            if filename := self.getSaveFilename()[0]:
                self._writeLogToFile(filename, records)
        else:
            QMessageBox.warning(self, "导不出来", "没有选择任何日志")
