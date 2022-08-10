import os
import time
import json
import requests
import logging
from copy import deepcopy
from urllib.parse import urlparse
from functools import wraps

from api.tiebaApi import getThread, getSubPost
from utils.progress import Progress, ProgressType


class TiebaAsset:
    Image = 0
    Video = 1
    Audio = 2
    Portrait = 3
    __types = ["image", "video", "audio", "portrait"]

    def getRoleName(self):
        return self.__types[self.type]

    def loadFromApiResult(self, type: int, src: str, filename: str, **kwargs):
        """
        General { src: 资源 URL 地址, filename: 资源文件名 }
        Image { id: 图片 ID, size: 图片文件大小 }
        Video { size: 视频文件大小 }
        Audio { md5: 音频 MD5 值 }
        Portrait { id: 用户 ID, portrait: 用户 portrait }
        """
        self.type = type
        self.src = src
        self.filename = filename
        self.__kwargs = kwargs.copy()
        return self

    def loadFromDict(self, _dict: dict):
        __dict = _dict.copy()
        self.type = self.__types.index(__dict.pop("type"))
        self.src = __dict.pop("src")
        self.filename = __dict.pop("filename")
        self.__kwargs = __dict
        return self

    def get(self, key: str):
        return self.__kwargs.get(key)

    def toDict(self):
        basic = {"type": self.getRoleName(), "src": self.src, "filename": self.filename}
        kwargs = self.__kwargs
        if self.type == self.Image:
            basic |= {"id": kwargs["id"], "size": kwargs["size"]}
        elif self.type == self.Video:
            basic |= {"size": kwargs["size"]}
        elif self.type == self.Audio:
            basic |= {"md5": kwargs["md5"]}
        elif self.type == self.Portrait:
            basic |= {"id": kwargs["id"], "portrait": kwargs["portrait"]}
        return basic

    def __uniqueKey(self):
        key = 0
        if self.type in [self.Image, self.Portrait]:
            key = self.__kwargs["id"]
        elif self.type == self.Audio:
            key = self.__kwargs["md5"]
        return (self.type, self.src, self.filename, key)

    def __hash__(self):
        return hash(self.__uniqueKey())

    def __eq__(self, other):
        return hash(self) == hash(other)


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


class RemoteThread(LightRemoteThread):
    logger = logging.getLogger("root.api.RemoteThread")

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

    def _requestData(self, _lzOnly: bool = None):
        lzOnly = _lzOnly if _lzOnly is not None else self.lzOnly
        self.logger.debug(f"处理 {self.threadId} 元数据")
        preRequest = getThread(self.threadId, page=1, lzOnly=lzOnly)
        if preRequest.get("page") is None:
            raise self.ThreadInvalidError(preRequest)

        self.dataRequestTime = int(time.time() * 1000)
        self.totalPage = int(preRequest["page"]["total_page"])

        pageProgress = Progress("RemoteThread-Page", "页面", "正在更新页面")
        postProgress = Progress("RemoteThread-Post", "回复贴")

        yield pageProgress._updateProgress(0, self.totalPage)
        for page in self.totalPageRange:
            self.logger.debug(f"请求 {self.threadId} > P{page} 数据")
            thread = getThread(self.threadId, page=page, lzOnly=lzOnly)
            yield postProgress._updateProgress(0, len(thread["post_list"]))
            for i, post in enumerate(thread["post_list"]):
                yield postProgress._updateText(str(post["id"]))
                subpostNum = int(post["sub_post_number"])
                if subpostNum > 0:
                    subposts = []
                    self.logger.debug(f'处理 {self.threadId} > P{page} > 楼中楼 {post["id"]} 数据')
                    preRequest = getSubPost(self.threadId, post["id"], page=1)
                    subposts += preRequest["subpost_list"]
                    if int(preRequest["page"]["total_page"]) > 1:
                        pages = range(2, int(preRequest["page"]["total_page"]) + 1)
                        for _page in pages:
                            self.logger.debug(f'请求 {self.threadId} > P{page} > 楼中楼 {post["id"]} > P{_page} 数据')
                            subposts += getSubPost(self.threadId, post["id"], page=_page)["subpost_list"]
                    post["sub_post_list"] = subposts
                yield postProgress._updateProgress(i + 1)
            yield pageProgress._updateProgress(page)

            self.origData[f"page_{page}"] = thread
        self.dataRequested = True

    def requestData(self):
        for _ in self._requestData():
            _

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
                    TiebaAsset().loadFromApiResult(
                        type=TiebaAsset.Image,
                        src=contentBlock["origin_src"],
                        filename=f'{contentBlock["pic_id"]}{os.path.splitext(os.path.basename(urlparse(contentBlock["origin_src"]).path))[1]}',
                        id=contentBlock["pic_id"],
                        size=contentBlock["size"],
                    )
                )
            elif contentType == "5":  # video
                assets.append(
                    TiebaAsset().loadFromApiResult(
                        type=TiebaAsset.Video,
                        src=contentBlock["link"],
                        filename=os.path.basename(urlparse(contentBlock["link"]).path),
                        size=contentBlock["origin_size"],
                    )
                )
            elif contentType == "10":  # audio
                assets.append(
                    TiebaAsset().loadFromApiResult(
                        type=TiebaAsset.Audio,
                        src=f'http://c.tieba.baidu.com/c/p/voice?voice_md5={contentBlock["voice_md5"]}&play_from=pb_voice_play',
                        filename=f'{contentBlock["voice_md5"]}.mp3',
                        md5=contentBlock["voice_md5"],
                    )
                )

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
    def getUsersById(self, page=1):
        users = {}
        # 先行获取所有楼中楼内发言的用户
        for post in self.getPosts(page):
            if subposts := post.get("sub_post_list"):
                for subpost in subposts:
                    users[subpost["author"]["id"]] = subpost["author"]
        # 再用 user_list 内包含的用户信息进行更新
        for user in self.origData[f"page_{page}"]["user_list"]:
            users[user["id"]] = user
        return users

    @DataRequested
    def getFullUsersById(self):
        fullUsers = {}
        for pageNum in self.totalPageRange:
            fullUsers |= self.getUsersById(pageNum)
        return fullUsers

    @DataRequested
    def getUsers(self, page=1):
        return list(self.getUsersById(page).values())

    @DataRequested
    def getFullUsers(self):
        fullUsers = []
        for pageNum in self.totalPageRange:
            fullUsers += self.getUsers(pageNum)
        return fullUsers

    @DataRequested
    def getPortraits(self, page=1):
        users = self.getUsers(page)
        return [
            TiebaAsset().loadFromApiResult(
                type=TiebaAsset.Portrait,
                src=f'http://tb.himg.baidu.com/sys/portrait/item/{user["portrait"]}',
                filename=f'{user["id"]}.jpg',
                portrait=user["portrait"],
                id=user["id"],
            )
            for user in users
        ]

    @DataRequested
    def getFullPortraits(self):
        fullPortraitList = []
        for pageNum in self.totalPageRange:
            fullPortraitList += self.getPortraits(pageNum)
        return fullPortraitList


