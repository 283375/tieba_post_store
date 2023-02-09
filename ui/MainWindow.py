from PySide6.QtCore import QCoreApplication, QTranslator
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMainWindow, QTabWidget

from ui import sharedVars
from ui.layouts import Index, FindInvalid, LogWindow
from ui.implements import Settings
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

        self.tab_Layout_Index = Index.Layout_Index(self.tabWidget)
        self.tab_Layout_FindInvalid = FindInvalid.Layout_FindInvalid(self.tabWidget)
        self.tab_Layout_LogWindow = LogWindow.Layout_LogWindow(self.tabWidget)
        self.tab_Settings = Settings.Settings(self.tabWidget)

        self.tabWidget.addTab(self.tab_Layout_Index, "Index")
        self.tabWidget.addTab(self.tab_Layout_FindInvalid, "Find Invalid Files")
        self.tabWidget.addTab(self.tab_Layout_LogWindow, "Log")
        self.tabWidget.addTab(self.tab_Settings, "Settings")
        
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

        self.tab_Layout_Index.retranslateUi()
        self.tab_Layout_FindInvalid.retranslateUi()
        self.tab_Layout_LogWindow.retranslateUi()
