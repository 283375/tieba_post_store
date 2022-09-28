from PySide6.QtCore import Slot
from PySide6.QtWidgets import QWidget

from ui.base.WorkDirectory import Ui_WorkDirectory
from ui._vars import workDirectoryInstance


class WorkDirectory(QWidget, Ui_WorkDirectory):
    def __init__(self, parent=None):
        super(WorkDirectory, self).__init__(parent)
        self.setupUi(self)

    @Slot()
    def on_changeDirButton_clicked(self):
        tempDir = workDirectoryInstance.dir
        self.changeDirFileDialog.setDirectory(tempDir)
        if self.changeDirFileDialog.exec_():
            newDir = self.changeDirFileDialog.selectedFiles()[0]
            self.dirLabel.setText(newDir)
            workDirectoryInstance.setWorkDirectory(newDir)
