from PySide6.QtCore import (
    Qt,
    QCoreApplication,
    QMetaObject,
    QEvent,
    QFileInfo,
    QDir,
    Slot,
)
from PySide6.QtGui import QColor, QPalette, QIcon, QValidator
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QLineEdit,
    QCompleter,
    QPushButton,
    QFileDialog,
    QHBoxLayout,
    QFileSystemModel,
)


class Ui_Comp_DirectoryLineEdit(object):
    def setupUi(self, frame: QFrame):
        self.layout = QHBoxLayout(frame)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.lineEdit = QLineEdit(frame)
        self.lineEdit.setObjectName("DLE_LineEdit")

        self.layout.addWidget(self.lineEdit)
        self.layout.setStretch(0, 1)

        self.changeDirButton = QPushButton(frame)
        self.changeDirButton.setIcon(QIcon(":/icons/folder.svg"))
        self.layout.addWidget(self.changeDirButton)

        self.applyButton = QPushButton(frame)
        self.applyButton.setIcon(QIcon(":/icons/check.svg"))
        self.layout.addWidget(self.applyButton)

        self.fileDialog = QFileDialog(frame)

        self.retranslateUi()

        QMetaObject.connectSlotsByName(frame)

    def retranslateUi(self):
        self.changeDirButton.setText(
            QCoreApplication.translate("Comp_DirectoryLineEdit", "changeDirButton")
        )
        self.applyButton.setText(
            QCoreApplication.translate("Comp_DirectoryLineEdit", "applyButton")
        )


class DirectoryLineEditValidator(QValidator):
    def __init__(self, parent=None):
        super(DirectoryLineEditValidator, self).__init__(parent)
        self.acceptNonExistingDir = False

    def validate(self, inputStr: str, pos: int = 0) -> QValidator.State:
        fileInfo = QFileInfo(inputStr)

        # isDir = fileInfo.isDir()
        exists = fileInfo.exists()

        if exists or self.acceptNonExistingDir:
            return QValidator.Acceptable
        else:
            return QValidator.Intermediate


class DirectoryLineEdit(QFrame, Ui_Comp_DirectoryLineEdit):
    IntermediateColor = QColor("#f3d19e")
    InvalidColor = QColor("#fab6b6")

    def __init__(self, parent: QWidget = None):
        super(DirectoryLineEdit, self).__init__(parent)
        self.setupUi(self)

        self.fileSystemModel = QFileSystemModel()
        self.fileSystemModel.setRootPath("/")
        self.fileSystemModel.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot)
        self.completer = QCompleter(self.fileSystemModel, self)
        self.completer.setMaxVisibleItems(5)
        self.lineEdit.setCompleter(self.completer)

        self.validator = DirectoryLineEditValidator(self.lineEdit)
        self.lineEdit.setValidator(self.validator)

        self.lineEdit.textChanged.connect(self.updateTooltip)

    @Slot()
    def on_DLE_LineEdit_editingFinished(self):
        pass

    def updateTooltip(self):
        def __show(state: QValidator.State, text: str = ""):
            palette = QPalette()
            if state == QValidator.Acceptable:
                pass
            elif state == QValidator.Intermediate:
                palette.setColor(QPalette.Window, self.IntermediateColor)
                palette.setColor(QPalette.Base, self.IntermediateColor)
                palette.setColor(QPalette.Button, self.IntermediateColor)
            elif state == QValidator.Invalid:
                palette.setColor(QPalette.Base, self.InvalidColor)
                palette.setColor(QPalette.Button, self.InvalidColor)
                palette.setColor(QPalette.Window, self.InvalidColor)

            self.lineEdit.setPalette(palette)
            self.applyButton.setPalette(palette)
            self.applyButton.setEnabled(state != QValidator.Invalid)
            self.applyButton.setToolTip(text)

        fileInfo = QFileInfo(self.lineEdit.text())

        isDir = fileInfo.isDir()
        exists = fileInfo.exists()
        readable = fileInfo.isReadable()

        # fmt: off
        if (not exists and self.validator.acceptNonExistingDir) or (exists and readable):
            __show(QValidator.Acceptable, "")
        elif exists and not isDir:
            __show(
                QValidator.Invalid,
                QCoreApplication.translate("Comp_DirectoryLineEdit", "applyButtonTooltip_Invalid", "notDir"),
            )
        elif not exists:
            __show(
                QValidator.Invalid,
                QCoreApplication.translate("Comp_DirectoryLineEdit", "applyButtonTooltip_Invalid", "nonExistingDir"),
            )
        else:
            __show(
                QValidator.Intermediate,
                QCoreApplication.translate("Comp_DirectoryLineEdit", "applyButtonTooltip_Intermediate", "dirNotReadable"),
            )
        # fmt: on

    def changeEvent(self, e: QEvent):
        if e.type() == QEvent.LanguageChange:
            self.retranslateUi()

        return super().changeEvent(e)
