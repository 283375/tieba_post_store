from os.path import basename, abspath
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QListView,
    QGroupBox,
    QCheckBox,
    QMessageBox,
    QVBoxLayout,
    QHBoxLayout,
)
from PySide6.QtCore import Qt, QStringListModel, QModelIndex, QItemSelectionModel, QFile

from api.thread import LocalThread
from ui.implements.WorkDirectory import WorkDirectory


class FindInvalid(QWidget):
    def __init__(self, parent=None):
        super(FindInvalid, self).__init__(parent)

        self.workDirectoryWidget = WorkDirectory()

        self._model = QStringListModel()
        self.listView = QListView()
        self.listView.setModel(self._model)
        self.listView.setSelectionMode(QListView.SelectionMode.MultiSelection)

        self.functionWrapper = QVBoxLayout()

        self.selectionButtons = QGroupBox("快速操作")
        self.selectionButtons.layout = QHBoxLayout(self.selectionButtons)
        self.selectionButtonAll = QPushButton("全选")
        self.selectionButtonAll.clicked.connect(lambda: self.selectAction("all"))
        self.selectionButtonNone = QPushButton("全不选")
        self.selectionButtonNone.clicked.connect(lambda: self.selectAction("none"))
        self.selectionButtonInverse = QPushButton("反选")
        self.selectionButtonInverse.clicked.connect(lambda: self.selectAction("inverse"))
        self.selectionButtons.layout.addWidget(self.selectionButtonAll)
        self.selectionButtons.layout.addWidget(self.selectionButtonNone)
        self.selectionButtons.layout.addWidget(self.selectionButtonInverse)

        self.triggerDeleteButton = QPushButton("Delete")
        self.triggerDeleteButton.clicked.connect(self.deleteConfirm)

        self.moveToTrashCheckBox = QCheckBox("Move to trash")

        self.functionWrapper.addWidget(self.selectionButtons)
        self.functionWrapper.addWidget(self.moveToTrashCheckBox)
        self.functionWrapper.addWidget(self.triggerDeleteButton)

        self.bottomLayout = QHBoxLayout()
        self.bottomLayout.addWidget(self.listView)
        self.bottomLayout.addLayout(self.functionWrapper)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.workDirectoryWidget)
        self.layout.addLayout(self.bottomLayout)

    def selectAction(self, action: str):
        setSelectState = lambda index, const: self.listView.selectionModel().select(
            index, const
        )

        for i in range(self._model.rowCount()):
            index = self._model.index(i, 0, QModelIndex())
            if action == "all":
                setSelectState(index, QItemSelectionModel.Select)
            elif action == "none":
                setSelectState(index, QItemSelectionModel.Deselect)
            elif action == "inverse":
                setSelectState(index, QItemSelectionModel.Toggle)

    def scanComplete(self, result: list[tuple[str, LocalThread | None]]):
        invalidDirs = [dir for dir, t in result if t is None]
        self._model.setStringList(invalidDirs)
        self.selectAction("all")

    def deleteConfirm(self):
        dirs = [
            self._model.data(index, Qt.UserRole)
            for index in self.listView.selectedIndexes()
        ]
        message = (
            "These files or directories will be "
            + ("moved to trash" if self.moveToTrashCheckBox.isChecked() else "deleted")
            + "<br><br>"
            + "<br>".join(basename(dir) for dir in dirs)
        )
        result = QMessageBox.question(self, "Confirm", message)
        if result == QMessageBox.Yes:
            self.delete(dirs)

    def delete(self, dirs: list[str]):
        for _dir in dirs:
            absDir = abspath(_dir)
            file = QFile(absDir)
            if file.exists():
                if self.moveToTrashCheckBox.isChecked():
                    result = file.moveToTrash()
                else:
                    result = file.remove()

                if result == False:
                    QMessageBox.warning(
                        self, "Warning", f"Unable to delete {absDir}, skipping."
                    )
                    continue
            else:
                QMessageBox.warning(
                    self, "Warning", f"{absDir} does not exist, skipping."
                )
                continue
