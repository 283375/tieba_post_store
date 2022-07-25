import os
import time
import json
import requests
import logging
from copy import deepcopy
from urllib.parse import urlparse
from functools import wraps

from api.tiebaApi import getThread, getSubPost

logger = logging.getLogger("main")


class LightRemoteThread:
    class ThreadInvalidError(Exception):
        def __init__(self, response: dict):
            self.code = response.get("error_code")
            self.message = response.get("error_msg")

        def __str__(self):
            return f'[{self.__class__.__name__}] 错误 {self.code or "(无代码)"}：{self.message or "无消息"}'

    def __init__(self, threadId, lzOnly: bool = True, fullSubpost: bool = False):
        thread = getThread(threadId, page=1, lzOnly=lzOnly)
        self.dataRequestTime = int(time.time() * 1000)
        if thread.get("page") is None:
            raise self.ThreadInvalidError(thread)
        if fullSubpost:
            for post in thread["post_list"]:
                subpostNum = int(post["sub_post_number"])
                if subpostNum > 0:
                    subpostInfo = getSubPost(threadId, post["id"], 0, rn=subpostNum)
                    post["sub_post_list"] = subpostInfo["subpost_list"]
        self.origData = thread

    def getThreadInfo(self):
        base = self.origData["thread"]
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
        }


