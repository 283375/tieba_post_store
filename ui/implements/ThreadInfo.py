from ui.base.ThreadInfo import Ui_ThreadInfo

import time
from PySide6.QtWidgets import QWidget, QLabel

from api.thread import LocalThread, getLocalThreadInfo


def formatTime(_timestamp: int, isMilliseconds: bool = True):
    strftimeStr = "%Y-%m-%d %H:%M:%S"
    timestamp = _timestamp // 1000 if isMilliseconds else _timestamp
    return time.strftime(strftimeStr, time.localtime(timestamp))


class ThreadInfo(QWidget, Ui_ThreadInfo):
    def __init__(self, parent=None):
        super(ThreadInfo, self).__init__(parent)
        self.setupUi(self)

        self.localThread = None

    def updateLabels(self, localThread: LocalThread):
        def _setText(l: QLabel, content):
            l.setText(str(content))

        info = getLocalThreadInfo(localThread)
        _setText(self.versionField, info["__VERSION__"])
        _setText(self.idField, info["id"])
        _setText(self.titleField, info["title"])
        _setText(
            self.authorField,
            f'{info["author"]["displayName"]} <br /> (ID {info["author"]["id"]}，曾用名 {info["author"]["origName"]})',
        )
        _setText(self.forumField, f'{info["forum"]["name"]}吧')
        _setText(self.storeDirField, info["storeDir"])
        _setText(self.createTimeField, formatTime(info["createTime"]))
        _setText(self.storeTimeField, formatTime(info["storeTime"]))
        _setText(
            self.updateTimeField,
            formatTime(info["updateTime"]) if info["updateTime"] else "从未更新过",
        )
