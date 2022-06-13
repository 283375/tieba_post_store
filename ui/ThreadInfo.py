import time

from PySide6.QtWidgets import QWidget, QFormLayout, QLabel
from PySide6.QtCore import Slot

from api.thread import LocalThread


class ThreadInfoWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.localThread = None

        self.idLabel = QLabel("")
        self.titleLabel = QLabel("")
        self.authorLabel = QLabel("")
        self.storeDirLabel = QLabel("")
        self.createTimeLabel = QLabel("")
        self.storedTimeLabel = QLabel("")
        self.updateTimeLabel = QLabel("")

        self.layout = QFormLayout(self)
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

        strftimeStr = "%Y-%m-%d %H:%M:%S"
        self.idLabel.setText(str(t.threadInfo["id"]))
        self.titleLabel.setText(t.threadInfo["title"])
        self.authorLabel.setText(
            f'{t.threadInfo["author"]["displayName"]} (原名 {t.threadInfo["author"]["origName"]})'
        )

        self.storeDirLabel.setText(t.storeDir)
        self.createTimeLabel.setText(
            time.strftime(strftimeStr, time.localtime(int(t.threadInfo["createTime"])))
        )
        self.storedTimeLabel.setText(
            time.strftime(
                strftimeStr,
                time.localtime(int(t.threadInfo["storeOptions"]["storeTime"]) / 1000),
            )
        )
        if t.threadInfo["storeOptions"]["updateTime"]:
            self.updateTimeLabel.setText(
                time.strftime(
                    strftimeStr,
                    time.localtime(
                        int(t.threadInfo["storeOptions"]["updateTime"]) / 1000
                    ),
                )
            )
        else:
            self.updateTimeLabel.setText("从未更新过")
