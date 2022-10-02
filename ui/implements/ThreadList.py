from ui.models.ThreadList import Model, Delegate

from PySide6.QtWidgets import QListView

from PySide6.QtCore import QModelIndex, Signal, Slot

from ui.sharedVars import statusBar, workDirectoryObject
from api.thread import LocalThread


class ThreadList(QListView):
    threadSelected = Signal(LocalThread)

    def __init__(self, parent=None):
        super(ThreadList, self).__init__(parent)
        self.setSelectionMode(QListView.SingleSelection)
        self.setSelectionRectVisible(True)
        self.setDragEnabled(False)
        self.setAcceptDrops(False)

        self._model = Model()
        self.setModel(self._model)
        self._delegate = Delegate()
        self.setItemDelegate(self._delegate)

        self.activated.connect(self.__itemChanged)

    @Slot(list)
    def dirScanComplete(self, validResult: list[tuple[str, LocalThread]]):
        statusBar.showMessage(
            f"在 {workDirectoryObject.dir} 中找到了 {len(validResult)} 个有效存档目录", 10000
        )
        self._model.updateList([t for dir, t in validResult])

    @Slot(QModelIndex)
    def __itemChanged(self, index: QModelIndex):
        localThread = self._model.data(index, Model.LocalThreadRole)
        self.threadSelected.emit(localThread)
