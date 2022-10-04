from PySide6.QtCore import QCoreApplication, QTranslator
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMainWindow, QTabWidget

from ui import sharedVars
from ui.layouts import Index, FindInvalid, LogWindow
from ui.resources import main_qrc

app = sharedVars.app

translator = QTranslator(app)
translator.load(":/lang/zh_CN.qm")
app.installTranslator(translator)


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("tieba_post_store")
        self.setWindowIcon(QIcon(":/logo.svg"))
        self.setStatusBar(sharedVars.statusBar)

        self.tabWidget = QTabWidget(self)

        self.layout_Index = Index.Layout_Index(self.tabWidget)
        self.layout_FindInvalid = FindInvalid.Layout_FindInvalid(self.tabWidget)
        self.layout_LogWindow = LogWindow.Layout_LogWindow(self.tabWidget)

        self.tabWidget.addTab(self.layout_Index, "Index")
        self.tabWidget.addTab(self.layout_FindInvalid, "Find Invalid Files")
        self.tabWidget.addTab(self.layout_LogWindow, "Log")
        
        self.setCentralWidget(self.tabWidget)

        self.retranslateUi()

    def retranslateUi(self, *args):
        self.tabWidget.setTabText(
            0, QCoreApplication.translate("MainWindow", "tab_Index")
        )
        self.tabWidget.setTabText(
            1, QCoreApplication.translate("MainWindow", "tab_FindInvalid")
        )
        self.tabWidget.setTabText(
            2, QCoreApplication.translate("MainWindow", "tab_LogWindow")
        )

        self.layout_Index.retranslateUi()
        self.layout_FindInvalid.retranslateUi()
        self.layout_LogWindow.retranslateUi()
