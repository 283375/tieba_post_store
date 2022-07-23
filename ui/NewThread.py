from os.path import join, abspath, basename
from urllib.parse import urlparse

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QWidget,
    QLabel,
    QVBoxLayout,
    QGridLayout,
)
from PySide6.QtCore import Qt, Signal, Slot

from api.thread import LightRemoteThread, LocalThread
from ._vars import app, workDirectoryInstance, statusBar
from .StoreThread import StoreThread


class NewThreadDialog(QDialog):
    def __init__(self, parent=None):
        super(NewThreadDialog, self).__init__(parent)
        self.setWindowTitle("New Thread")
        self.layout = QVBoxLayout(self)
        self.tipLabel = QLabel(
            "请输入贴子的 ID 或网页链接。<br />如 7741777833 或 https://tieba.baidu.com/p/7741777833"
        )
        self.edit = QLineEdit()
        self.edit.setPlaceholderText("在此处输入……")
        self.edit.setClearButtonEnabled(True)
        self.edit.setMinimumWidth(300)
        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.layout.addWidget(self.tipLabel)
        self.layout.addWidget(self.edit)
        self.layout.addWidget(self.buttonBox)


class NewThreadConfirmDialog(QDialog):
    def __init__(self, parent=None):
        super(NewThreadConfirmDialog, self).__init__(parent)
        self.storeThread = StoreThread()
        self.storeThread.setVisible(False)
        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.store)
        self.buttonBox.rejected.connect(self.reject)
        self.layout = QGridLayout(self)
        self.idLabel = QLabel()
        self.titleLabel = QLabel()
        self.authorLabel = QLabel()
        self.storeDirLabel = QLabel()
        self.layout.addWidget(QLabel("ID"), 0, 0)
        self.layout.addWidget(self.idLabel, 0, 1)
        self.layout.addWidget(QLabel("标题"), 1, 0)
        self.layout.addWidget(self.titleLabel, 1, 1)
        self.layout.addWidget(QLabel("楼主"), 2, 0)
        self.layout.addWidget(self.authorLabel, 2, 1)
        self.layout.addWidget(QLabel("将存档于"), 4, 0)
        self.layout.addWidget(self.storeDirLabel, 4, 1)
        self.layout.addWidget(QLabel("确定吗？"), 5, 0, 1, 2)
        self.layout.addWidget(self.buttonBox, 6, 0, 1, 2)
        self.layout.addWidget(self.storeThread, 7, 0, 1, 2)

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
        except LightRemoteThread.ThreadInvalidError as e:
            QMessageBox.critical(self, "错误", f"贴子 {threadId} 无效。\n详细信息: {str(e)}")
            statusBar.clearMessage()
            raise e

    def store(self):
        lt = LocalThread(self.storeDir, self.threadId)
        lt.updateStoreOptions({"assets": True, "portraits": True})
        self.storeThread.storeComplete.connect(self.accept)
        self.storeThread.setLocalThread(lt)
        self.storeThread.setVisible(True)
        self.storeThread.storeStart()


class NewThreadWidget(QPushButton):
    def __init__(self):
        super().__init__()
        self.setText("+ 新存档贴子")
        self.dialog = NewThreadDialog(self)
        self.clicked.connect(self.showDialog)
        self.dialog.finished.connect(self.dialogFinished)
        self.confirmDialog = NewThreadConfirmDialog(self)

    @Slot()
    def showDialog(self):
        self.dialog.open()

    @Slot()
    def dialogFinished(self, signal: int):
        if signal != QDialog.Accepted:
            return

        _input = self.dialog.edit.text()
        try:
            _id = int(_input, 10)  # _input is id?
        except ValueError:
            try:
                _id = int(basename(urlparse(_input).path))  # _input is url?
            except Exception as e:
                _id = None
                QMessageBox.critical(self, "输入无效", f'无法解析 "{_input}"\n详细信息: {str(e)}')
                self.dialog.open()
                raise e

        self.confirmDialog.updateId(_id)
        self.confirmDialog.open()
