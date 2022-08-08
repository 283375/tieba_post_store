from threading import Thread, Timer
from queue import Queue
import logging
from uuid import uuid4
from typing import List, Dict, Callable

logger = logging.getLogger("main")

class HandlerNotCallableError(Exception):
    def __init__(self, handler):
        self.handler = handler

    def __str__(self):
        return f"{(type(self.handler))}: {str(self.handler)} is not callable."

signalEmitQueue = Queue(maxsize=0)

def emitSignal():
    while True:
        try:
            sig = signalEmitQueue.get()
            handlers, args, kwargs = sig
            for _ in handlers:
                handler, opt = _
                handler.__call__() if opt["noArgs"] else handler.__call__(*args, **kwargs)
        except Exception as e:
            logger.error(e)
        finally:
            signalEmitQueue.task_done()


class KeepQueueAlive:
    def __init__(self):
        self.__timer: Timer = None
        self.__seconds = 1
        self.__action = signalEmitQueue.join

    def run(self, seconds: int = 1):
        if self.is_running():
            return

        self.__seconds = seconds
        self.__run_action()

    def __run_action(self):
        self.__timer = Timer(self.__seconds, self.__hook)
        self.__timer.start()

    def __hook(self, *args, **kwargs):
        self.__action(*args, **kwargs)
        self.__run_action()

    def is_running(self):
        return self.__timer and self.__timer.is_alive()

    def cancel(self):
        if self.is_running():
            self.__timer.cancel()
            self.__timer = None

# signalEmitter = ...
signalEmitter = Thread(target=emitSignal, daemon=True, name='signalEmitter')
signalEmitter.start()
keepQueueAliveInstance = KeepQueueAlive()
keepQueueAliveInstance.run()

class SimpleSignal:
    def __init__(self):
        self.__id = uuid4()
        self.__handlers: List[Callable] = []
        self.handlers = []

    def connect(self, handler: Callable, noArgs: bool = False):
        logger.debug(f"收到 connect 请求：{str(handler)}")
        if not callable(handler):
            raise HandlerNotCallableError(handler)
        if handler not in self.__handlers:
            self.handlers.append([handler, {"noArgs": noArgs}])
            self.__handlers.append(handler)
        logger.debug(f"{str(self.__id)}: {self.handlers}")

    def disconnect(self, handler: Callable):
        logger.debug(f"收到 disconnect 请求：{handler}")
        try:
            i = self.__handlers.index(handler)
            self.__handlers.pop(i)
            self.handlers.pop(i)
        except Exception as e:
            logger.error(f"simpleSignal disconnect {str(e)}: {handler}")

    def emit(self, *args, **kwargs):
        if self.handlers:
            signalEmitQueue.put((self.handlers, args, kwargs))

"""
class SimpleSignalByName:
    def __init__(self):
        self.signals = []
        self.handlers: Dict[str, List[Callable]] = {}

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
"""
