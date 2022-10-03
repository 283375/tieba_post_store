import time
import logging

from PySide6.QtCore import (
    Qt,
    QAbstractListModel,
    QIdentityProxyModel,
    QModelIndex,
    QByteArray,
    QCoreApplication,
    QMetaObject,
)
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QListView,
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

logger = logging.getLogger("root")

formatter = logging.Formatter(
    "[%(asctime)s %(levelno)s:%(levelname)s][%(name)s > %(funcName)s()>> %(message)s",
    "%m-%d %H:%M:%S",
)


class LogRecordModel(QAbstractListModel):
    __logRecordList = []
    LogRecordRole = Qt.UserRole + 1

    def __init__(self, parent=None):
        super(LogRecordModel, self).__init__(parent)

    def rowCount(self, parent=None):
        return len(self.__logRecordList)

    def roleNames(self):
        return {
            **super().roleNames(),
            self.LogRecordRole: QByteArray("LogRecord"),
        }

    def data(self, index, role=Qt.DisplayRole):
        # sourcery skip: remove-unnecessary-else, swap-if-else-branches
        if not index.isValid() or index.row() >= self.rowCount():
            return None

        if role == Qt.DisplayRole:
            logRecord = self.__logRecordList[index.row()].get(self.LogRecordRole)
            return formatter.format(logRecord) if logRecord else None
        else:
            return self.__logRecordList[index.row()].get(role)

    def appendLogRecord(self, record: logging.LogRecord):
        _lastRow = self.rowCount()
        self.beginInsertRows(QModelIndex(), _lastRow, _lastRow)
        self.__logRecordList.append({self.LogRecordRole: record})
        self.endInsertRows()


class LogRecordLimitModel(QIdentityProxyModel):
    displayLimit = 100

    def setDisplayLimit(self, value: int):
        self.beginResetModel()
        self.displayLimit = value
        self.endResetModel()

    def rowCount(self, parent=None):
        if self.sourceModel():
            return (
                self.sourceModel().rowCount(parent)
                if self.sourceModel().rowCount(parent) < self.displayLimit
                else self.displayLimit
            )
        else:
            return 0

    def data(self, proxyIndex, role):
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


class Ui_Layout_LogWindow(object):
    def setupUi(self, widget: QWidget):
        self.layout = QVBoxLayout(widget)

        # upperFrame start
        self.upperFrame = QFrame(widget)
        self.upperFrameLayout = QHBoxLayout(self.upperFrame)

        # upperFrame -> logLimitFrame start
        self.logLimitFrame = QFrame(self.upperFrame)
        self.logLimitLayout = QHBoxLayout(self.logLimitFrame)

        self.logLimitPrefix = QLabel(self.logLimitFrame)
        self.logLimitLayout.addWidget(self.logLimitPrefix)

        self.logLimitSpinBox = QSpinBox(self.logLimitFrame)
        self.logLimitSpinBox.setMaximum(10000)
        self.logLimitSpinBox.setSingleStep(10)
        self.logLimitSpinBox.setValue(100)
        self.logLimitLayout.addWidget(self.logLimitSpinBox)

        self.logLimitSeperateSlash = QLabel("/", self.logLimitFrame)
        self.logLimitLayout.addWidget(self.logLimitSeperateSlash)

        self.logCount = QLabel("0", self.logLimitFrame)
        self.logLimitLayout.addWidget(self.logCount)

        self.logLimitSuffix = QLabel(self.logLimitFrame)
        self.logLimitLayout.addWidget(self.logLimitSuffix)

        self.upperFrameLayout.addWidget(self.logLimitFrame)
        # upperFrame -> logLimitFrame end

        self.horizontalSpacerItem = QSpacerItem(
            0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum
        )
        self.upperFrameLayout.addSpacerItem(self.horizontalSpacerItem)

        self.setLogLimitButton = QPushButton(self.upperFrame)
        self.setLogLimitButton.setIcon(QIcon(":/icons/reload.svg"))

        self.upperFrameLayout.addWidget(self.setLogLimitButton)

        self.layout.addWidget(self.upperFrame)
        # upperFrame end

        self.listView = QListView(widget)
        self.listView.setAcceptDrops(False)
        self.listView.setDragEnabled(False)
        self.listView.setSelectionMode(QListView.ExtendedSelection)

        self.layout.addWidget(self.listView)

        self.fileDialog = QFileDialog(widget)

        # exportFrame start
        self.exportFrame = QFrame(widget)
        self.exportLayout = QHBoxLayout(self.exportFrame)

        self.exportAllButton = QPushButton(self.exportFrame)
        self.exportLayout.addWidget(self.exportAllButton)

        self.exportSelectionButton = QPushButton(self.exportFrame)
        self.exportLayout.addWidget(self.exportSelectionButton)

        self.layout.addWidget(self.exportFrame)
        # exportFrame end

        self.retranslateUi(widget)

        QMetaObject.connectSlotsByName(widget)

    def retranslateUi(self, widget: QWidget = None):
        self.logLimitPrefix.setText(
            QCoreApplication.translate("Layout_LogWindow", "logLimitPrefix")
        )
        self.logLimitSuffix.setText(
            QCoreApplication.translate("Layout_LogWindow", "logLimitSuffix")
        )
        self.setLogLimitButton.setText(
            QCoreApplication.translate("Layout_LogWindow", "setLogLimitButton")
        )
        self.exportAllButton.setText(
            QCoreApplication.translate("Layout_LogWindow", "exportAllButton")
        )
        self.exportSelectionButton.setText(
            QCoreApplication.translate("Layout_LogWindow", "exportSelectionButton")
        )


