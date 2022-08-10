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
from PySide6.QtCore import Qt, QObject, QThread, QMutex, Signal, Slot

from api.thread import LocalThread
from utils.progress import Progress
from ._vars import app, signals

logger = logging.getLogger("root")


class UserTerminate(Exception):
    def __str__(self):
        return "用户自行终止。"


class StoreThreadThread(QThread):
    exceptionOccured = Signal(Exception)
    actionFinal = Signal()
    progressUpdated = Signal(Progress)

    def __init__(self, parent=None):
        super(StoreThreadThread, self).__init__(parent)

    def setLocalThread(self, t: LocalThread):
        self.localThread = t

    def run(self):
        try:
            for p in self.localThread._store():
                self.progressUpdated.emit(p)
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
        self.detailProgressBar = QProgressBar()
        self.singleFileProgressBar = QProgressBar()
        self.stepProgressBar.setAlignment(Qt.AlignVCenter)
        self.detailProgressBar.setAlignment(Qt.AlignVCenter)
        self.singleFileProgressBar.setAlignment(Qt.AlignVCenter)
        self.label = QLabel("")
        self.labelSizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.labelSizePolicy.setHorizontalStretch(1)
        self.label.setSizePolicy(self.labelSizePolicy)
        self.storeStartButton = QPushButton("存档")
        self.storeStartButton.clicked.connect(self.storeStart)
        self.storeSuspendButton = QPushButton("强制中止")
        self.storeSuspendButton.setEnabled(False)
        self.storeSuspendButton.clicked.connect(self.storeSuspend)

        self.lowerWrapper = QHBoxLayout()
        self.lowerWrapper.addWidget(self.storeSuspendButton)
        self.lowerWrapper.addWidget(self.storeStartButton)
        self.lowerWrapper.addWidget(self.label)
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.stepProgressBar)
        self.layout.addWidget(self.detailProgressBar)
        self.layout.addWidget(self.singleFileProgressBar)
        self.layout.addLayout(self.lowerWrapper)

    @Slot(LocalThread)
    def setLocalThread(self, t: LocalThread):
        self.localThread = t
        self.storeStartButton.setText("更新" if t.isValid else "存档")

    def __updateProgressBar(self, progressBar: QProgressBar, progress: Progress):
        # self._thread.blockSignals(True)
        if progressBar.minimum() != 0:
            progressBar.setMinimum(0)
            progressBar.setValue(0)
        if progressBar.maximum() != progress.totalProgress:
            progressBar.setMaximum(progress.totalProgress)
            progressBar.setValue(0)
        progressBar.setFormat(progress.format())
        if progressBar.value() != progress.progress:
            progressBar.setValue(progress.progress)
        app.processEvents()
        # self._thread.blockSignals(False)

    @Slot(Progress)
    def updateProgress(self, p: Progress):
        if p.id in ["LocalThread-Step"]:
            self.__updateProgressBar(self.stepProgressBar, p)
        elif p.id in ["RemoteThread-Page", "LocalThread-Detail"]:
            self.__updateProgressBar(self.detailProgressBar, p)
        elif p.id in ["RemoteThread-Post", "LocalThread-DownloadAsset"]:
            self.__updateProgressBar(self.singleFileProgressBar, p)
        else:
            logger.warning(f"Unknown progress id {p.id}")

    @Slot()
    def storeStart(self, *args):
        self._thread = StoreThreadThread()
        self._thread.exceptionOccured.connect(self.storeExceptionOccured)
        self._thread.actionFinal.connect(self.storeFinal)
        self._thread.progressUpdated.connect(self.updateProgress, Qt.BlockingQueuedConnection)
        self.storeStartButton.setEnabled(False)
        self.storeSuspendButton.setEnabled(True)
        self._thread.setLocalThread(self.localThread)
        self._thread.start()

    def storeSuspend(self, *args):
        self.storeExceptionOccured(UserTerminate())

    @Slot(Exception)
    def storeExceptionOccured(self, e: Exception):
        self._thread.exceptionOccured.disconnect(self.storeExceptionOccured)
        self._thread.actionFinal.disconnect(self.storeFinal)
        self._thread.progressUpdated.disconnect(self.updateProgress)
        self._thread.terminate()
        logger.error(f"{self.__class__.__name__}: Store {self.localThread.threadId} failed due to: {str(e)}")

        errorText = "网络超时" if type(e) in (ConnectTimeout, ReadTimeout) else "出现意外错误"
        QMessageBox.critical(self, "错误", f"{errorText}，存档失败。详细信息:\n{str(e)}")
        self.storeFinal(exception=True)

    def __resetProgressBar(self, progressBar: QProgressBar):
        progressBar.reset()
        progressBar.resetFormat()

    @Slot()
    def storeFinal(self, exception: bool = False):
        self.label.setText("异常终止。" if exception else "存档完成！")
        if self._thread.isRunning():
            self._thread.quit()
        self.__resetProgressBar(self.stepProgressBar)
        self.__resetProgressBar(self.detailProgressBar)
        self.__resetProgressBar(self.singleFileProgressBar)
        self.storeComplete.emit()
        signals.refreshWorkDirectory.emit()
        self.storeStartButton.setEnabled(True)
        self.storeSuspendButton.setEnabled(False)
