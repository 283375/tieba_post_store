from PySide6.QtCore import Qt, QMetaObject, QCoreApplication
from PySide6.QtWidgets import (
    QWidget,
    QGroupBox,
    QCheckBox,
    QProgressBar,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
)


class Ui_StoreThread(object):
    def setupUi(self, widget: QWidget):
        self.localThread = None

        self.layout = QVBoxLayout(widget)

        self.storeOptionsGroupBox = QGroupBox()
        self.groupBoxLayout = QHBoxLayout(self.storeOptionsGroupBox)

        self.lzOnlyCheckBox = QCheckBox()
        self.assetsCheckBox = QCheckBox()
        self.portraitsCheckBox = QCheckBox()

        self.groupBoxLayout.addWidget(self.lzOnlyCheckBox)
        self.groupBoxLayout.addWidget(self.assetsCheckBox)
        self.groupBoxLayout.addWidget(self.portraitsCheckBox)

        self.layout.addWidget(self.storeOptionsGroupBox)

        self.progressBar1 = QProgressBar()
        self.progressBar2 = QProgressBar()
        self.progressBar3 = QProgressBar()
        self.progressBar1.setAlignment(Qt.AlignVCenter)
        self.progressBar2.setAlignment(Qt.AlignVCenter)
        self.progressBar3.setAlignment(Qt.AlignVCenter)

        self.layout.addWidget(self.progressBar1)
        self.layout.addWidget(self.progressBar2)
        self.layout.addWidget(self.progressBar3)

        self.lowerWrapper = QHBoxLayout()

        self.startButton = QPushButton()
        self.startButton.setObjectName("ST_startButton")

        self.lowerWrapper.addWidget(self.startButton)

        self.abortButton = QPushButton()
        self.abortButton.setObjectName("ST_abortButton")
        self.abortButton.setEnabled(False)

        self.lowerWrapper.addWidget(self.abortButton)

        self.label = QLabel()
        self.sizePolicy1 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self.sizePolicy1.setHorizontalStretch(1)
        self.label.setSizePolicy(self.sizePolicy1)

        self.lowerWrapper.addWidget(self.label)

        self.layout.addLayout(self.lowerWrapper)

        self.retranslateUi(widget)

        QMetaObject.connectSlotsByName(widget)

    def retranslateUi(self, widget: QWidget = None):
        self.lzOnlyCheckBox.setText(
            QCoreApplication.translate("StoreThread", "lzOnlyCheckBox", None)
        )
        self.assetsCheckBox.setText(
            QCoreApplication.translate("StoreThread", "assetsCheckBox", None)
        )
        self.portraitsCheckBox.setText(
            QCoreApplication.translate("StoreThread", "portraitsCheckBox", None)
        )
        self.storeOptionsGroupBox.setTitle(
            QCoreApplication.translate("StoreThread", "storeOptionsGroupBox", None)
        )
        if self.localThread and self.localThread.isValid:
            self.startButton.setText(
                QCoreApplication.translate("StoreThread", "startButton", "threadValid")
            )
        else:
            self.startButton.setText(
                QCoreApplication.translate("StoreThread", "startButton", "threadInvalid")
            )
        self.abortButton.setText(
            QCoreApplication.translate("StoreThread", "abortButton", None)
        )
