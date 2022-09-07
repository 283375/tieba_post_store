from typing import Any, Union
from PySide6.QtCore import QPersistentModelIndex, QSize
from PySide6.QtWidgets import QStyleOptionViewItem
from PySide6.QtGui import QPainter

from PySide6.QtWidgets import QWidget, QListView, QLabel, QStackedLayout, QVBoxLayout, QStyledItemDelegate, QStyle
from PySide6.QtCore import Qt, QRect, QAbstractListModel, QModelIndex, QByteArray, QThread, Signal, Slot
from PySide6.QtGui import QPen, QFont, QFontMetrics, QColor, QBrush

from .ThreadInfo import ThreadInfoWidget
from ._vars import app, statusBar
from api.workDirectory import scanDirectory
from api.thread import LocalThread, getLocalThreadInfo


class ThreadListModel(QAbstractListModel):
    __threadList: list[dict[int, Any]] = []
    LocalThreadRole = 20
    TitleTextRole = 21
    AuthorTextRole = 22
    StoreInfoTextRole = 23
    TitleTextQFont = QFont()
    TitleTextQFont.setPixelSize(14)
    # TitleTextQFont.setBold(True)
    TitleTextQFontRole = 31
    AuthorTextQFont = QFont()
    AuthorTextQFont.setPixelSize(12)
    AuthorTextQFontRole = 32
    StoreInfoTextQFont = QFont()
    StoreInfoTextQFont.setPixelSize(12)
    StoreInfoTextQFontRole = 33

    def __init__(self, parent=None):
        super(ThreadListModel, self).__init__(parent)

    def rowCount(self, parent=None) -> int:
        return len(self.__threadList)

    def roleNames(self) -> dict[int, QByteArray]:
        return {**super().roleNames(), self.LocalThreadRole: QByteArray(b"LocalThread")}

    def data(
        self,
        index: Union[QModelIndex, QPersistentModelIndex],
        role: int = 20,
    ):
        if not index.isValid() or index.row() >= self.rowCount():
            return None
        return self.__threadList[index.row()].get(role)

    def updateList(self, _list: list[LocalThread]):
        _totalRow = self.rowCount()
        self.beginRemoveRows(QModelIndex(), 0, _totalRow - 1)
        self.__threadList.clear()
        self.endRemoveRows()

        _totalRow = len(_list)
        self.beginInsertRows(QModelIndex(), 0, _totalRow - 1)
        for t in _list:
            info = getLocalThreadInfo(t)
            self.__threadList.append(
                {
                    self.LocalThreadRole: t,
                    self.TitleTextRole: f'{info["title"]} (ID: {info["threadId"]})',
                    self.AuthorTextRole: f'楼主 {info["author"]["displayName"]} (曾用名 {info["author"]["origName"]})',
                    self.StoreInfoTextRole: f'存档于 {info["storeDir"]}',
                    self.TitleTextQFontRole: self.TitleTextQFont,
                    self.AuthorTextQFontRole: self.AuthorTextQFont,
                    self.StoreInfoTextQFontRole: self.StoreInfoTextQFont,
                }
            )
        self.endInsertRows()

    def _allLocalThreads(self):
        return [t[self.LocalThreadRole] for t in self.__threadList]


class LocalThreadDisplayDelegate(QStyledItemDelegate):
    horizontalPadding = 6
    verticalPadding = 6
    borderBaseColor = (0x58, 0xB6, 0xFB)
    fillColor = (0x4F, 0x41, 0xC2)

    def __getTextAndQFonts(self, index: Union[QModelIndex, QPersistentModelIndex]):
        model = ThreadListModel
        return [
            [index.data(model.TitleTextRole), index.data(model.TitleTextQFontRole)],
            [index.data(model.AuthorTextRole), index.data(model.AuthorTextQFontRole)],
            [index.data(model.StoreInfoTextRole), index.data(model.StoreInfoTextQFontRole)],
        ]

    def paint(
        self, painter: QPainter, option: QStyleOptionViewItem, index: Union[QModelIndex, QPersistentModelIndex]
    ) -> None:
        painter.save()

        rect: QRect = option.rect
        if option.state & QStyle.State_MouseOver:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(*(self.fillColor), 50)))  # fillBrush
            painter.drawRect(rect.x(), rect.y(), rect.width(), rect.height())
            painter.setBrush(Qt.NoBrush)
            painter.setPen(option.palette.text().color())
        if option.state & QStyle.State_Selected:
            painter.setPen(QPen(QColor(*(self.borderBaseColor))))  # borderPen
            painter.setBrush(QBrush(QColor(*(self.fillColor), 200)))  # fillBrush
            painter.drawRect(rect.x() + 1, rect.y(), rect.width(), rect.height())
            painter.setPen(Qt.white)
            painter.setBrush(Qt.NoBrush)

        def __drawText(top: int, font: QFont, text: str):
            fm = QFontMetrics(font)
            fontWidth = fm.horizontalAdvance(text, Qt.AlignLeft | Qt.AlignVCenter)
            __rect = QRect(
                self.horizontalPadding + rect.left(),
                rect.y() + top,
                self.horizontalPadding + fontWidth + self.horizontalPadding,
                fm.height(),
            )
            painter.setFont(font)
            painter.drawText(__rect, Qt.AlignLeft | Qt.AlignVCenter, text)

        _top = self.verticalPadding
        for _ in self.__getTextAndQFonts(index):
            text, font = _
            __drawText(_top, font, text)
            _top += font.pixelSize() + self.verticalPadding

        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index: Union[QModelIndex, QPersistentModelIndex]) -> QSize:
        maxWidth = 0
        height = 0
        for _ in self.__getTextAndQFonts(index):
            text, font = _
            fm = QFontMetrics(font)
            height += font.pixelSize() + self.verticalPadding
            width = fm.horizontalAdvance(text)
            if maxWidth < width:
                maxWidth = width
        return QSize(maxWidth + self.horizontalPadding * 2, height + self.verticalPadding * 2)


