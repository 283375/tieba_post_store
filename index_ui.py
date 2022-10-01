import sys
from PySide6.QtCore import QTranslator

from ui.Entry import *

# fmt: off
# import time
# debugFileHandler = logging.FileHandler(f"./__debug/logs/{time.strftime('%Y-%m-%d %H-%M-%S', time.localtime())}.log", encoding="utf-8")
# debugFileHandler.setFormatter(logging.Formatter("[%(asctime)s][%(levelno)s:%(levelname)s][%(funcName)s() in %(module)s>> %(message)s", "%Y-%m-%d %H:%M:%S"))
# logger.addHandler(debugFileHandler)
# fmt: on

if __name__ == "__main__":
    mainWindow.show()
    sys.exit(app.exec())