class LogWindowForwardHandler(logging.Handler):
    def __init__(self, model):
        super(LogWindowForwardHandler, self).__init__()
        self.model = model

    def handle(self, record):
        self.model.appendLogRecord(record)
        return True


class Layout_LogWindow(QWidget, Ui_Layout_LogWindow):
    def __init__(self, parent=None):
        super(Layout_LogWindow, self).__init__(parent)
        self.setupUi(self)

        self._model = LogRecordModel()
        self._model.rowsInserted.connect(self.modelRowsInserted)

        self.logRecordForwarder = LogWindowForwardHandler(self._model)
        logger.addHandler(self.logRecordForwarder)

        self._limitModel = LogRecordLimitModel()
        self._limitModel.setSourceModel(self._model)

        self.setLogLimitButton.clicked.connect(self.setDisplayLimit)

        self.listView.setModel(self._limitModel)

        self.exportSelectionButton.clicked.connect(self.exportSelection)
        self.exportAllButton.clicked.connect(self.exportAll)

    def modelRowsInserted(self, *args):
        # args: (topLeft, bottomRight, roles)
        self.logCount.setText(str(self._model.rowCount()))
        self.listView.scrollToBottom()

    def setDisplayLimit(self):
        self._limitModel.setDisplayLimit(self.logLimitSpinBox.value())

    def getSaveFilename(self, __time: time.struct_time = None):
        _time = __time or time.localtime()
        timeStr = time.strftime("%Y%m%d-%H%M%S", _time)
        filename = f"tieba_post_store_{timeStr}.log"
        return self.fileDialog.getSaveFileName(
            self,
            QCoreApplication.translate("Layout_LogWindow", "getSaveFileNameDialogTitle"),
            filename,
        )

    def _writeLogToFile(self, filename, logs: list[logging.LogRecord]) -> None:
        humanReadable = [formatter.format(r) for r in logs]
        details = [str(r.__dict__) for r in logs]

        with open(filename, "w", encoding="utf-8") as f:
            f.write("----- Human readable -----\n")
            [f.write(f"{logText}\n") for logText in humanReadable]
            f.write("\n----- Details -----\n")
            [f.write(f"{logDict}\n") for logDict in details]

    def exportAll(self):
        records = []
        for i in range(self._model.rowCount()):
            index = self._model.index(i, 0, QModelIndex())
            records.append(self._model.data(index, LogRecordModel.LogRecordRole))

        if records:
            if filename := self.getSaveFilename()[0]:
                self._writeLogToFile(filename, records)
        else:
            QMessageBox.warning(
                self,
                QCoreApplication.translate("Layout_LogWindow", "exportFailedDialogTitle"),
                QCoreApplication.translate("Layout_LogWindow", "exportFailedEmptyList"),
            )

    def exportSelection(self):
        if records := [
            index.data(LogRecordModel.LogRecordRole)
            for index in self.listView.selectedIndexes()
        ]:
            if filename := self.getSaveFilename()[0]:
                self._writeLogToFile(filename, records)
        else:
            QMessageBox.warning(
                self,
                QCoreApplication.translate("Layout_LogWindow", "exportFailedDialogTitle"),
                QCoreApplication.translate("Layout_LogWindow", "exportFailedNoSelection"),
            )
