# from typing import Self
from uuid import uuid4
from .simpleSignal import SimpleSignal


class Progress:
    _id = uuid4()
    id = ""
    progress = 0
    totalProgress = 0
    text = ""
    title = ""


class ProgressIndicator(SimpleSignal):
    def __init__(self, id=None, title=None, text=None):
        self.progress = Progress()
        self.inheritPI = None
        self.progress.id = id
        self.updateText(text, title)

    def inherit(self, newPI):
        self.inheritPI = newPI
        self.inheritPI.connect(self.getProgress, noArgs=True)

    def disinherit(self):
        self.inheritPI.disconnect(self.getProgress, noArgs=True)
        self.inheritPI = None

    def getProgress(self):
        return self.progress if self.inheritPI is None else self.inheritPI.getProgress()

    def updateText(self, text=None, title=None):
        if self.inheritPI is not None:
            self.inheritPI.updateText(text, title)
        else:
            if text is not None:
                self.progress.text = text
            if title is not None:
                self.progress.title = title
        self.emit(self.getProgress())

    def updateProgress(self, progress=None, totalProgress=None):
        if self.inheritPI is not None:
            self.inheritPI.updateProgress(progress, totalProgress)
        else:
            if progress is not None:
                self.progress.progress = progress
            if totalProgress is not None:
                self.progress.totalProgress = totalProgress
        self.emit(self.getProgress())
