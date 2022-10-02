import sys
import logging

from PySide6.QtCore import QDir

from ui.sharedVars import app, workDirectoryObject
from ui.MainWindow import MainWindow

# fmt: off
# import time
# debugFileHandler = logging.FileHandler(f"./__debug/logs/{time.strftime('%Y-%m-%d %H-%M-%S', time.localtime())}.log", encoding="utf-8")
# debugFileHandler.setFormatter(logging.Formatter("[%(asctime)s][%(levelno)s:%(levelname)s][%(funcName)s() in %(module)s>> %(message)s", "%Y-%m-%d %H:%M:%S"))
# logger.addHandler(debugFileHandler)
# fmt: on

if __name__ == "__main__":
    logger = logging.getLogger("root")
    logger.setLevel(logging.DEBUG)

    mainWindow = MainWindow()

    workDirectoryObject.setWorkDirectory(QDir.currentPath())

    mainWindow.resize(800, 600)
    mainWindow.show()
    sys.exit(app.exec())
