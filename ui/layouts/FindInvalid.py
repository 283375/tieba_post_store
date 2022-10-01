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
from PySide6.QtCore import Qt, QAbstractListModel, QModelIndex, QItemSelectionModel, QFile

from api.thread import LocalThread
from ui._vars import workDirectoryObject


class ListModel(QAbstractListModel):
    def __init__(self, parent=None):
        super(ListModel, self).__init__(parent)
        self.__list = []

    def rowCount(self, parent=None) -> int:
        return len(self.__list)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if index.row() < 0 or index.row() >= self.rowCount():
            return None
        return self.__list[index.row()].get(role)

    def setList(self, _list: list):
        self.beginRemoveRows(QModelIndex(), 0, self.rowCount() - 1)
        self.__list.clear()
        self.endRemoveRows()

        self.beginInsertRows(QModelIndex(), 0, len(_list) - 1)
        for item in _list:
            self.__list.append({Qt.DisplayRole: str(item), Qt.UserRole: str(item)})
        self.endInsertRows()


class FindInvalid(QWidget):
    def __init__(self, parent=None):
        super(FindInvalid, self).__init__(parent)

        self.dirLabel = QLabel()
        workDirectoryObject.dirChanged.connect(lambda dir: self.dirLabel.setText(dir))

        self._model = ListModel()
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
        self.layout.addWidget(self.dirLabel)
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
        self._model.setList(invalidDirs)
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