class ScanDirectoryThread(QThread):
    scanningDir = Signal(str)
    scanComplete = Signal(list)

    def __init__(self, dir: str = "", parent=None):
        super(ScanDirectoryThread, self).__init__(parent)
        self.dir = dir

    def run(self):
        savedThreads = []

        for dir, t in scanDirectory(self.dir):
            self.scanningDir.emit(dir)
            if type(t) == LocalThread and t.isValid:
                savedThreads.append(t)

        self.scanComplete.emit(savedThreads)


class ThreadListWidget(QListView):
    listUpdated = Signal(list)
    selectedIndexChanged = Signal(QModelIndex)

    def __init__(self, parent=None):
        super(ThreadListWidget, self).__init__(parent)
        self.setSelectionMode(QListView.SingleSelection)
        self.setSelectionRectVisible(True)
        self.setDragEnabled(False)
        self.setAcceptDrops(False)
        self.lastDirectory = None

        self._model = ThreadListModel()
        self.setModel(self._model)
        self.setItemDelegate(LocalThreadDisplayDelegate())

        self.doubleClicked.connect(self.__changeSelectedIndex)

    @Slot(str)
    def workDirectoryChanged(self, dir: str):
        self.lastDirectory = dir
        self.startScan(dir)

    def startScan(self, dir: str):
        self._thread = ScanDirectoryThread(dir)
        _showScanningDir = lambda dir: statusBar.showMessage(f"正在检测 {dir}")
        self._thread.scanningDir.connect(_showScanningDir)
        self._thread.scanComplete.connect(self.scanComplete)
        self._thread.start()

    @Slot(list)
    def scanComplete(self, savedThreads: list[LocalThread]):
        statusBar.showMessage(f"在 {self.lastDirectory} 中找到了 {len(savedThreads)} 个有效存档目录", 10000)
        self._model.updateList(savedThreads)
        self.listUpdated.emit(savedThreads)

    @Slot()
    def refreshDirectory(self):
        self.workDirectoryChanged(self.lastDirectory)

    @Slot(QModelIndex)
    def __changeSelectedIndex(self, index: QModelIndex):
        self.selectedIndexChanged.emit(index)


class ThreadInfoStackedWidget(QWidget):
    emptyWidget = QWidget()
    emptyWidget.layout = QVBoxLayout(emptyWidget)
    emptyWidget.layout.addWidget(QLabel("未找到任何存档"))
    emptyWidget.layout.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

    placeholderWidget = QWidget()
    placeholderWidget.layout = QVBoxLayout(placeholderWidget)
    placeholderWidget.setVisible(False)

    def __init__(self, parent=None):
        super(ThreadInfoStackedWidget, self).__init__(parent)
        self.layout: QStackedLayout = QStackedLayout(self)
        self.layout.insertWidget(0, self.emptyWidget)

    @Slot(list)
    def updateList(self, _list: list[LocalThread]) -> None:
        for i in range(self.layout.count()):
            self.layout.insertWidget(i, self.placeholderWidget)

        for i, lt in enumerate(_list):
            widget = ThreadInfoWidget()
            widget.setLocalThread(lt)
            self.layout.insertWidget(i, widget)

    @Slot(QModelIndex)
    def setCurrentIndex(self, i: QModelIndex):
        self.layout.setCurrentIndex(i.row())