class LocalThread:
    logger = logging.getLogger("root.api.LocalThread")

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

        self.isValid = False
        self.__checkValid()
        if self.isValid:
            if newThreadId:
                raise self.LocalThreadNoOverwriteError()
            self._fillLocalData()
        self.remoteThread = RemoteThread(self.threadId, self.storeOptions["lzOnly"], lazyRequest=True)

    @property
    def threadId(self):
        return (self.threadInfo and self.threadInfo.get("id")) or self.newThreadId

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
                self.assets = [TiebaAsset().loadFromDict(_dict) for _dict in loadLocalJson("assets.json")]
            if self.storeOptions["portraits"]:
                self.portraits = [TiebaAsset().loadFromDict(_dict) for _dict in loadLocalJson("portraits.json")]
        except FileNotFoundError as e:
            raise self.LocalThreadInvalidError() from e

    def _fillRemoteData(self):
        yield from self.remoteThread._requestData()

    def _requestAsset(self, filepath, src, progressText=None, max_retry: int = 3):
        for count in range(max_retry):
            try:
                with open(filepath, "wb") as f:
                    req = requests.get(src, stream=True)
                    progress = Progress("LocalThread-DownloadAsset", type=ProgressType.Byte)
                    totalSize = int(req.headers.get("Content-Length", 0))
                    progress.update(0, totalSize, progressText)
                    for part in req.iter_content(chunk_size=512):
                        size = f.write(part)
                        yield progress.increase(size if totalSize else 0)
            except (requests.ConnectTimeout, requests.ReadTimeout) as e:
                if count + 1 == max_retry:
                    raise e
                else:
                    self.logger.warning(f"(第 {count} 次重试) 请求 {src} 失败: {str(e)}")

    def _storeAssets(self, assets: list[TiebaAsset] = None):
        for asset in assets:
            assetSortedDir = os.path.join(self.assetDir, asset.getRoleName())
            os.makedirs(assetSortedDir, exist_ok=True)

            self.logger.debug(f"正在保存资源 {asset.filename}: {asset.src}")
            yield from self._requestAsset(os.path.join(assetSortedDir, asset.filename), asset.src, asset.filename)
            yield asset

    def _storePortraits(self, portraits: list[TiebaAsset] = None):
        for portrait in portraits:
            self.logger.debug(f'正在保存头像 {portrait.get("portrait")}(ID {portrait.get("id")})')
            portraitPath = os.path.join(self.portraitDir, portrait.filename)
            yield from self._requestAsset(portraitPath, portrait.src, portrait.get("id"))
            yield portrait

    def _storeOrigData(self, timestamp):
        os.makedirs(os.path.join(self.storeDir, "origData"), exist_ok=True)
        with open(
            os.path.join(self.storeDir, "origData", f"{timestamp}.json"),
            "w",
            encoding="utf-8",
        ) as f:
            json.dump({"__storeTimestamp": timestamp, **self.origData}, f, ensure_ascii=False, indent=2)

    def _writeDataToFile(self):
        __len = 4 + int(self.storeOptions["assets"]) + int(self.storeOptions["portraits"])
        __progress = Progress("LocalThread-WriteData", "保存数据")
        yield __progress.update(tp=__len)

        def __saveData(filename, data):
            nonlocal __progress
            __progress.update(text=filename)
            with open(os.path.join(self.storeDir, filename), "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return __progress.increase()

        self._storeOrigData(self.remoteThread.dataRequestTime)
        yield __progress.increase()
        threadInfo = {
            **self.threadInfo,
            "storeOptions": self.storeOptions,
            "updateInfo": self.updateInfo,
        }
        yield __saveData("threadInfo.json", threadInfo)
        yield __saveData("posts.json", self.posts)
        yield __saveData("users.json", self.users)
        if self.storeOptions["assets"]:
            yield __saveData("assets.json", [_.toDict() for _ in self.assets])
        if self.storeOptions["portraits"]:
            yield __saveData("portraits.json", [_.toDict() for _ in self.portraits])

    def _store(self):
        # yield Progress(...)
        self.logger.info(f"开始存档 {self.threadId}")

        stepProgress = Progress("LocalThread-Step", "步骤")
        stepProgress.update(tp=5)
        detailProgress = Progress("LocalThread-Detail", "详情")

        yield stepProgress.update(text="正在请求最新数据")
        yield stepProgress.increase()
        _data = {
            "update": {"posts": None, "assets": None, "portraits": None},
            "download": {"assets": [], "portraits": []},
        }
        yield from self._fillRemoteData()
        os.makedirs(self.storeDir, exist_ok=True)

        # Analyze & update data
        yield stepProgress.update(text="正在分析数据")
        yield stepProgress.increase()
        self.threadInfo = self.remoteThread.getThreadInfo()
        self.users = self.remoteThread.getFullUsersById()
        self.origData = self.remoteThread.getOrigData()
        if self.isValid:
            _a = self._updateAssets() if self.storeOptions["assets"] else []
            _p = self._updatePortraits() if self.storeOptions["portraits"] else []
            _data["update"]["posts"] = self._updatePosts()
            _data["download"]["assets"] = _a
            _data["download"]["portraits"] = _p
            _data["update"]["assets"] = [_.toDict() for _ in _a]
            _data["update"]["portraits"] = [_.toDict() for _ in _a]

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

        # Download data
        #  Caculate total number
        __len = len(_data["download"]["assets"]) + len(_data["download"]["portraits"])
        yield stepProgress.update(text="正在下载资源")
        yield stepProgress.increase()
        yield detailProgress.update(0, __len or 1, "下载资源")

        #  Download & yield progress
        if __len:
            if _data["download"]["assets"]:
                for _ in self._storeAssets(_data["download"]["assets"]):
                    if type(_) == Progress:
                        yield _
                    elif type(_) == TiebaAsset:
                        yield detailProgress.increase()
            if _data["download"]["portraits"]:
                for _ in self._storePortraits(_data["download"]["portraits"]):
                    if type(_) == Progress:
                        yield _
                    elif type(_) == TiebaAsset:
                        yield detailProgress.increase()
        else:
            yield detailProgress.increase()

        # Writing data to files
        yield stepProgress.update(text="将数据写入文件")
        yield stepProgress.increase()
        yield from self._writeDataToFile()
        yield stepProgress.update(text="整理数据")
        yield stepProgress.increase()
        self.__checkValid()
        self._fillLocalData()
        self.logger.info(f"存档 {self.threadId} 完成！")

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
                    key=lambda x: int(x["id"]),
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
                self.logger.info(f"{self.threadId} > {floorNum} 楼完全缺失")
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
            self.logger.info(f"{self.threadId} 无需更新资源")
        else:
            combinedAssets = newAssets + oldAssets
            duplicatedAssets = list(set(combinedAssets))
            downloadAssets = [assetObj for assetObj in combinedAssets if assetObj not in duplicatedAssets]
            self.assets = combinedAssets

        return downloadAssets

    def _updatePortraits(self, _new: list[TiebaAsset] = None, _old: list[TiebaAsset] = None) -> list:
        # WARNING: NOT TESTED
        newPortraits = set(_new or self.remoteThread.getFullPortraits() or [])
        oldPortraits = set(_old or self.portraits or [])
        oldPortraitsById = {portrait.get("id"): portrait for portrait in oldPortraits}
        newPortraitsById = {portrait.get("id"): portrait for portrait in newPortraits}

        downloadPortraits = [
            newPortrait
            for newPortraitId, newPortrait in newPortraitsById.items()
            if oldPortraitsById.get(newPortraitId) != newPortrait
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
