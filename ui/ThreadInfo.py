import time

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QSpacerItem,
    QFormLayout,
    QVBoxLayout,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Slot

from api.thread import LocalThread, getLocalThreadInfo
from .StoreThread import StoreThread


def formatTime(_timestamp: int, isMilliseconds: bool = True):
    strftimeStr = "%Y-%m-%d %H:%M:%S"
    timestamp = _timestamp // 1000 if isMilliseconds else _timestamp
    return time.strftime(strftimeStr, time.localtime(timestamp))


class ThreadInfoWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.localThread = None

        self.infoFormWrapper = QFormLayout()
        self.versionLabel = QLabel("")
        self.idLabel = QLabel("")
        self.titleLabel = QLabel("")
        self.authorLabel = QLabel(" <br /> ")
        self.storeDirLabel = QLabel("")
        self.createTimeLabel = QLabel("")
        self.storedTimeLabel = QLabel("")
        self.updateTimeLabel = QLabel("")
        self.infoFormWrapper.addRow("存档版本", self.versionLabel)
        self.infoFormWrapper.addRow("贴子 ID", self.idLabel)
        self.infoFormWrapper.addRow("标题", self.titleLabel)
        self.infoFormWrapper.addRow("楼主", self.authorLabel)
        self.infoFormWrapper.addRow("存档于", self.storeDirLabel)
        self.infoFormWrapper.addRow("贴子发布时间", self.createTimeLabel)
        self.infoFormWrapper.addRow("存档时间", self.storedTimeLabel)
        self.infoFormWrapper.addRow("最后更新时间", self.updateTimeLabel)

        self.vSpacer = QSpacerItem(1, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.storeThread = StoreThread()

        self.layout = QVBoxLayout(self)
        self.layout.addLayout(self.infoFormWrapper)
        self.layout.addSpacerItem(self.vSpacer)
        self.layout.addWidget(self.storeThread)

    @Slot(LocalThread)
    def setLocalThread(self, t: LocalThread):
        self.localThread = t
        self.storeThread.setLocalThread(t)
        self.updateLabels()

    def updateLabels(self):
        def _setText(l: QLabel, content):
            l.setText(str(content))

        info = getLocalThreadInfo(self.localThread)
        _setText(self.versionLabel, info["__VERSION__"])
        _setText(self.idLabel, info["threadId"])
        _setText(self.titleLabel, info["title"])
        _setText(
            self.authorLabel,
            f'{info["author"]["displayName"]} <br /> (ID {info["author"]["id"]}，曾用名 {info["author"]["origName"]})',
        )
        _setText(self.storeDirLabel, info["storeDir"])
        _setText(self.createTimeLabel, formatTime(info["createTime"]))
        _setText(self.storedTimeLabel, formatTime(info["storeTime"]))
        _setText(
            self.updateTimeLabel,
            formatTime(info["updateTime"]) if info["updateTime"] else "从未更新过",
        )
