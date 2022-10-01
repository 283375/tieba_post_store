from PySide6.QtCore import Qt, QMetaObject, QCoreApplication
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QDialogButtonBox,
    QVBoxLayout,
    QGridLayout,
)

from ui.implements.StoreThread import StoreThread


class Ui_NewThreadInputDialog(object):
    def setupUi(self, widget: QWidget):
        self.layout = QVBoxLayout(widget)

        self.tipLabel = QLabel("tip")
        self.layout.addWidget(self.tipLabel)

        self.lineEdit = QLineEdit()
        self.lineEdit.setObjectName("NTID_lineEdit")
        self.lineEdit.setClearButtonEnabled(True)
        self.lineEdit.setMinimumWidth(300)
        self.layout.addWidget(self.lineEdit)

        self.buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal,
            widget,
        )
        self.buttonBox.setObjectName("NTID_buttonBox")
        self.layout.addWidget(self.buttonBox)

        self.retranslateUi(widget)

        QMetaObject.connectSlotsByName(widget)

    def retranslateUi(self, widget: QWidget = None):
        self.tipLabel.setText(
            QCoreApplication.translate("NewThreadInputDialog", "tip", None)
        )
        self.lineEdit.setPlaceholderText(
            QCoreApplication.translate(
                "NewThreadInputDialog", "lineEditPlaceholder", None
            )
        )


class Ui_NewThreadConfirmDialog(object):
    def setupUi(self, widget: QWidget):
        self.layout = QGridLayout(widget)

        self.idLabel = QLabel()
        self.layout.addWidget(QLabel("ID"), 0, 0)
        self.layout.addWidget(self.idLabel, 0, 1)

        self.titleLabel = QLabel()
        self.layout.addWidget(QLabel("标题"), 1, 0)
        self.layout.addWidget(self.titleLabel, 1, 1)

        self.authorLabel = QLabel()
        self.layout.addWidget(QLabel("楼主"), 2, 0)
        self.layout.addWidget(self.authorLabel, 2, 1)

        self.storeDirLabel = QLabel()
        self.layout.addWidget(QLabel("将存档于"), 4, 0)
        self.layout.addWidget(self.storeDirLabel, 4, 1)

        self.layout.addWidget(QLabel("若确定，请在确认存档选项后单击“存档”按钮"), 5, 0, 1, 2)

        self.storeThread = StoreThread()
        self.layout.addWidget(self.storeThread, 6, 0, 1, 2)
