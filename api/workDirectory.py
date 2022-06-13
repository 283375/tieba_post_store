import os
import json
import logging

from api.thread import LocalThread

logger = logging.getLogger("main")


def getSavedPosts(rootPath: str) -> list:
    savedPosts = []
    for directory in os.listdir(rootPath):
        directory = os.path.abspath(os.path.join(rootPath, directory))
        try:
            t = LocalThread(directory)
            if t.isValid:
                savedPosts.append(t)
        except (LocalThread.LocalThreadInvalidException, json.JSONDecodeError):
            logger.warning(f"无效存档目录：{directory}")
    logger.info(f"Found {len(savedPosts)} posts in {rootPath}")
    return savedPosts
