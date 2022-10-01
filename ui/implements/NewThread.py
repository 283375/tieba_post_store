from ui.base.NewThread import Ui_NewThreadInputDialog, Ui_NewThreadConfirmDialog

import logging
from os.path import join, abspath, basename
from urllib.parse import urlparse

from PySide6.QtWidgets import QDialog, QPushButton, QMessageBox
from PySide6.QtCore import Qt, Slot

from api.thread import LightRemoteThread, LocalThread
from ui._vars import workDirectoryInstance, statusBar
from .StoreThread import StoreThread

logger = logging.getLogger("root.ui.NewThread")


class NewThreadInputDialog(QDialog, Ui_NewThreadInputDialog):
    def __init__(self, parent=None):
        super(NewThreadInputDialog, self).__init__(parent)
        self.setWindowTitle("New Thread")
        self.setupUi(self)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)


class NewThreadConfirmDialog(QDialog, Ui_NewThreadConfirmDialog):
    def __init__(self, parent=None):
        super(NewThreadConfirmDialog, self).__init__(parent)
        self.setupUi(self)

    def updateId(self, threadId: int):
        self.threadId = threadId
        try:
            t = LightRemoteThread(threadId)
            self.info = t.getThreadInfo()
            self.storeDir = abspath(join(workDirectoryInstance.dir, self.info["id"]))
            self.idLabel.setText(self.info["id"])
            self.titleLabel.setText(
                f'【{self.info["forum"]["name"]}吧】{self.info["title"]}'
            )
            self.authorLabel.setText(f'楼主 {self.info["author"]["displayName"]}')
            self.storeDirLabel.setText(self.storeDir)
            self.storeThread.setLocalThread(LocalThread(self.storeDir, self.threadId))
        except LightRemoteThread.ThreadInvalidError as e:
            QMessageBox.critical(self, "错误", f"贴子 {threadId} 无效。\n详细信息: {str(e)}")
            statusBar.clearMessage()
            raise e


class NewThreadEntryWidget(QPushButton):
    def __init__(self):
        super().__init__()
        self.setText("+ 新存档贴子")
        self.inputDialog = NewThreadInputDialog(self)
        self.clicked.connect(lambda: self.inputDialog.open())
        self.inputDialog.accepted.connect(self.parseInput)
        self.confirmDialog = NewThreadConfirmDialog(self)

    @Slot()
    def parseInput(self):
        _input = self.inputDialog.lineEdit.text()

        _id = None
        try:  # _input is id?
            _id = int(_input, 10)
        except ValueError:
            ...  # No :(

        try:  # _input is url?
            _id = int(basename(urlparse(_input).path), 10)
        except Exception as e:
            logger.warning(e)
            QMessageBox.critical(self, "输入无效", f'无法解析 "{_input}"\n详细信息: {str(e)}')
            self.inputDialog.open()

        if _id is not None:
            self.confirmDialog.updateId(_id)
            self.confirmDialog.show()
