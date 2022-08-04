import logging
from requests import ConnectTimeout, ReadTimeout
from PySide6.QtWidgets import (
    QProgressBar,
    QLabel,
    QPushButton,
    QMessageBox,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
)
from PySide6.QtCore import Qt, QObject, QThread, Signal, Slot

from api.thread import LocalThread
from utils.progressIndicator import Progress
from ._vars import app, signals

logger = logging.getLogger("main")


class StoreThreadThread(QThread):
    exceptionOccured = Signal(Exception)
    actionFinal = Signal()

    progressUpdatedSignal = Signal(Progress)

    def __init__(self, parent=None):
        super(StoreThreadThread, self).__init__(parent)
        self.localThread = None

    def progressUpdated(self, progress):
        self.progressUpdatedSignal.emit(progress)

    def setLocalThread(self, t: LocalThread):
        self.localThread = t
        self.localThread.stepProgress.connect(self.progressUpdated)
        self.localThread.stepDetailProgress.connect(self.progressUpdated)
        self.localThread.singleFileProgress.connect(self.progressUpdated)

    def run(self):
        try:
            self.localThread._store()
        except Exception as e:
            self.exceptionOccured.emit(e)
        else:
            self.actionFinal.emit()


class StoreThread(QWidget):
    storeComplete = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.localThread = None

        self.stepProgressBar = QProgressBar()
        self.stepDetailProgressBar = QProgressBar()
        self.singleFileProgressBar = QProgressBar()
        self.label = QLabel("")
        self.labelSizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.labelSizePolicy.setHorizontalStretch(1)
        self.label.setSizePolicy(self.labelSizePolicy)
        self.pushButton = QPushButton("存档")
        self.pushButton.clicked.connect(self.storeStart)

        self.lowerWrapper = QHBoxLayout()
        self.lowerWrapper.addWidget(self.pushButton)
        self.lowerWrapper.addWidget(self.label)
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.stepProgressBar)
        self.layout.addWidget(self.stepDetailProgressBar)
        self.layout.addWidget(self.singleFileProgressBar)
        self.layout.addLayout(self.lowerWrapper)

        self._thread = StoreThreadThread()
        self._thread.progressUpdatedSignal.connect(self.progressUpdated)
        self._thread.exceptionOccured.connect(self.storeExceptionOccured)
        self._thread.actionFinal.connect(self.storeFinal)

    @Slot(LocalThread)
    def setLocalThread(self, t: LocalThread):
        self.localThread = t
        self._thread.setLocalThread(t)
        self.pushButton.setText("更新" if t.isValid else "存档")

    def __updateProgressBar(self, progressBar: QProgressBar, progress: Progress):
        if progressBar.minimum() != 0:
            progressBar.setMinimum(0)
        if progressBar.maximum() != progress.totalProgress:
            progressBar.setMaximum(progress.totalProgress)
        progressBar.setFormat(f"{progress.title} - {progress.text}: %p%")
        progressBar.setValue(progress.progress)
        app.processEvents()

    @Slot(Progress)
    def progressUpdated(self, p: Progress):
        if p.id in ["LocalThread-Step"]:
            self.__updateProgressBar(self.stepProgressBar, p)
        elif p.id in ["RemoteThread-Page", "LocalThread-StepDetail"]:
            self.__updateProgressBar(self.stepDetailProgressBar, p)
        elif p.id in ["RemoteThread-Post", "LocalThread-SingleFile"]:
            self.__updateProgressBar(self.singleFileProgressBar, p)
        else:
            logger.warning(f"Unknown progress id {p.id}")

    @Slot()
    def storeStart(self, *args):
        self.pushButton.setEnabled(False)
        self._thread.start()

    @Slot(Exception)
    def storeExceptionOccured(self, e: Exception):
        logger.error(f"{self.__class__.__name__}: Store {self.localThread.threadId} failed due to: {str(e)}")

        errorText = "网络超时" if type(e) in (ConnectTimeout, ReadTimeout) else "出现意外错误"
        QMessageBox.critical(self, "错误", f"{errorText}，存档失败。详细信息:\n{str(e)}")
        self.storeFinal(exception=True)

    @Slot()
    def storeFinal(self, exception: bool = False):
        self.label.setText("异常终止。" if exception else "存档完成！")
        self.storeComplete.emit()
        signals.refreshWorkDirectory.emit()
        self.pushButton.setEnabled(True)
