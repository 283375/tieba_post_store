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
        self.idField = QLabel()
        self.layout.addWidget(self.idLabel, 0, 0)
        self.layout.addWidget(self.idField, 0, 1)

        self.titleLabel = QLabel()
        self.titleField = QLabel()
        self.layout.addWidget(self.titleLabel, 1, 0)
        self.layout.addWidget(self.titleField, 1, 1)

        self.authorLabel = QLabel()
        self.authorField = QLabel()
        self.layout.addWidget(self.authorLabel, 2, 0)
        self.layout.addWidget(self.authorField, 2, 1)

        self.storeDirLabel = QLabel()
        self.storeDirField = QLabel()
        self.layout.addWidget(self.storeDirLabel, 4, 0)
        self.layout.addWidget(self.storeDirField, 4, 1)

        self.confirmLabel = QLabel()
        self.layout.addWidget(self.confirmLabel, 5, 0, 1, 2)

        self.storeThread = StoreThread()
        self.layout.addWidget(self.storeThread, 6, 0, 1, 2)

        self.retranslateUi(widget)

        QMetaObject.connectSlotsByName(widget)

    def retranslateUi(self, widget: QWidget = None):
        self.idLabel.setText(
            QCoreApplication.translate("NewThreadConfirmDialog", "idLabel", None)
        )
        self.titleLabel.setText(
            QCoreApplication.translate("NewThreadConfirmDialog", "titleLabel", None)
        )
        self.authorLabel.setText(
            QCoreApplication.translate("NewThreadConfirmDialog", "authorLabel", None)
        )
        self.storeDirLabel.setText(
            QCoreApplication.translate("NewThreadConfirmDialog", "storeDirLabel", None)
        )
        self.confirmLabel.setText(
            QCoreApplication.translate("NewThreadConfirmDialog", "confirmLabel", None)
        )
