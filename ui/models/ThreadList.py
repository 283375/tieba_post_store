# Model imports
from PySide6.QtCore import QAbstractListModel, QModelIndex, QByteArray

from api.thread import LocalThread

# Delegate imports
from PySide6.QtCore import Qt, QPoint
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

    def __getTextAndQFonts(self, index: QModelIndex) -> tuple[tuple[str, QFont]]:
        threadInfo = getLocalThreadInfo(index.data(Model.LocalThreadRole))
        title = threadInfo["title"]
        author = (
            f'{threadInfo["author"]["displayName"]} (ID {threadInfo["author"]["id"]})'
        )
        storeInfo = threadInfo["storeDir"]

        return (
            (title, self.TitleQFont),
            (author, self.AuthorQFont),
            (storeInfo, self.StoreInfoQFont),
        )

    def paint(self, painter, option, index) -> None:
        # Background painting
        painter.save()
        painter.setPen(Qt.NoPen)  # No border
        if option.state & QStyle.State_MouseOver:
            painter.fillRect(option.rect, QBrush(QColor(*(self.defaultColor), 40)))
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, QBrush(QColor(*(self.defaultColor), 200)))
        painter.restore()

        # Text painting
        painter.save()
        if option.state & QStyle.State_Selected:
            painter.setPen(QPen("#ffffff"))

        def __drawText(topOffset: int, font: QFont, text: str):
            painter.setFont(font)
            fm = QFontMetrics(font)
            point = QPoint(
                self.xPadding + option.rect.left(),
                topOffset + option.rect.y() + fm.ascent(),
            )
            painter.drawText(point, text)

        topOffset = self.yPadding
        for _ in self.__getTextAndQFonts(index):
            text, font = _
            __drawText(topOffset, font, text)
            topOffset += font.pixelSize() + self.yPadding

        painter.restore()

    def sizeHint(self, option, index):
        textAndQFonts = self.__getTextAndQFonts(index)

        widths = []
        for _tuple in textAndQFonts:
            text, font = _tuple
            fm = QFontMetrics(font)
            widths.append(fm.horizontalAdvance(text))

        totalHeight = sum(
            [_tuple[1].pixelSize() for _tuple in textAndQFonts]
            + [self.yPadding * (2 + len(textAndQFonts))]
        )

        size = super().sizeHint(option, index)
        size.setWidth(max(widths) + self.xPadding * 2)
        size.setHeight(totalHeight)
        return size
