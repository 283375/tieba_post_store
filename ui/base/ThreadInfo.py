from PySide6.QtCore import Qt, QMetaObject, QCoreApplication
from PySide6.QtWidgets import QWidget, QLabel, QFormLayout


class Ui_ThreadInfo(object):
    def setupUi(self, widget: QWidget):
        self.layout = QFormLayout(widget)
        self.layout.setLabelAlignment(Qt.AlignRight)

        self.versionLabel = QLabel()
        self.versionField = QLabel()
        self.layout.addRow(self.versionLabel, self.versionField)

        self.idLabel = QLabel()
        self.idField = QLabel()
        self.layout.addRow(self.idLabel, self.idField)

        self.titleLabel = QLabel()
        self.titleField = QLabel()
        self.layout.addRow(self.titleLabel, self.titleField)

        self.forumLabel = QLabel()
        self.forumField = QLabel()
        self.layout.addRow(self.forumLabel, self.forumField)

        self.authorLabel = QLabel()
        self.authorField = QLabel(" <br /> ")
        self.layout.addRow(self.authorLabel, self.authorField)

        self.storeDirLabel = QLabel()
        self.storeDirField = QLabel()
        self.layout.addRow(self.storeDirLabel, self.storeDirField)

        self.createTimeLabel = QLabel()
        self.createTimeField = QLabel()
        self.layout.addRow(self.createTimeLabel, self.createTimeField)

        self.storeTimeLabel = QLabel()
        self.storeTimeField = QLabel()
        self.layout.addRow(self.storeTimeLabel, self.storeTimeField)

        self.updateTimeLabel = QLabel()
        self.updateTimeField = QLabel()
        self.layout.addRow(self.updateTimeLabel, self.updateTimeField)

        self.retranslateUi(widget)

        QMetaObject.connectSlotsByName(widget)

    def retranslateUi(self, widget: QWidget = None):
        self.versionLabel.setText(
            QCoreApplication.translate("ThreadInfo", "versionLabel", None)
        )
        self.idLabel.setText(QCoreApplication.translate("ThreadInfo", "idLabel", None))
        self.titleLabel.setText(
            QCoreApplication.translate("ThreadInfo", "titleLabel", None)
        )
        self.forumLabel.setText(
            QCoreApplication.translate("ThreadInfo", "forumLabel", None)
        )
        self.authorLabel.setText(
            QCoreApplication.translate("ThreadInfo", "authorLabel", None)
        )
        self.storeDirLabel.setText(
            QCoreApplication.translate("ThreadInfo", "storeDirLabel", None)
        )
        self.createTimeLabel.setText(
            QCoreApplication.translate("ThreadInfo", "createTimeLabel", None)
        )
        self.storeTimeLabel.setText(
            QCoreApplication.translate("ThreadInfo", "storeTimeLabel", None)
        )
        self.updateTimeLabel.setText(
            QCoreApplication.translate("ThreadInfo", "updateTimeLabel", None)
        )
