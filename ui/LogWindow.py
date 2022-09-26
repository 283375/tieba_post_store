import time
import logging

from PySide6.QtWidgets import (
    QListView,
    QWidget,
    QSpinBox,
    QLabel,
    QSpacerItem,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
)
from PySide6.QtCore import (
    Qt,
    QAbstractListModel,
    QIdentityProxyModel,
    QModelIndex,
    QByteArray,
)


logger = logging.getLogger("root")

previewFormatter = logging.Formatter(
    "[%(asctime)s %(levelname)s][%(name)s > %(funcName)s()>> %(message)s",
    "%m-%d %H:%M:%S",
)
saveFormatter = logging.Formatter(
    "[%(asctime)s %(levelno)s:%(levelname)s][%(name)s > %(funcName)s()>> %(message)s",
    "%Y-%m-%d %H:%M:%S",
)


class LogRecordAbstractListModel(QAbstractListModel):
    __logRecordList = []
    LogRecordRole = 20

    def __init__(self, parent=None):
        super(LogRecordAbstractListModel, self).__init__(parent)

    def rowCount(self, parent=None) -> int:
        return len(self.__logRecordList)

    def roleNames(self) -> dict[int, QByteArray]:
        return {
            **super().roleNames(),
            self.LogRecordRole: QByteArray(b"LogRecord"),
        }

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
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


class LogRecordDisplayLimitModel(QIdentityProxyModel):
    displayLimit = 100

    def setDisplayLimit(self, value: int):
        self.beginResetModel()
        self.displayLimit = value
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = None) -> int:
        if self.sourceModel():
            return (
                self.sourceModel().rowCount(parent)
                if self.sourceModel().rowCount(parent) < self.displayLimit
                else self.displayLimit
            )
        else:
            return 0

    def data(self, proxyIndex: QModelIndex, role: int):
        if self.sourceModel():
            if self.rowCount() < self.displayLimit:
                return self.sourceModel().data(proxyIndex, role)

            offset = self.sourceModel().rowCount() - self.displayLimit
            index = self.sourceModel().index(
                proxyIndex.row() + offset, proxyIndex.column()
            )
            return self.sourceModel().data(index, role)
        else:
            return None


class LogWindowWidget(QWidget):
    def __init__(self, parent=None):
        super(LogWindowWidget, self).__init__(parent)

        self.logLimitSpinBox = QSpinBox()
        self.logLimitSpinBox.setMaximum(10000)
        self.logLimitSpinBox.setSingleStep(10)
        self.logLimitSpinBox.setValue(100)
        self.logCountLabel = QLabel("0")
        self.logLimitUpdatePushButton = QPushButton("更新显示限制")
        spacer = QSpacerItem(1, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.upperWrapper = QHBoxLayout()
        self.upperWrapper.addWidget(QLabel("显示"))
        self.upperWrapper.addWidget(self.logLimitSpinBox)
        self.upperWrapper.addWidget(QLabel(" / "))
        self.upperWrapper.addWidget(self.logCountLabel)
        self.upperWrapper.addWidget(QLabel(" 条日志"))
        self.upperWrapper.addSpacerItem(spacer)
        self.upperWrapper.addWidget(self.logLimitUpdatePushButton)

        self._view = QListView(self)
        self._view.setAcceptDrops(False)
        self._view.setDragEnabled(False)
        self._view.setSelectionMode(QListView.ExtendedSelection)

        self._model = LogRecordAbstractListModel()
        self._model.rowsInserted.connect(self.modelRowsInserted)
        self._limitModel = LogRecordDisplayLimitModel()
        self._limitModel.setSourceModel(self._model)
        self.logLimitUpdatePushButton.clicked.connect(self.setLimitModelDisplayLimit)
        self._view.setModel(self._limitModel)

        self.fileDialog = QFileDialog()
        self.buttonWrapper = QHBoxLayout()
        self.exportSelectionButton = QPushButton("导出选中日志")
        self.exportAllButton = QPushButton("导出所有日志")
        self.exportSelectionButton.clicked.connect(self.exportSelection)
        self.exportAllButton.clicked.connect(self.exportAll)
        self.buttonWrapper.addWidget(self.exportSelectionButton)
        self.buttonWrapper.addWidget(self.exportAllButton)

        self.layout = QVBoxLayout(self)
        self.layout.addLayout(self.upperWrapper)
        self.layout.addWidget(self._view)
        self.layout.addLayout(self.buttonWrapper)

    def modelRowsInserted(
        self, topLeft: QModelIndex, bottomRight: QModelIndex, roles: list[int]
    ):
        self.logCountLabel.setText(str(self._model.rowCount()))
        self._view.scrollToBottom()

    def setLimitModelDisplayLimit(self):
        self._limitModel.setDisplayLimit(self.logLimitSpinBox.value())

    def getSaveFilename(self, __time: time.struct_time = None):
        _time = __time or time.localtime()
        timeStr = time.strftime("%Y%m%d-%H%M%S", _time)
        filename = f"tieba_post_store_{timeStr}.log"
        return self.fileDialog.getSaveFileName(self, "选择导出文件路径", filename)

    def _writeLogToFile(self, filename, logs: list[logging.LogRecord]) -> None:
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
            i.data(self._model.LogRecordRole) for i in self._view.selectedIndexes()
        ]:
            if filename := self.getSaveFilename()[0]:
                self._writeLogToFile(filename, records)
        else:
            QMessageBox.warning(self, "导不出来", "没有选择任何日志")
