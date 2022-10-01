from ui.base.NewThread import Ui_NewThreadInputDialog, Ui_NewThreadConfirmDialog

import logging
from os.path import join, abspath, basename
from urllib.parse import urlparse

from PySide6.QtWidgets import QDialog, QPushButton, QMessageBox
from PySide6.QtCore import Signal, Slot

from api.thread import LightRemoteThread, LocalThread
from ui._vars import workDirectoryObject

logger = logging.getLogger("root.ui.NewThread")


class NewThreadInputDialog(QDialog, Ui_NewThreadInputDialog):
    storeRequest = Signal(str)
    # use str instead of int because
    # libshiboken: Overflow: Value 7741777833 exceeds limits of type  [signed] "int" (4bytes).

    def __init__(self, parent=None):
        super(NewThreadInputDialog, self).__init__(parent)
        self.setWindowTitle("New Thread")
        self.setupUi(self)

        self.buttonBox.accepted.connect(self.parseInput)
        self.buttonBox.rejected.connect(self.reject)

    @Slot()
    def parseInput(self):
        userInput = self.lineEdit.text()

        threadId = None
        try:  # Is input an id?
            threadId = int(userInput, 10)
        except ValueError:
            ...  # No :(

        try:  # Or maybe a url?
            threadId = int(basename(urlparse(userInput).path), 10)
        except Exception as e:  # Invalid input :(
            logger.warning(e)
            QMessageBox.critical(self, "输入无效", f'无法解析 "{userInput}"\n{str(e)}')
            self.open()

        if threadId is not None:
            self.storeRequest.emit(str(threadId))
            self.lineEdit.setText("")
            self.close()


class NewThreadConfirmDialog(QDialog, Ui_NewThreadConfirmDialog):
    def __init__(self, parent=None):
        super(NewThreadConfirmDialog, self).__init__(parent)
        self.setupUi(self)

    def setId(self, threadId: str) -> bool:
        try:
            t = LightRemoteThread(threadId)
            info = t.getThreadInfo()
            storeDir = abspath(join(workDirectoryObject.dir, info["id"]))
            self.idLabel.setText(info["id"])
            self.titleLabel.setText(f'【{info["forum"]["name"]}吧】{info["title"]}')
            self.authorLabel.setText(f'楼主 {info["author"]["displayName"]}')
            self.storeDirLabel.setText(storeDir)
            self.storeThread.setLocalThread(LocalThread(storeDir, threadId))
            return True
        except LightRemoteThread.ThreadInvalidError as e:
            logger.error(f"Invalid thread {threadId}, {str(e)}")
            QMessageBox.critical(self, "错误", f"贴子 {threadId} 无效。\n{str(e)}")
            return False


class NewThreadEntryWidget(QPushButton):
    def __init__(self):
        super().__init__()
        self.setText("+ 新存档贴子")
        self.inputDialog = NewThreadInputDialog()
        self.confirmDialog = NewThreadConfirmDialog()
        self.clicked.connect(lambda: self.inputDialog.open())
        self.inputDialog.storeRequest.connect(self.gotStoreRequest)

    def gotStoreRequest(self, threadId: str):
        if self.confirmDialog.setId(threadId):
            self.confirmDialog.show()
