from PySide6.QtCore import QMetaObject, QCoreApplication
from PySide6.QtWidgets import (
    QWidget,
    QGroupBox,
    QPushButton,
    QFileDialog,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
)


class Ui_WorkDirectory(object):
    def setupUi(self, widget: QWidget):
        if not widget.objectName():
            widget.setObjectName("WorkDirectory")

        self.layout = QVBoxLayout(widget)

        self.groupBox = QGroupBox()

        self.innerLayout = QHBoxLayout(self.groupBox)

        self.changeDirButton = QPushButton(widget)
        self.changeDirButton.setObjectName("changeDirButton")

        self.innerLayout.addWidget(self.changeDirButton)

        self.changeDirFileDialog = QFileDialog(widget)
        self.changeDirFileDialog.setFileMode(QFileDialog.Directory)
        self.changeDirFileDialog.setOption(QFileDialog.ShowDirsOnly)

        self.dirLabel = QLabel(widget)
        self.sizePolicy1 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.sizePolicy1.setHorizontalStretch(1)
        self.dirLabel.setSizePolicy(self.sizePolicy1)

        self.innerLayout.addWidget(self.dirLabel)

        self.layout.addWidget(self.groupBox)

        self.retranslateUi(widget)

        QMetaObject.connectSlotsByName(widget)

    def retranslateUi(self, widget: QWidget = None):
        self.groupBox.setTitle(
            QCoreApplication.translate("WorkDirectory", "title", None)
        )
        self.changeDirButton.setText(
            QCoreApplication.translate("WorkDirectory", "changeDirButton", None)
        )
