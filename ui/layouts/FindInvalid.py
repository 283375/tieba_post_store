from os.path import basename, abspath
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QPushButton,
    QListView,
    QGroupBox,
    QCheckBox,
    QMessageBox,
    QVBoxLayout,
    QHBoxLayout,
)
from PySide6.QtCore import (
    QStringListModel,
    QModelIndex,
    QItemSelectionModel,
    QFile,
    QCoreApplication,
    QMetaObject,
)

from api.thread import LocalThread
from ui.sharedVars import workDirectoryObject
from ui.implements.WorkDirectory import WorkDirectory


class Ui_Layout_FindInvalid(object):
    def setupUi(self, widget: QWidget):
        self.layout = QVBoxLayout(widget)

        self.workDirectoryWidget = WorkDirectory()
        self.layout.addWidget(self.workDirectoryWidget)

        self.deleteFrame = QFrame(widget)
        self.deleteFrameLayout = QHBoxLayout(self.deleteFrame)

        self.deleteFrame_RecycleCheckBox = QCheckBox(widget)
        self.deleteFrameLayout.addWidget(self.deleteFrame_RecycleCheckBox)

        self.deleteFrame_delete = QPushButton(widget)
        self.deleteFrameLayout.addWidget(self.deleteFrame_delete)

        self.layout.addWidget(self.deleteFrame)

        self.quickActionsGroupBox = QGroupBox(widget)
        self.quickActionsLayout = QHBoxLayout(self.quickActionsGroupBox)

        self.quickActions_SelectAll = QPushButton(self.quickActionsGroupBox)
        self.quickActionsLayout.addWidget(self.quickActions_SelectAll)

        self.quickActions_DeselectAll = QPushButton(self.quickActionsGroupBox)
        self.quickActionsLayout.addWidget(self.quickActions_DeselectAll)

        self.quickActions_InvertSelection = QPushButton(self.quickActionsGroupBox)
        self.quickActionsLayout.addWidget(self.quickActions_InvertSelection)

        self.layout.addWidget(self.quickActionsGroupBox)

        self.listView = QListView(widget)
        self.listView.setSelectionMode(QListView.SelectionMode.MultiSelection)

        self.layout.addWidget(self.listView)

        self.retranslateUi(widget)

        QMetaObject.connectSlotsByName(widget)

    def retranslateUi(self, widget: QWidget = None):
        self.deleteFrame_RecycleCheckBox.setText(
            QCoreApplication.translate("Layout_FindInvalid", "recycleCheckBox")
        )
        self.deleteFrame_delete.setText(
            QCoreApplication.translate("Layout_FindInvalid", "deleteButton")
        )
        self.quickActionsGroupBox.setTitle(
            QCoreApplication.translate("Layout_FindInvalid", "quickActionsTitle")
        )
        self.quickActions_SelectAll.setText(
            QCoreApplication.translate("Layout_FindInvalid", "quickActions_SelectAll")
        )
        self.quickActions_DeselectAll.setText(
            QCoreApplication.translate("Layout_FindInvalid", "quickActions_DeselectAll")
        )
        self.quickActions_InvertSelection.setText(
            QCoreApplication.translate(
                "Layout_FindInvalid", "quickActions_InvertSelection"
            )
        )


class Layout_FindInvalid(QWidget, Ui_Layout_FindInvalid):
    def __init__(self, parent=None):
        super(Layout_FindInvalid, self).__init__(parent)

        self.setupUi(self)

        self._model = QStringListModel()
        self.listView.setModel(self._model)

        self.quickActions_SelectAll.clicked.connect(lambda: self.quickSelect("all"))
        self.quickActions_DeselectAll.clicked.connect(lambda: self.quickSelect("none"))
        self.quickActions_InvertSelection.clicked.connect(
            lambda: self.quickSelect("invert")
        )

        self.deleteFrame_delete.clicked.connect(self.deleteConfirm)

        workDirectoryObject.dirScanResult.connect(self.scanComplete)

    def quickSelect(self, action: str):
        setSelectState = lambda index, const: self.listView.selectionModel().select(
            index, const
        )

        for i in range(self._model.rowCount()):
            index = self._model.index(i, 0, QModelIndex())
            if action == "all":
                setSelectState(index, QItemSelectionModel.Select)
            elif action == "none":
                setSelectState(index, QItemSelectionModel.Deselect)
            elif action == "invert":
                setSelectState(index, QItemSelectionModel.Toggle)

    def scanComplete(self, result: list[tuple[str, LocalThread | None]]):
        invalidDirs = [dir for dir, t in result if t is None]
        self._model.setStringList(invalidDirs)
        self.quickSelect("all")

    def deleteConfirm(self):
        files = [self._model.data(index) for index in self.listView.selectedIndexes()]

        if self.deleteFrame_RecycleCheckBox.isChecked():
            message = QCoreApplication.translate(
                "Layout_FindInvalid", "deleteConfirmDialogMessage", "recycle"
            )
        else:
            message = QCoreApplication.translate(
                "Layout_FindInvalid", "deleteConfirmDialogMessage", "directDelete"
            )

        message = message.format("<br>".join(basename(file) for file in files))
        result = QMessageBox.question(
            self,
            QCoreApplication.translate("Layout_FindInvalid", "deleteConfirmDialogTitle"),
            message,
        )
        if result == QMessageBox.Yes:
            self.delete(files)

    def delete(self, files: list[str]):
        for file in files:
            fileAbsPath = abspath(file)
            file = QFile(fileAbsPath)
            if file.exists():
                if self.deleteFrame_RecycleCheckBox.isChecked():
                    deleteResult = file.moveToTrash()
                else:
                    deleteResult = file.remove()

                if deleteResult == False:
                    QMessageBox.warning(
                        self,
                        QCoreApplication.translate(
                            "Layout_FindInvalid", "deleteFailedDialogTitle"
                        ),
                        # fmt: off
                        QCoreApplication.translate(
                            "Layout_FindInvalid",
                            "deleteFailedDialogMessage",
                            "deleteFailed" 
                            # no trailing comma because lupdate will treat this line as a "numerus" translation key.
                        ).format(fileAbsPath)
                        # fmt: on
                    )
                    continue
            else:
                QMessageBox.warning(
                    self,
                    QCoreApplication.translate(
                        "Layout_FindInvalid", "deleteFailedDialogTitle"
                    ),
                    QCoreApplication.translate(
                        "Layout_FindInvalid", "deleteFailedDialogMessage", "fileNotFound"
                    ).format(fileAbsPath),
                )
                continue