class RemoteThread:
    class ThreadInvalidError(Exception):
        def __init__(self, response: dict):
            self.code = response.get("error_code")
            self.message = response.get("error_msg")

        def __str__(self):
            return f'[{self.__class__.__name__}] 错误 {self.code or "(无代码)"}：{self.message or "无消息"}'

    class DataNotRequestedError(Exception):
        def __init__(self):
            self.message = f"{self.__class__.__name__} 尚未请求数据，请先调用 requestData()。"

        def __str__(self):
            return self.message

    def __init__(self, threadId, lzOnly=False, lazyRequest=False):
        """
        __init__ 初始化网络贴子数据

        :param threadId: 贴子 ID
        :type threadId: str | int
        :param lzOnly: 只看楼主，默认为 False
        :type lzOnly: bool, optional
        :param lazyRequest: 延迟数据请求，默认为 False。开启后，只有调用 requestData() 后才会发起网络请求，也许对 GUI 应用很有用。
        :type lazyRequest: bool, optional
        """
        self.threadId = threadId
        self.lzOnly = lzOnly

        self.totalPage = None

        self.origData = {}
        self.threadInfo = None
        self.posts = None
        self.assets = None

        self.dataRequested = False
        self.dataRequestTime = None
        if not lazyRequest:
            self.requestData(self.lzOnly)

    @property
    def totalPageRange(self):
        if self.totalPage:
            return range(1, self.totalPage + 1)

    def requestData(self, lzOnly):
        preRequest = getThread(self.threadId, page=1, lzOnly=lzOnly)
        if preRequest.get("page") is None:
            raise self.ThreadInvalidError(preRequest)

        self.dataRequestTime = int(time.time() * 1000)
        self.totalPage = int(preRequest["page"]["total_page"])

        for page in self.totalPageRange:
            thread = getThread(self.threadId, page=page, lzOnly=lzOnly)
            for post in thread["post_list"]:
                subpostNum = int(post["sub_post_number"])
                if subpostNum > 0:
                    subpostInfo = getSubPost(
                        self.threadId,
                        postId=post["id"],
                        subpostId=0,
                        rn=subpostNum,
                    )
                    post["sub_post_list"] = subpostInfo["subpost_list"]
            self.origData[f"page_{page}"] = thread
        self.dataRequested = True

    def DataRequested(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not self.dataRequested:
                raise self.DataNotRequestedError()
            else:
                return func(self, *args, **kwargs)

        return wrapper

    @DataRequested
    def getOrigData(self):
        return self.origData

    @DataRequested
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
        }

    def sortPost(self, posts):
        return sorted(posts, key=lambda x: int(x["floor"]))

    @DataRequested
    def getPosts(self, page=1):
        try:
            postList = self.origData[f"page_{page}"]["post_list"]
            return self.sortPost(postList)
        except KeyError as e:
            raise IndexError(f"Page {page} does not exist.") from e

    @DataRequested
    def getFullPosts(self):
        fullList = []
        for pageNum in self.totalPageRange:
            fullList += self.getPosts(pageNum)
        return self.sortPost(fullList)

    def analyzeAsset(self, postContents):
        assets = []
        for contentBlock in postContents:
            contentType = contentBlock["type"]
            if contentType == "3":  # image
                assets.append(
                    {
                        "type": "image",
                        "src": contentBlock["origin_src"],
                        "id": contentBlock["pic_id"],
                        "size": contentBlock["size"],
                        "filename": f'{contentBlock["pic_id"]}{os.path.splitext(os.path.basename(urlparse(contentBlock["origin_src"]).path))[1]}',
                    }
                )

            elif contentType == "5":  # video
                assets.append(
                    {
                        "type": "video",
                        "src": contentBlock["link"],
                        "size": contentBlock["origin_size"],
                        "filename": os.path.basename(urlparse(contentBlock["link"]).path),
                    }
                )
            elif contentType == "10":  # audio
                assets.append(
                    {
                        "type": "audio",
                        "md5": contentBlock["voice_md5"],
                        "src": f'http://c.tieba.baidu.com/c/p/voice?voice_md5={contentBlock["voice_md5"]}&play_from=pb_voice_play',
                        "filename": f'{contentBlock["voice_md5"]}.mp3',
                    }
                )
            """
            elif contentType == "20":  # [?] maybe memePic
                imageList.append(content)
            """
        return assets

    @DataRequested
    def getAssets(self, page=1):
        posts = self.getPosts(page)
        assets = []
        for post in posts:
            assets += self.analyzeAsset(post["content"])
        return assets

    @DataRequested
    def getFullAssets(self):
        fullAssets = []
        for pageNum in self.totalPageRange:
            fullAssets += self.getAssets(pageNum)
        return fullAssets

    @DataRequested
    def getUserList(self, page=1):
        return self.origData[f"page_{page}"]["user_list"]

    @DataRequested
    def getFullUsers(self):
        fullUserList = []
        fullUserIdList = [user["id"] for user in fullUserList]

        for pageNum in self.totalPageRange:
            userList = self.getUserList(pageNum)
            for user in userList:
                if user["id"] not in fullUserIdList:
                    fullUserList.append(user)
        return fullUserList

    @DataRequested
    def getUsersById(self, page=1):
        userList = self.getUserList(page)
        return {user["id"]: user for user in userList}

    @DataRequested
    def getFullUsersById(self):
        fullUserList = {}
        for pageNum in self.totalPageRange:
            userList = self.getUsersById(pageNum)
            fullUserList |= userList
        return fullUserList

    @DataRequested
    def getPortraits(self, page=1):
        userList = self.getUserList(page)
        return [
            {
                "id": user["id"],
                "portrait": user["portrait"],
                "src": "http://tb.himg.baidu.com/sys/portrait/item/" + user["portrait"],
            }
            for user in userList
        ]

    @DataRequested
    def getFullPortraits(self):
        fullPortraitList = []
        for pageNum in self.totalPageRange:
            fullPortraitList += self.getPortraits(pageNum)
        return fullPortraitList


