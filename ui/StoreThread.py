from PySide6.QtWidgets import (
    QProgressBar,
    QLabel,
    QPushButton,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
)
from PySide6.QtCore import Qt, QThread, Signal, Slot

from api.thread import LocalThread
from ._vars import app, signals


class StoreThreadThread(QThread):
    actionUpdate = Signal(tuple)
    exceptionOccured = Signal(Exception)
    actionFinal = Signal()

    def __init__(self, parent=None):
        super(StoreThreadThread, self).__init__(parent)
        self.localThread = None

    def setLocalThread(self, t: LocalThread):
        self.localThread = t

    def run(self):
        try:
            _generator = self.localThread._store()
            for action in _generator:
                self.actionUpdate.emit(action)
        except Exception as e:
            self.exceptionOccured.emit(e)
        finally:
            self.actionFinal.emit()


class StoreThread(QWidget):
    storeComplete = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.localThread = None
        self.totalStep = 4
        self.step = -1
        self.labels = ["请求最新最热数据", "分析最新最热数据", "下载资源文件", "保存最新最热数据"]

        self.progressBar = QProgressBar()
        self.progressBar.setMinimum(0)
        self.progressBar.setAlignment(Qt.AlignVCenter)
        self.label = QLabel("")
        self.labelSizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.labelSizePolicy.setHorizontalStretch(1)
        self.label.setSizePolicy(self.labelSizePolicy)
        self.pushButton = QPushButton("存档")
        self.pushButton.clicked.connect(self.storeStart)

        self.lowerWrapper = QWidget(self)
        self.lowerWrapper.layout = QHBoxLayout(self.lowerWrapper)
        self.lowerWrapper.layout.addWidget(self.pushButton)
        self.lowerWrapper.layout.addWidget(self.label)
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.progressBar)
        self.layout.addWidget(self.lowerWrapper)

        self._thread = StoreThreadThread()
        self._thread.actionUpdate.connect(self.storeActionUpdate)
        self._thread.exceptionOccured.connect(self.storeExceptionOccured)
        self._thread.actionFinal.connect(self.storeFinal)

    @Slot(LocalThread)
    def setLocalThread(self, t: LocalThread):
        self.localThread = t
        self._thread.setLocalThread(t)
        self.pushButton.setText("更新" if t.isValid else "存档")

    @Slot()
    def storeStart(self, *args):
        self.pushButton.setEnabled(False)
        self._thread.start()

    @Slot(tuple)
    def storeActionUpdate(self, action: tuple):
        newStep = action[0]
        newProgress = action[1][0]
        newTotalProgress = action[1][1]
        if newStep > self.step:
            self.step = newStep
            if newTotalProgress < 0:
                self.progressBar.setMinimum(0)
                self.progressBar.setMaximum(0)
            else:
                self.progressBar.setMaximum(newTotalProgress)
                self.progressBar.setValue(newProgress)
        else:
            self.progressBar.setValue(newProgress)
        self.label.setText(
            f"{self.step} / {self.totalStep - 1} - 正在{self.labels[self.step]} ({newProgress}/{newTotalProgress})"
        )
        app.processEvents()

    @Slot(Exception)
    def storeExceptionOccured(self, e: Exception):
        raise e

    @Slot()
    def storeFinal(self):
        self.label.setText("存档完成！")
        self.storeComplete.emit()
        signals.refreshWorkDirectory.emit()
        self.step = -1
        self.pushButton.setEnabled(True)
