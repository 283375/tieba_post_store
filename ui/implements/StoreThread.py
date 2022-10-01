from ui.base.StoreThread import Ui_StoreThread

import logging
from requests import ConnectTimeout, ReadTimeout
from PySide6.QtWidgets import QProgressBar, QMessageBox, QWidget
from PySide6.QtCore import Qt, QThread, Signal, Slot

from api.thread import LocalThread
from utils.progress import Progress
from ui._vars import app, workDirectoryObject

logger = logging.getLogger("root")


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


class StoreThread(QWidget, Ui_StoreThread):
    storeComplete = Signal()

    def __init__(self, parent=None):
        super(StoreThread, self).__init__(parent)
        self.localThread = None

        self.setupUi(self)

    @Slot()
    def on_ST_startButton_clicked(self):
        self.storeStart()

    @Slot()
    def on_ST_abortButton_clicked(self):
        self.storeSuspend()

    @Slot(LocalThread)
    def setLocalThread(self, t: LocalThread):
        self.localThread = t
        self.lzOnlyCheckBox.setChecked(t.storeOptions["lzOnly"])
        self.assetsCheckBox.setChecked(t.storeOptions["assets"])
        self.portraitsCheckBox.setChecked(t.storeOptions["portraits"])
        self.startButton.setText("更新" if t.isValid else "存档")

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
            self.__updateProgressBar(self.progressBar1, p)
        elif p.id in ["RemoteThread-Page", "LocalThread-Detail"]:
            self.__updateProgressBar(self.progressBar2, p)
        elif p.id in ["RemoteThread-Post", "LocalThread-DownloadAsset"]:
            self.__updateProgressBar(self.progressBar3, p)
        else:
            logger.warning(f"Unknown progress id {p.id}")

    @Slot()
    def storeStart(self, *args):
        self.localThread.updateStoreOptions(
            {
                "lzOnly": self.lzOnlyCheckBox.isChecked(),
                "assets": self.assetsCheckBox.isChecked(),
                "portraits": self.portraitsCheckBox.isChecked(),
            }
        )
        self._thread = StoreThreadThread()
        self._thread.exceptionOccured.connect(self.storeExceptionOccured)
        self._thread.actionFinal.connect(self.storeFinal)
        self._thread.progressUpdated.connect(
            self.updateProgress, Qt.BlockingQueuedConnection
        )

        self.lzOnlyCheckBox.setEnabled(False)
        self.assetsCheckBox.setEnabled(False)
        self.portraitsCheckBox.setEnabled(False)
        self.startButton.setEnabled(False)
        self.abortButton.setEnabled(True)

        self._thread.setLocalThread(self.localThread)
        self._thread.start()

    def storeSuspend(self, *args):
        self.storeExceptionOccured(Exception("Terminated by user."))

    @Slot(Exception)
    def storeExceptionOccured(self, e: Exception):
        self._thread.progressUpdated.disconnect(self.updateProgress)
        self._thread.exceptionOccured.disconnect(self.storeExceptionOccured)
        self._thread.actionFinal.disconnect(self.storeFinal)
        self._thread.terminate()
        self._thread.wait()
        logger.exception(f"存档 {self.localThread.threadId} 时发生错误: {str(e)}")

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
        self.__resetProgressBar(self.progressBar1)
        self.__resetProgressBar(self.progressBar2)
        self.__resetProgressBar(self.progressBar3)
        self.storeComplete.emit()
        workDirectoryObject.scan()

        self.lzOnlyCheckBox.setEnabled(True)
        self.assetsCheckBox.setEnabled(True)
        self.portraitsCheckBox.setEnabled(True)
        self.startButton.setEnabled(True)
        self.abortButton.setEnabled(False)
