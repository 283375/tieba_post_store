from PySide6.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextBrowser,
    QMainWindow,
    QWidget,
)

from ui import WorkDirectory


class CentralWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.functionalArea = QWidget()
        self.functionalArea.layout = QVBoxLayout(self.functionalArea)
        self.postIdEdit = QLineEdit()
        self.postIdEdit.setPlaceholderText("在此输入贴子 ID")

        self.changeWorkDirectoryWidget = WorkDirectory.ChangeWorkDirectory()

        self.functionalArea.layout.addWidget(self.postIdEdit)
        self.functionalArea.layout.addWidget(QPushButton('Preview'))
        self.functionalArea.layout.addWidget(QPushButton('Download'))

        self.logArea = QTextBrowser()

        self.layout = QVBoxLayout(self)
        wdsGroupbox = QGroupBox("Work Directory")
        wdsGroupbox.layout = QVBoxLayout(wdsGroupbox)
        wdsGroupbox.layout.addWidget(self.changeWorkDirectoryWidget)
        self.layout.addWidget(wdsGroupbox)
        self.layout.addWidget(self.functionalArea)
        self.layout.addWidget(self.logArea)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setCentralWidget(CentralWidget())
