import logging
from typing import List, Dict, Callable

logger = logging.getLogger("main")

class HandlerNotCallableError(Exception):
    def __init__(self, handler):
        self.handler = handler

    def __str__(self):
        return f"{(type(self.handler))}: {str(self.handler)} is not callable."


class SimpleSignal:
    __handlers: List[Callable] = []
    handlers = []

    def connect(self, handler: Callable, noArgs: bool = False):
        if not callable(handler):
            raise HandlerNotCallableError(handler)
        if handler not in self.__handlers:
            self.handlers.append([handler, {"noArgs": noArgs}])
            self.__handlers.append(handler)

    def disconnect(self, handler: Callable):
        try:
            i = self.__handlers.index(handler)
            self.__handlers.pop(i)
            self.handlers.pop(i)
        except (ValueError, IndexError) as e:
            logger.error(f"simpleSignal disconnect {str(e)}: {handler}")

    def emit(self, *args, **kwargs):
        if self.handlers:
            for _ in self.handlers:
                handler, opt = _
                handler.__call__() if opt["noArgs"] else handler.__call__(*args, **kwargs)


class SimpleSignalByName:
    signals = []
    handlers: Dict[str, List[Callable]] = {}

    def on(self, name, handler: Callable):
        if not callable(handler):
            raise HandlerNotCallableError(handler)

        if name not in self.signals:
            self.signals.append(name)
            self.handlers[name] = [handler]
        else:
            self.handlers[name].append(handler)

    def off(self, name, handler: Callable):
        if name in self.signals:
            self.handlers[name].remove(handler)

    def emit(self, name, *args, **kwargs):
        if name in self.signals:
            [handler.__call__(*args, **kwargs) for handler in self.handlers[name]]
