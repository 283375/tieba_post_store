# Model imports
from PySide6.QtCore import QAbstractListModel, QModelIndex, QByteArray

from api.thread import LocalThread

# Delegate imports
from PySide6.QtCore import Qt, QRect, QSize
from PySide6.QtGui import QColor, QBrush, QPen, QFont, QFontMetrics
from PySide6.QtWidgets import QStyle, QStyledItemDelegate

from api.thread import getLocalThreadInfo


class Model(QAbstractListModel):
    LocalThreadRole = 20

    def __init__(self, parent=None):
        super(Model, self).__init__(parent)
        self.__threadList = []

    def rowCount(self, parent=None):
        return len(self.__threadList)

    def roleNames(self):
        return {
            **super().roleNames(),
            self.LocalThreadRole: QByteArray("LocalThread"),
        }

    def data(self, index, role=20):
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
        [self.__threadList.append({self.LocalThreadRole: t}) for t in _list]
        self.endInsertRows()


class Delegate(QStyledItemDelegate):
    xPadding = 6
    yPadding = 6
    defaultColor = (0x00, 0x90, 0xFF)

    TitleQFont = QFont()
    TitleQFont.setPixelSize(14)
    # TitleQFont.setBold(True)

    AuthorQFont = QFont()
    AuthorQFont.setPixelSize(12)

    StoreInfoQFont = QFont()
    StoreInfoQFont.setPixelSize(12)

    def __getTextAndQFonts(self, index: QModelIndex):
        threadInfo = getLocalThreadInfo(index.data(Model.LocalThreadRole))
        title = threadInfo["title"]
        author = f'{threadInfo["author"]["displayName"]} (ID {threadInfo["author"]["id"]})'
        storeInfo = threadInfo["storeDir"]

        return (
            (title, self.TitleQFont),
            (author, self.AuthorQFont),
            (storeInfo, self.StoreInfoQFont),
        )

    def paint(self, painter, option, index) -> None:
        painter.save()

        rect: QRect = option.rect
        if option.state & QStyle.State_MouseOver:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(*(self.defaultColor), 40)))
            painter.drawRect(rect.x(), rect.y(), rect.width(), rect.height())
            painter.setBrush(Qt.NoBrush)
            painter.setPen(option.palette.text().color())
        if option.state & QStyle.State_Selected:
            painter.setPen(QPen(QColor(*(self.defaultColor))))
            painter.setBrush(QBrush(QColor(*(self.defaultColor), 200)))
            painter.drawRect(rect.x(), rect.y(), rect.width(), rect.height())
            painter.setPen(Qt.white)
            painter.setBrush(Qt.NoBrush)

        def __drawText(top: int, font: QFont, text: str):
            fm = QFontMetrics(font)
            fontWidth = fm.horizontalAdvance(text, Qt.AlignLeft | Qt.AlignVCenter)
            fontRect = QRect(
                self.xPadding + rect.left(),
                rect.y() + top,
                self.xPadding + fontWidth + self.xPadding,
                fm.height(),
            )
            painter.setFont(font)
            painter.drawText(fontRect, Qt.AlignLeft | Qt.AlignVCenter, text)

        _top = self.yPadding
        for _ in self.__getTextAndQFonts(index):
            text, font = _
            __drawText(_top, font, text)
            _top += font.pixelSize() + self.yPadding

        painter.restore()

    def sizeHint(self, option, index):
        maxWidth = 0
        height = 0
        for _ in self.__getTextAndQFonts(index):
            text, font = _
            fm = QFontMetrics(font)
            height += font.pixelSize() + self.yPadding
            width = fm.horizontalAdvance(text)
            if maxWidth < width:
                maxWidth = width
        return QSize(
            maxWidth + self.xPadding * 2,
            height + self.yPadding * 2,
        )
