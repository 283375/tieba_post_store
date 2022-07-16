import time

from PySide6.QtWidgets import QWidget, QFormLayout, QLabel
from PySide6.QtCore import Slot

from api.thread import LocalThread


def getInfo(t: LocalThread) -> dict:
    ver = t.storeOptions["__VERSION__"]
    info = {
        "__VERSION__": ver,
        "threadId": None,
        "title": None,
        "author": {
            "id": None,
            "displayName": None,
            "origName": None,
        },
        "storeDir": None,
        "createTime": None,
        "storeTime": None,
        "updateTime": None,
    }
    # if ver == 1: 胎死腹中的破烂版本，没人用得着的
    if ver == 2:
        info["threadId"] = t.threadInfo["id"]
        info["title"] = t.threadInfo["title"]
        info["author"] = t.threadInfo["author"]
        info["storeDir"] = t.storeDir
        info["createTime"] = int(t.threadInfo["createTime"]) * 1000
        info["storeTime"] = t.updateInfo["storeTime"]
        info["updateTime"] = t.updateInfo["updateTime"]
    # elif ver == 3: 也许用得着，谁知道呢
    return info


def formatTime(_timestamp: int, isMilliseconds: bool = True):
    strftimeStr = "%Y-%m-%d %H:%M:%S"
    timestamp = _timestamp // 1000 if isMilliseconds else _timestamp
    return time.strftime(strftimeStr, time.localtime(timestamp))


class ThreadInfoWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.localThread = None

        self.versionLabel = QLabel("")
        self.idLabel = QLabel("")
        self.titleLabel = QLabel("")
        self.authorLabel = QLabel(" <br /> ")
        self.storeDirLabel = QLabel("")
        self.createTimeLabel = QLabel("")
        self.storedTimeLabel = QLabel("")
        self.updateTimeLabel = QLabel("")

        self.layout = QFormLayout(self)
        self.layout.addRow("存档版本", self.versionLabel)
        self.layout.addRow("贴子 ID", self.idLabel)
        self.layout.addRow("标题", self.titleLabel)
        self.layout.addRow("作者", self.authorLabel)
        self.layout.addRow("存档位置", self.storeDirLabel)
        self.layout.addRow("贴子发布时间", self.createTimeLabel)
        self.layout.addRow("存档时间", self.storedTimeLabel)
        self.layout.addRow("最后更新时间", self.updateTimeLabel)

    @Slot(LocalThread)
    def updateLocalThread(self, t: LocalThread):
        self.localThread = t
        self.updateLabels()

    def updateLabels(self):
        def _setText(l: QLabel, content):
            l.setText(str(content))

        info = getInfo(self.localThread)
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
