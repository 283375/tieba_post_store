import logging
from functools import wraps
from typing import Callable
from typing_extensions import Self
from uuid import uuid4

from . import formatNumber

logger = logging.getLogger("root")


class UncallableError(Exception):
    def __init__(self, obj):
        self.obj = obj

    def __str__(self):
        return f"{type(self.obj)} is not a callable object."


class ProgressType:
    Plain = 0
    BigNumber = 1
    Byte = 2


class Progress:
    def __init__(self, id: str = "", title: str = "", type: int = ProgressType.Plain):
        self.__uuid = uuid4()
        self.id = id
        self.type = type
        self.progress = 0
        self.totalProgress = 0
        self.text = 0
        self.title = title
        self.overrideFormat: Callable[[Self], str] = None

    def __str__(self):
        return f'<Progress {str(self.__uuid)} {str(self.id)}> {f"{self.title} - {self.text}" if self.title else self.text}: {self.progress} / {self.totalProgress}'

    def ReturnSelf(func):
        @wraps(func)
        def wrapper(self: Self, *args, **kwargs):
            func(self, *args, **kwargs)
            return self

        return wrapper

    @ReturnSelf
    def _updateProgress(self, p: int = None, tp: int = None):
        if p is not None:
            self.progress = p
        if tp is not None:
            self.totalProgress = tp

    @ReturnSelf
    def _updateText(self, text: str = None, title: str = None):
        if text is not None:
            self.text = text
        if title is not None:
            self.title = title

    @ReturnSelf
    def update(self, p: int = None, tp: int = None, text: str = None, title: str = None):
        self._updateProgress(p, tp)
        self._updateText(text, title)

    @ReturnSelf
    def increase(self, p: int = 1):
        self.progress += p

    @ReturnSelf
    def decrease(self, p: int = 1):
        self.progress -= p

    @ReturnSelf
    def setType(self, type: int):
        self.type = type

    def __defaultFormat(self) -> str:
        """
        __defaultFormat: Default formatter for current progress
        Will return something like
        `title - text: 52.37MB / 521.85MB (9.96%)`

        :rtype: str
        """
        __str = ""
        if self.title and self.text:
            __str += f"{self.title} - {self.text}: "
        elif self.title or self.text:
            __str += f"{self.title or self.text}: "

        __formatNum = str
        if self.type == ProgressType.BigNumber:
            __formatNum = formatNumber.bigNumber
        elif self.type == ProgressType.Byte:
            __formatNum = formatNumber.byte
        __str += f"{__formatNum(self.progress)} / {__formatNum(self.totalProgress)} "
        __str += f"{(self.progress / self.totalProgress):.2%}"
        return __str

    def format(self):
        return (
            self.overrideFormat(self)
            if self.overrideFormat is not None and callable(self.overrideFormat)
            else self.__defaultFormat()
        )


"""
class ProgressIndicator(SimpleSignal):
    def __init__(self, id=None, title=None, text=None):
        super(ProgressIndicator, self).__init__()
        self.progress = Progress(id)
        self.inheritPI = None
        self.updateText(text, title)

    def __broadcast(self):
        self.emit(self.getProgress())

    def inherit(self, newPI: Self):
        self.inheritPI = newPI
        self.inheritPI.connect(self.__broadcast, noArgs=True)

    def disinherit(self):
        self.inheritPI.disconnect(self.__broadcast)
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
        self.__broadcast()

    def updateProgress(self, progress=None, totalProgress=None):
        if self.inheritPI is not None:
            self.inheritPI.updateProgress(progress, totalProgress)
        else:
            if progress is not None:
                self.progress.progress = progress
            if totalProgress is not None:
                self.progress.totalProgress = totalProgress
        self.__broadcast()
"""
