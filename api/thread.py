import os
import time
import json
import requests
import logging
from copy import deepcopy
from urllib.parse import urlparse
from functools import partial, wraps

from api.tiebaApi import getThread, getSubPost

logger = logging.getLogger("main")


class RemoteThread:
    class ThreadInvalidException(Exception):
        def __init__(self, response: dict):
            self.code = response.get("error_code")
            self.message = response.get("error_msg")

        def __str__(self):
            return f'错误 {self.code or "(无代码)"}：{self.message or "无消息"}'

    class DataNotRequestedException(Exception):
        def __init__(self):
            self.message = "尚未请求数据，请先调用 _requestOrigData()。"

        def __str__(self):
            return self.message

    def __init__(self, threadId, lzOnly=False, lazyRequest=False):
        self.threadId = threadId
        self.lzOnly = lzOnly

        self.origData = {}
        self.threadInfo = None
        self.postList = None
        self.assetList = None

        self.dataRequested = False
        if not lazyRequest:
            self._requestOrigData(self.lzOnly)

    def isDataRequested(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not self.dataRequested:
                raise self.DataNotRequestedException()
            else:
                return func(self, *args, **kwargs)

        return wrapper

    def _requestOrigData(self, lzOnly):
        preRequest = getThread(self.threadId, page=1, lzOnly=lzOnly)
        if preRequest.get("page", None) is None:
            raise self.ThreadInvalidException(preRequest)

        threadTotalPage = int(preRequest["page"]["total_page"])

        for page in range(1, threadTotalPage + 1):
            thread = getThread(self.threadId, page=page, lzOnly=lzOnly)
            self.origData[f"page_{page}"] = thread
            self.dataRequested = True

    @isDataRequested
    def getOrigData(self):
        return self.origData

    @isDataRequested
    def getThreadInfo(self):
        base = self.origData["page_1"]["thread"]
        return {
            "id": base["id"],
            "title": base["thread_info"]["title"],
            "createTime": base["thread_info"]["create_time"],
            "author": {
                "id": base["author"]["id"],
                "origName": base["author"]["name"],
                "displayName": base["author"]["name_show"],
            },
            "forum": {
                "id": base["thread_info"]["forum_id"],
                "name": base["thread_info"]["forum_name"],
            },
            "__ORIG_DATA__": base,
        }

    def sortPost(self, postList):
        return sorted(postList, key=lambda x: int(x["floor"]))

    @isDataRequested
    def getPostList(self, page=1):
        try:
            postList = self.origData[f"page_{page}"]["post_list"]
            for post in postList:
                subpostNum = int(post["sub_post_number"])
                if subpostNum > 0:
                    subpostInfo = getSubPost(
                        self.threadId,
                        postId=post["id"],
                        subpostId=0,
                        rn=subpostNum,
                    )
                    post["sub_post_list"] = subpostInfo["subpost_list"]
            return self.sortPost(postList)
        except KeyError as e:
            raise IndexError(f"Page {page} does not exist.") from e

    @isDataRequested
    def getFullPostList(self):
        fullList = []
        for pageNum in range(1, len(self.origData) + 1):
            fullList += self.getPostList(pageNum)
        return self.sortPost(fullList)

    def analyzeAsset(self, postContents):
        assetList = {
            "images": [],
            "videos": [],
            "audios": [],
        }
        for contentBlock in postContents:
            contentType = contentBlock["type"]
            if contentType == "3":  # image
                assetList["images"].append(
                    {
                        "src": contentBlock["origin_src"],
                        "id": contentBlock["pic_id"],
                        "size": contentBlock["size"],
                        "filename": "{}{}".format(
                            contentBlock["pic_id"],
                            os.path.splitext(
                                os.path.basename(
                                    urlparse(contentBlock["origin_src"]).path
                                )
                            )[1],
                        ),
                    }
                )
            elif contentType == "5":  # video
                assetList["videos"].append(
                    {
                        "src": contentBlock["link"],
                        "size": contentBlock["origin_size"],
                        "filename": os.path.basename(
                            urlparse(contentBlock["link"]).path
                        ),
                    }
                )
            elif contentType == "10":  # audio
                assetList["audios"].append(
                    {
                        "src": f'http://c.tieba.baidu.com/c/p/voice?voice_md5={contentBlock["voice_md5"]}&play_from=pb_voice_play',
                        "filename": f'{contentBlock["voice_md5"]}.mp3',
                    }
                )

            """
            elif contentType == "20":  # [?] maybe memePic
                # [?] all the code below is not tested
                imageList.append(content)
            """
        return assetList

    @isDataRequested
    def getAssetList(self, page=1):
        postList = self.getPostList(page)
        assetList = {
            "images": [],
            "audios": [],
            "videos": [],
        }
        for post in postList:
            analyzedAssets = self.analyzeAsset(post["content"])
            assetList["images"] += analyzedAssets["images"]
            assetList["audios"] += analyzedAssets["audios"]
            assetList["videos"] += analyzedAssets["videos"]
        return assetList

    @isDataRequested
    def getFullAssetList(self):
        fullAssetList = {
            "images": [],
            "audios": [],
            "videos": [],
        }
        for pageNum in range(1, len(self.origData) + 1):
            analyzedAsset = self.getAssetList(pageNum)
            fullAssetList["images"] += analyzedAsset["images"]
            fullAssetList["audios"] += analyzedAsset["audios"]
            fullAssetList["videos"] += analyzedAsset["videos"]
        return fullAssetList

    @isDataRequested
    def getUserList(self, page=1):
        return self.origData[f"page_{page}"]["user_list"]

    @isDataRequested
    def getFullUserList(self):
        fullUserList = []
        fullUserIdList = [user["id"] for user in fullUserList]

        for pageNum in range(1, len(self.origData) + 1):
            userList = self.getUserList(pageNum)
            for user in userList:
                if user["id"] not in fullUserIdList:
                    fullUserList.append(user)
        return fullUserList

    @isDataRequested
    def getUserListById(self, page=1):
        userList = self.getUserList(page)
        return {user["id"]: user for user in userList}

    @isDataRequested
    def getFullUserListById(self):
        fullUserList = {}
        for pageNum in range(1, len(self.origData) + 1):
            userList = self.getUserListById(pageNum)
            fullUserList |= userList
        return fullUserList

    @isDataRequested
    def getPortraitList(self, page=1):
        userList = self.getUserList(page)
        return [
            {
                "id": user["id"],
                "portrait": user["portrait"],
                "src": "http://tb.himg.baidu.com/sys/portrait/item/" + user["portrait"],
            }
            for user in userList
        ]

    @isDataRequested
    def getFullPortraitList(self):
        fullPortraitList = []
        for pageNum in range(1, len(self.origData) + 1):
            fullPortraitList += self.getPortraitList(pageNum)
        return fullPortraitList


open_utf8 = partial(open, encoding="utf-8")


def json_dump(data, filepath, _ensure_ascii=False, _indent=2, *args, **kwargs):
    with open_utf8(filepath, "w") as f:
        json.dump(data, f, ensure_ascii=_ensure_ascii, indent=_indent, *args, **kwargs)


class LocalThread:
    class LocalThreadNoOverwriteException(Exception):
        def __init__(self):
            self.message = "该目录已存在一个存档，无法使用新 ID 覆盖。"

        def __str__(self) -> str:
            return self.message

    class LocalThreadInvalidException(Exception):
        def __init__(self):
            self.message = "存档目录无效或损坏。"

        def __str__(self) -> str:
            return self.message

    class LocalThreadRepeatStoreException(Exception):
        def __init__(self, message=None):
            self.message = (
                message
                or "在已有的存档目录中调用任何 store 方法将覆盖相对应的原有存档并重置 updateTime 和 updateLog。\n使用 force=True以忽略此异常并强制执行。"
            )

        def __str__(self) -> str:
            return str(self.message)

    def __init__(self, storeDir: str, newThreadId: int = None):
        """
        __init__ 初始化本地贴子存档目录

        :param storeDir: 贴子存档目录
        :type storeDir: str
        :param newThreadId: 新存档的贴子 ID，默认为 None
        :type newThreadId: int, optional
        :raises self.LocalThreadNoOverwriteException: 若原存档目录有效且传入了 `newThreadId`，则抛出此异常
        """
        self.storeDir = os.path.abspath(storeDir)
        self.assetDir = os.path.join(self.storeDir, "assets")
        self.portraitDir = os.path.join(self.storeDir, "portraits")
        self.newThreadId = newThreadId

        self.storeOptions = {
            "__VERSION__": 1,
            "lzOnly": False,
            "withAsset": False,
            "withPortrait": False,
            "storeTime": None,
            "updateTime": None,
            "updateLog": [],
        }

        self.threadInfo = None
        self.postList = None
        self.userList = None
        self.assetList = None
        self.origData = None

        self.isValid = False
        self._isValid()
        if self.isValid:
            if newThreadId:
                raise self.LocalThreadNoOverwriteException()
            self._fillStoredData()
            self.updateStoreOptions(self.threadInfo["storeOptions"])

    def _isValid(self):
        try:
            open_utf8(os.path.join(self.storeDir, "threadInfo.json"), "r")
            open_utf8(os.path.join(self.storeDir, "postList.json"), "r")
            open_utf8(os.path.join(self.storeDir, "userList.json"), "r")
            self.isValid = True
        except FileNotFoundError:
            self.isValid = False

    def _fillStoredData(self):
        try:
            with open_utf8(os.path.join(self.storeDir, "threadInfo.json"), "r") as f:
                self.threadInfo = json.load(f)
            with open_utf8(os.path.join(self.storeDir, "postList.json"), "r") as f:
                self.postList = json.load(f)
            with open_utf8(os.path.join(self.storeDir, "userList.json"), "r") as f:
                self.userList = json.load(f)

            if self.threadInfo["storeOptions"]["withAsset"]:
                with open_utf8(os.path.join(self.storeDir, "assetList.json"), "r") as f:
                    self.assetList = json.load(f)
        except FileNotFoundError as e:
            raise self.LocalThreadInvalidException() from e

    def updateStoreOptions(self, _overwriteOptions: dict):
        """
        updateStoreOptions 更新贴子的存档选项

        调用该方法的同时会检测 `assets` 及 `portraits` 目录是否存在，减少报错的风险。

        >>> updateStoreOptions({"withAsset": True})
        # 若 assets 目录不存在则自动创建

        :param _overwriteOptions: 要覆盖的存档选项
        :type _overwriteOptions: dict
        """
        overwriteOptions = deepcopy(_overwriteOptions)
        overwriteOptions.pop("__VERSION__", None)
        for k in [("withAsset", "assets"), ("withPortrait", "portraits")]:
            if overwriteOptions.get(k[0], False):
                os.makedirs(os.path.join(self.storeDir, k[1]), exist_ok=True)
        self.storeOptions = {**self.storeOptions, **overwriteOptions}

    def _storeAsset(self, overwriteAssetList=None):
        storeAssetPath = self.assetDir
        assetList = overwriteAssetList or self.assetList

        for key in ["images", "audios", "videos"]:
            if assetList[key]:
                storeAssetKeyPath = os.path.join(storeAssetPath, key)
                os.makedirs(storeAssetKeyPath, exist_ok=True)

                for asset in assetList[key]:
                    with open(
                        os.path.join(storeAssetKeyPath, asset["filename"]), "wb"
                    ) as f:
                        f.write(requests.get(asset["src"]).content)
        return assetList

    def _storePortrait(self, portraitList: list):
        storePortraitPath = self.portraitDir

        for portrait in portraitList:
            portraitFilename = os.path.join(storePortraitPath, f'{portrait["id"]}.jpg')
            logger.debug(f"正在保存头像 {portraitFilename}……")
            with open(portraitFilename, "wb") as f:
                f.write(requests.get(portrait["src"]).content)

    def _storeOrigData(self, timestamp):
        os.makedirs(os.path.join(self.storeDir, "origData"), exist_ok=True)
        with open_utf8(
            os.path.join(self.storeDir, "origData", f"{timestamp}.json"), "w"
        ) as f:
            json.dump(self.origData, f, ensure_ascii=False, indent=2)

    def store(self, force: bool = False):
        if self.isValid and not force:
            raise self.LocalThreadRepeatStoreException()

        os.makedirs(self.storeDir, exist_ok=True)

        remoteThread = RemoteThread(self.newThreadId, self.storeOptions["lzOnly"])
        self.origData = remoteThread.getOrigData()
        self.postList = remoteThread.getFullPostList()
        self.userList = remoteThread.getFullUserListById()

        storeTimestamp = int(time.time() * 1000)
        self.updateStoreOptions({"storeTime": storeTimestamp})
        overwriteThreadInfo = {
            "storeOptions": self.storeOptions,
            **remoteThread.getThreadInfo(),
        }
        self.threadInfo = (
            {**self.threadInfo, **overwriteThreadInfo}
            if self.threadInfo
            else overwriteThreadInfo
        )

        self._storeOrigData(storeTimestamp)
        json_dump(self.threadInfo, os.path.join(self.storeDir, "threadInfo.json"))
        json_dump(self.postList, os.path.join(self.storeDir, "postList.json"))
        json_dump(self.userList, os.path.join(self.storeDir, "userList.json"))

        if self.storeOptions["withAsset"]:
            self.assetList = remoteThread.getFullAssetList()
            self._storeAsset()
            json_dump(self.assetList, os.path.join(self.storeDir, "assetList.json"))
        if self.storeOptions["withPortrait"]:
            portraitList = remoteThread.getFullPortraitList()
            self._storePortrait(portraitList)

        # 更新类自身数据，再次 store 时触发警告
        self._isValid()
        self._fillStoredData()

        return {
            "storeOptions": self.storeOptions,
            "threadInfo": self.threadInfo,
            "postList": self.postList,
            "assetList": self.assetList,
            "origData": self.origData,
        }

    def _updatePostList(self, oldPostList, newPostList):
        oldFloors = sorted([int(post["floor"]) for post in oldPostList])
        newFloors = sorted([int(post["floor"]) for post in newPostList])

        intersectedFloors = []
        newPostedFloors = []
        deletedFloors = sorted(list(set(oldFloors).difference(set(newFloors))))
        for floor in newFloors:
            if floor in oldFloors:
                intersectedFloors.append(
                    {
                        "floor": floor,
                        "oldIndex": oldFloors.index(floor),
                        "newIndex": newFloors.index(floor),
                    }
                )
            else:
                newPostedFloors.append(
                    {
                        "floor": floor,
                        "newIndex": newFloors.index(floor),
                    }
                )

        _updatedFloors = []

        updatedPostList = deepcopy(oldPostList)
        for _floor in intersectedFloors:
            floor, oldIndex, newIndex = _floor.values()
            if updatedPostList[oldIndex] != newPostList[newIndex]:
                _updatedFloors.append(_floor)
                updatedPostList[oldIndex] = newPostList[newIndex]

        for _floor in newPostedFloors:
            _updatedFloors.append(_floor)
            floor, newIndex = _floor.values()
            updatedPostList.append(newPostList[newIndex])
        return {
            "updatedPostList": updatedPostList,
            "deletedFloors": deletedFloors,
            "intersectedFloors": intersectedFloors,
            "newPostedFloors": newPostedFloors,
            "_updateLog": _updatedFloors,
        }

    def _updateAssetList(self, newAssetList, overwriteOldAssetList: dict = None):
        oldAssetList = overwriteOldAssetList or self.assetList
        needUpdateAssetList = {
            "images": [],
            "audios": [],
            "videos": [],
        }
        if oldAssetList and oldAssetList == newAssetList:
            # 无需更新
            pass
        elif oldAssetList:
            # 原先存在资源，更新资源
            for key in ["images", "audios", "videos"]:
                if newAssetList[key]:
                    for asset in newAssetList[key]:
                        if asset not in oldAssetList.get(key, []):
                            # 资源不在已存档列表内，直接下载
                            needUpdateAssetList[key].append(asset)
                        else:
                            # 否则，判断资源是否需要更新
                            oldAsset = oldAssetList[key][oldAssetList[key].index(asset)]
                            newAsset = asset
                            if oldAsset != newAsset:
                                needUpdateAssetList[key].append(asset)
        else:
            needUpdateAssetList = newAssetList
            self._storeAsset(newAssetList)

        for key in ["images", "audios", "videos"]:
            if needUpdateAssetList[key]:
                for asset in needUpdateAssetList[key]:
                    assetFilename = os.path.join(self.assetDir, key, asset["filename"])
                    with open(assetFilename, "wb") as f:
                        f.write(requests.get(asset["src"]).content)

        return {
            "updateAssetList": needUpdateAssetList,
            "newAssetList": newAssetList,
            "oldAssetList": oldAssetList,
        }

    def update(self):
        if not self.isValid:
            raise self.LocalThreadInvalidException()

        # 请求最新贴子信息
        remoteThread = RemoteThread(self.threadInfo["id"], self.storeOptions["lzOnly"])
        origData = remoteThread.getOrigData()

        # 更新贴子列表
        _updatePostInfo = self._updatePostList(
            self.postList, remoteThread.getFullPostList()
        )

        # 更新资源、头像等列表
        newAssetList = remoteThread.getFullAssetList()
        _updateAssetInfo = {}
        if self.storeOptions["withAsset"]:
            _updateAssetInfo = self._updateAssetList(newAssetList)
        if self.storeOptions["withPortrait"]:
            portraitList = remoteThread.getFullPortraitList()
            self._storePortrait(portraitList)
        # 是哪个铸币写完新方法只管 store 不管 update？又是哪个铸币 update 了 4 次才想起这个问题？
        # 哈哈，是我！我是个闪避！哈哈哈
        self.userList |= remoteThread.getFullUserListById()

        # 写入更新日志
        updateTimestamp = int(time.time() * 1000)
        self.updateStoreOptions({"updateTime": updateTimestamp})
        updateLog = {
            "updateTime": updateTimestamp,
            "updatePostInfo": _updatePostInfo["_updateLog"],
            "updateAssetInfo": _updateAssetInfo["updateAssetList"],
        }
        self.storeOptions["updateLog"].append(updateLog)

        # 更新类自身数据
        overwriteThreadInfo = {
            "storeOptions": self.storeOptions,
            **remoteThread.getThreadInfo(),
        }
        self.threadInfo = (
            {**self.threadInfo, **overwriteThreadInfo}
            if self.threadInfo
            else overwriteThreadInfo
        )
        self.postList = _updatePostInfo["updatedPostList"]
        self.assetList = newAssetList
        self.origData = origData

        # 写入更新后的数据
        self._storeOrigData(updateTimestamp)
        json_dump(self.threadInfo, os.path.join(self.storeDir, "threadInfo.json"))
        json_dump(self.postList, os.path.join(self.storeDir, "postList.json"))
        json_dump(self.userList, os.path.join(self.storeDir, "userList.json"))
        json_dump(
            self.assetList, os.path.join(self.storeDir, "assetList.json")
        ) if self.assetList else ...
