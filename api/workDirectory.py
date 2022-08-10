import os
import logging

from api.thread import LocalThread

logger = logging.getLogger("root")


def scanDirectory(_rootPath: str) -> list:
    rootPath = os.path.abspath(_rootPath)
    logger.info(f"开始扫描 {rootPath}")
    for directory in os.listdir(rootPath):
        directory = os.path.abspath(os.path.join(rootPath, directory))
        try:
            t = LocalThread(directory)
            logger.info(f"检测到存档目录 {directory}")
        except LocalThread.LocalThreadInvalidError:
            t = None
        finally:
            yield (directory, t)
