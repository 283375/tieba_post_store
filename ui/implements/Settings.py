from ui.base.Settings import Ui_Settings

from PySide6.QtWidgets import QWidget, QFileDialog


class Settings(QWidget, Ui_Settings):
    def __init__(self, parent=None):
        super(Settings, self).__init__(parent)
        self.setupUi(self)

        self.fileDialog = QFileDialog()
        self.defaultStoreDir_FieldChangeButton.clicked.connect(self.fileDialog.open)
