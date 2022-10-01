from ui.base.WorkDirectory import Ui_WorkDirectory

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QWidget

from ui._vars import workDirectoryObject


class WorkDirectory(QWidget, Ui_WorkDirectory):
    def __init__(self, parent=None):
        super(WorkDirectory, self).__init__(parent)
        self.setupUi(self)

        self.dirLabel.setText(workDirectoryObject.dir)

    @Slot()
    def on_WD_changeDirButton_clicked(self):
        tempDir = workDirectoryObject.dir
        self.changeDirFileDialog.setDirectory(tempDir)
        if self.changeDirFileDialog.exec_():
            newDir = self.changeDirFileDialog.selectedFiles()[0]
            self.dirLabel.setText(newDir)
            workDirectoryObject.setWorkDirectory(newDir)
