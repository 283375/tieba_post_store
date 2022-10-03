from PySide6.QtCore import Qt, QCoreApplication, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
)

from api.thread import LocalThread
from ui.implements.WorkDirectory import WorkDirectory
from ui.implements.ThreadList import ThreadList
from ui.implements.NewThread import NewThreadInputDialog, NewThreadConfirmDialog
from ui.implements.ThreadInfo import ThreadInfo


class EmptyPlaceholder(QWidget):
    def __init__(self, parent=None):
        super(EmptyPlaceholder, self).__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        self.label = QLabel(self)
        self.layout.addWidget(self.label)

    def retranslateUi(self, whatever=None):
        self.label.setText(
            QCoreApplication.translate("Layout_Index", "emptyPlaceholderLabel")
        )


class Ui_Layout_Index(object):
    def setupUi(self, widget: QWidget):
        self.layout = QVBoxLayout(widget)

        self.workDirectoryWidget = WorkDirectory(widget)

        self.layout.addWidget(self.workDirectoryWidget)

        self.lowerFrame = QFrame(widget)
        self.lowerFrameLayout = QHBoxLayout(self.lowerFrame)

        self.threadListFrame = QFrame(widget)
        self.threadListFrame.setFixedWidth(300)
        self.threadListFrameLayout = QVBoxLayout(self.threadListFrame)
        self.threadListFrameLayout.setAlignment(Qt.AlignCenter)

        self.threadList = ThreadList(self.threadListFrame)

        self.threadListFrameLayout.addWidget(self.threadList)

        self.newThreadButton = QPushButton(widget)
        self.newThreadButton.setIcon(QIcon(":/icons/add.svg"))

        self.newThreadInputDialog = NewThreadInputDialog(widget)
        self.newThreadConfirmDialog = NewThreadConfirmDialog(widget)

        self.threadListFrameLayout.addWidget(self.newThreadButton)

        self.lowerFrameLayout.addWidget(self.threadListFrame)

        self.threadInfoFrame = QFrame(self.lowerFrame)
        self.threadInfoFrameLayout = QVBoxLayout(self.threadInfoFrame)

        self.emptyPlaceholder = EmptyPlaceholder(widget)

        self.threadInfoFrameLayout.addWidget(self.emptyPlaceholder)

        self.lowerFrameLayout.addWidget(self.threadInfoFrame)

        self.layout.addWidget(self.lowerFrame)

        self.retranslateUi(widget)

    def retranslateUi(self, widget: QWidget = None):
        self.newThreadButton.setText(
            QCoreApplication.translate("Layout_Index", "newThreadButton")
        )

        self.workDirectoryWidget.retranslateUi()
        if self.threadInfoFrameLayout.itemAt(0) and hasattr(
            self.threadInfoFrameLayout.itemAt(0).widget(), "retranslateUi"
        ):
            self.threadInfoFrameLayout.itemAt(0).widget().retranslateUi()


class Layout_Index(QWidget, Ui_Layout_Index):
    def __init__(self, parent=None):
        super(Layout_Index, self).__init__(parent)
        self.setupUi(self)

        self.threadList.threadSelected.connect(self.updateLocalThread)

        self.newThreadButton.clicked.connect(self.newThreadInputDialog.open)
        self.newThreadInputDialog.storeRequest.connect(self.newThreadStoreRequest)

    @Slot(LocalThread)
    def updateLocalThread(self, lt: LocalThread):
        oldWidget = self.threadInfoFrameLayout.itemAt(0).widget()

        newWidget = ThreadInfo(self)
        newWidget.updateLabels(lt)

        self.threadInfoFrameLayout.replaceWidget(oldWidget, newWidget)

        oldWidget.deleteLater()

    @Slot(str)
    def newThreadStoreRequest(self, threadId: str):
        result = self.newThreadConfirmDialog.setId(threadId)
        if result:
            self.newThreadInputDialog.close()
            self.newThreadConfirmDialog.open()
        else:
            self.newThreadInputDialog.open()