class LocalThread:
    class LocalThreadNoOverwriteError(Exception):
        def __init__(self):
            self.message = "不允许使用新 ID 覆盖一个有效的存档。"

        def __str__(self) -> str:
            return self.message

    class LocalThreadInvalidError(Exception):
        def __init__(self):
            self.message = "存档目录损坏或无效。"

        def __str__(self) -> str:
            return self.message

    def __init__(self, storeDir: str, newThreadId: int = None, override: bool = False):
        """
        __init__ 初始化本地贴子存档目录

        :param storeDir: 贴子存档目录
        :type storeDir: str
        :param newThreadId: 新存档的贴子 ID，默认为 None
        :type newThreadId: int, optional
        :raises self.LocalThreadNoOverwriteError: 若原存档目录有效且传入了 `newThreadId`，则抛出此异常
        """
        self.storeDir = os.path.abspath(storeDir)
        self.assetDir = os.path.join(self.storeDir, "assets")
        self.portraitDir = os.path.join(self.storeDir, "portraits")
        self.newThreadId = newThreadId

        self.storeOptions = {
            "__VERSION__": 2,
            "lzOnly": False,
            "assets": False,
            "portraits": False,
        }
        self.updateInfo = {
            "storeTime": None,
            "updateTime": None,
            "updateLog": {},
        }

        self.threadInfo = None
        self.posts = None
        self.users = None
        self.assets = None
        self.portraits = None
        self.origData = None
        self.remoteThread = None

        self.isValid = False
        self.__checkValid()
        if self.isValid:
            if newThreadId:
                raise self.LocalThreadNoOverwriteError()
            self._fillLocalData()

    @property
    def threadId(self):
        return (self.threadInfo and self.threadInfo.get("id")) or self.newThreadId

    def __log(self, msg, level: int = logging.DEBUG):
        logger.log(level, f"LocalThread({self.threadId}): {msg}")

    def __checkValid(self):
        def __test(filename):
            with open(filename, "r", encoding="utf-8") as f:
                json.load(f)

        try:
            __test(os.path.join(self.storeDir, "threadInfo.json"))
            __test(os.path.join(self.storeDir, "posts.json"))
            __test(os.path.join(self.storeDir, "users.json"))
            self.isValid = True
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.isValid = False
            if self.newThreadId is None:
                raise self.LocalThreadInvalidError() from e

    def updateStoreOptions(self, _overwriteOptions: dict):
        """
        updateStoreOptions 更新贴子的存档选项

        调用该方法的同时会检测 `assets` 及 `portraits` 目录是否存在并自动创建，减少报错的风险。

        >>> updateStoreOptions({"assets": True})
        # 若 assets 目录不存在则自动创建

        :param _overwriteOptions: 要覆盖的存档选项
        :type _overwriteOptions: dict
        """
        overwriteOptions = deepcopy(_overwriteOptions)
        overwriteOptions.pop("__VERSION__", None)
        for storeOpt, dirName in [("assets", "assets"), ("portraits", "portraits")]:
            if overwriteOptions.get(storeOpt, False):
                os.makedirs(os.path.join(self.storeDir, dirName), exist_ok=True)
        self.storeOptions = {**self.storeOptions, **overwriteOptions}

    def _fillLocalData(self):
        def loadLocalJson(file):
            with open(os.path.join(self.storeDir, file), "r", encoding="utf-8") as f:
                return json.load(f)

        try:
            threadInfo = loadLocalJson("threadInfo.json")
            self.storeOptions = threadInfo.pop("storeOptions")
            self.updateInfo = threadInfo.pop("updateInfo")
            self.threadInfo = threadInfo
            self.updateStoreOptions(self.storeOptions)
            self.posts = loadLocalJson("posts.json")
            self.users = loadLocalJson("users.json")

            if self.storeOptions["assets"]:
                self.assets = loadLocalJson("assets.json")
            if self.storeOptions["portraits"]:
                self.portraits = loadLocalJson("portraits.json")
        except FileNotFoundError as e:
            raise self.LocalThreadInvalidError() from e

    def _fillRemoteData(self):
        self.remoteThread = RemoteThread(self.newThreadId or self.threadInfo.get("id"), self.storeOptions["lzOnly"])
        return self.remoteThread

    def _storeAssets(self, assets=None):
        for assetObj in assets:
            assetSortedDir = os.path.join(self.assetDir, assetObj["type"])
            os.makedirs(assetSortedDir, exist_ok=True)

            with open(os.path.join(assetSortedDir, assetObj["filename"]), "wb") as f:
                self.__log(f"正在保存资源 {assetObj['filename']}")
                f.write(requests.get(assetObj["src"]).content)
            yield assetObj

    def _storePortraits(self, portraits: list = None):
        for portrait in portraits:
            portraitFilename = os.path.join(self.portraitDir, f'{portrait["id"]}.jpg')
            self.__log(f'正在保存头像 {portrait["portrait"]}(ID {portrait["id"]})')
            with open(portraitFilename, "wb") as f:
                f.write(requests.get(portrait["src"]).content)
            yield portrait

    def _storeOrigData(self, timestamp):
        os.makedirs(os.path.join(self.storeDir, "origData"), exist_ok=True)
        with open(
            os.path.join(self.storeDir, "origData", f"{timestamp}.json"),
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(self.origData, f, ensure_ascii=False, indent=2)

    def _writeDataToFile(self):
        def _writeJson(filename, data):
            with open(os.path.join(self.storeDir, filename), "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        self._storeOrigData(self.remoteThread.dataRequestTime)
        threadInfo = {
            **self.threadInfo,
            "storeOptions": self.storeOptions,
            "updateInfo": self.updateInfo,
        }
        _writeJson("threadInfo.json", threadInfo)
        _writeJson("posts.json", self.posts)
        _writeJson("users.json", self.users)
        if self.storeOptions["assets"]:
            _writeJson("assets.json", self.assets)
        if self.storeOptions["portraits"]:
            _writeJson("portraits.json", self.portraits)

    def _store(self):
        # yield(step, [progress, totalProgress], extraData)
        self.__log(f"开始存档 {self.threadId}", logging.INFO)

        yield (0, [0, -1], None)
        _data = {
            "update": {"posts": None, "assets": None, "portraits": None},
            "download": {"assets": [], "portraits": []},
        }
        yield (0, [0, -1], self._fillRemoteData())
        os.makedirs(self.storeDir, exist_ok=True)

        yield (1, [0, 1], None)
        # Analyze & update data
        self.threadInfo = self.remoteThread.getThreadInfo()
        self.users = self.remoteThread.getFullUsersById()
        self.origData = self.remoteThread.getOrigData()
        if self.isValid:
            _a = self._updateAssets() if self.storeOptions["assets"] else []
            _p = self._updatePortraits() if self.storeOptions["portraits"] else []
            _data["update"]["posts"] = self._updatePosts()
            _data["update"]["assets"] = _data["download"]["assets"] = _a
            _data["update"]["portraits"] = _data["download"]["portraits"] = _p

            updateTime = self.remoteThread.dataRequestTime
            self.updateInfo["updateTime"] = updateTime
            self.updateInfo["updateLog"][updateTime] = _data["update"]
        else:
            self.posts = self.remoteThread.getFullPosts()
            if self.storeOptions["assets"]:
                self.assets = self.remoteThread.getFullAssets()
                _data["download"]["assets"] = self.assets
            if self.storeOptions["portraits"]:
                self.portraits = self.remoteThread.getFullPortraits()
                _data["download"]["portraits"] = self.portraits
            self.updateInfo["storeTime"] = self.remoteThread.dataRequestTime
        yield (1, [1, 1], _data)

        # Download data
        #  Caculate total number
        __len = len(_data["download"]["assets"]) + len(_data["download"]["portraits"])
        __progress = 0

        yield (2, [0, __len or 1], None)
        #  Download & yield progress
        if __len:
            if _data["download"]["assets"]:
                for _ in self._storeAssets(_data["download"]["assets"]):
                    __progress += 1
                    yield (2, [__progress, __len], _)
            if _data["download"]["portraits"]:
                for _ in self._storePortraits(_data["download"]["portraits"]):
                    __progress += 1
                    yield (2, [__progress, __len], _)
        else:
            yield (2, [1, 1], None)

        # Writing data to files
        yield (3, [0, 1], None)
        self._writeDataToFile()
        self.__checkValid()
        self._fillLocalData()
        yield (3, [1, 1], None)
        self.__log("存档完成！", logging.INFO)

    def _updatePosts(self, _new: list = None, _old: list = None) -> list:
        # WARNING: NOT TESTED
        newPosts = _new or self.remoteThread.getFullPosts() or []
        oldPosts = _old or self.posts or []
        _updateLog = []

        oldFloors = {int(post["floor"]): post for post in oldPosts}
        newFloors = {int(post["floor"]): post for post in newPosts}
        newLastFloor = int(list(newFloors.values())[-1]["floor"])
        oldLastFloor = int(list(oldFloors.values())[-1]["floor"])

        lastFloor = max(oldLastFloor, newLastFloor)
        updatedPosts = []
        for floorNum in range(1, int(lastFloor) + 1):
            floor = None
            if floorNum in newFloors and floorNum in oldFloors:
                floor = newFloors.get(floorNum, oldFloors.get(floorNum))
                # 单独更新楼中楼（以防回复被举报/异常消失等情况）
                oldSubPosts = {sp["id"]: sp for sp in oldFloors[floorNum]["sub_post_list"]}
                newSubPosts = {sp["id"]: sp for sp in newFloors[floorNum]["sub_post_list"]}
                subPosts = sorted(
                    list((oldSubPosts | newSubPosts).values()),
                    key=lambda x: int(x["time"]),
                )
                floor["sub_post_list"] = subPosts

                if floor != oldFloors[floorNum] or oldSubPosts != newSubPosts:
                    _updateLog.append(floorNum)
            elif floorNum in newFloors:
                floor = newFloors[floorNum]
                _updateLog.append(floorNum)
            elif floorNum in oldFloors:
                floor = oldFloors[floorNum]
            else:
                self.__log(f"{floorNum} 楼完全缺失", logging.INFO)
            if floor is not None:
                updatedPosts.append(floor)

        self.posts = updatedPosts
        return _updateLog

    def _updateAssets(self, _new: list = None, _old: list = None) -> list:
        # WARNING: NOT TESTED
        newAssets = _new or self.remoteThread.getFullAssets() or []
        oldAssets = _old or self.assets or []

        downloadAssets = []
        if newAssets == oldAssets:
            self.__log("无需更新资源", logging.INFO)
        else:
            combinedAssets = newAssets + oldAssets
            duplicatedAssets = list(set(combinedAssets))
            downloadAssets = [assetObj for assetObj in combinedAssets if assetObj not in duplicatedAssets]
            __sort_order = lambda x: {"image": 1, "video": 2, "audio": 3}[x["type"]]
            self.assets = sorted(combinedAssets, key=__sort_order)

        return downloadAssets

    def _updatePortraits(self, _new: list = None, _old: list = None) -> list:
        newPortraits = _new or self.remoteThread.getFullPortraits() or {}
        oldPortraits = _old or self.portraits or {}
        # WARNING: NOT TESTED
        oldPortraitsById = {portrait["id"]: portrait for portrait in oldPortraits}
        newPortraitsById = {portrait["id"]: portrait for portrait in newPortraits}

        downloadPortraits = [
            newPortraitValue
            for newPortraitId, newPortraitValue in newPortraitsById.items()
            if oldPortraitsById.get(newPortraitId) != newPortraitValue
        ]

        self.portraits = list((oldPortraitsById | newPortraitsById).values())
        return downloadPortraits


def getLocalThreadInfo(t: LocalThread):
    ver = t.storeOptions["__VERSION__"]
    info = {
        "__VERSION__": ver,
        "threadId": None,
        "title": None,
        "author": {
            "id": None,
            "displayName": None,
            "origName": None,
        },
        "storeDir": None,
        "createTime": None,
        "storeTime": None,
        "updateTime": None,
    }
    # if ver == 1: 胎死腹中的破烂版本，没人用得着的
    if ver == 2:
        info["threadId"] = t.threadInfo["id"]
        info["title"] = t.threadInfo["title"]
        info["author"] = t.threadInfo["author"]
        info["storeDir"] = t.storeDir
        info["createTime"] = int(t.threadInfo["createTime"]) * 1000
        info["storeTime"] = t.updateInfo["storeTime"]
        info["updateTime"] = t.updateInfo["updateTime"]
    # elif ver == 3: 也许用得着，谁知道呢
    return info
