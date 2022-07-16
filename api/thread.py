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

    def isDataRequested(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not self.dataRequested:
                raise self.DataNotRequestedException()
            else:
                return func(self, *args, **kwargs)

        return wrapper

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
        }

    def sortPost(self, posts):
        return sorted(posts, key=lambda x: int(x["floor"]))

    @isDataRequested
    def getPosts(self, page=1):
        try:
            postList = self.origData[f"page_{page}"]["post_list"]
            return self.sortPost(postList)
        except KeyError as e:
            raise IndexError(f"Page {page} does not exist.") from e

    @isDataRequested
    def getFullPosts(self):
        fullList = []
        for pageNum in self.totalPageRange:
            fullList += self.getPosts(pageNum)
        return self.sortPost(fullList)

    def analyzeAsset(self, postContents):
        assets = {"images": [], "videos": [], "audios": []}
        for contentBlock in postContents:
            contentType = contentBlock["type"]
            if contentType == "3":  # image
                assets["images"].append(
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
                assets["videos"].append(
                    {
                        "src": contentBlock["link"],
                        "size": contentBlock["origin_size"],
                        "filename": os.path.basename(
                            urlparse(contentBlock["link"]).path
                        ),
                    }
                )
            elif contentType == "10":  # audio
                assets["audios"].append(
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
        return assets

    @isDataRequested
    def getAssets(self, page=1):
        postList = self.getPosts(page)
        assets = {"images": [], "audios": [], "videos": []}
        for post in postList:
            analyzedAssets = self.analyzeAsset(post["content"])
            assets["images"] += analyzedAssets["images"]
            assets["audios"] += analyzedAssets["audios"]
            assets["videos"] += analyzedAssets["videos"]
        return assets

    @isDataRequested
    def getFullAssets(self):
        fullAssets = {"images": [], "audios": [], "videos": []}
        for pageNum in self.totalPageRange:
            analyzedAsset = self.getAssets(pageNum)
            fullAssets["images"] += analyzedAsset["images"]
            fullAssets["audios"] += analyzedAsset["audios"]
            fullAssets["videos"] += analyzedAsset["videos"]
        return fullAssets

    @isDataRequested
    def getUserList(self, page=1):
        return self.origData[f"page_{page}"]["user_list"]

    @isDataRequested
    def getFullUsers(self):
        fullUserList = []
        fullUserIdList = [user["id"] for user in fullUserList]

        for pageNum in self.totalPageRange:
            userList = self.getUserList(pageNum)
            for user in userList:
                if user["id"] not in fullUserIdList:
                    fullUserList.append(user)
        return fullUserList

    @isDataRequested
    def getUsersById(self, page=1):
        userList = self.getUserList(page)
        return {user["id"]: user for user in userList}

    @isDataRequested
    def getFullUsersById(self):
        fullUserList = {}
        for pageNum in self.totalPageRange:
            userList = self.getUsersById(pageNum)
            fullUserList |= userList
        return fullUserList

    @isDataRequested
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

    @isDataRequested
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
            "__VERSION__": 2,
            "lzOnly": False,
            "withAsset": False,
            "withPortrait": False,
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
        self._isValid()
        if self.isValid:
            if newThreadId:
                raise self.LocalThreadNoOverwriteError()
            self._fillLocalData()

    def _isValid(self):
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
            raise self.LocalThreadInvalidError() from e

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

            if self.storeOptions["withAsset"]:
                self.assets = loadLocalJson("assets.json")
            if self.storeOptions["withPortrait"]:
                self.portraits = loadLocalJson("portraits.json")
        except FileNotFoundError as e:
            raise self.LocalThreadInvalidError() from e

    def _fillRemoteData(self):
        self.remoteThread = RemoteThread(
            self.newThreadId or self.threadInfo.get("id"), self.storeOptions["lzOnly"]
        )
        return True

    def _storeAsset(self, assets=None):
        for key in ["images", "audios", "videos"]:
            if assets[key]:
                storeAssetKeyPath = os.path.join(self.assetDir, key)
                os.makedirs(storeAssetKeyPath, exist_ok=True)

                for asset in assets[key]:
                    with open(
                        os.path.join(storeAssetKeyPath, asset["filename"]), "wb"
                    ) as f:
                        logger.debug(f"正在保存资源 {asset['filename']}")
                        f.write(requests.get(asset["src"]).content)
                yield asset
        return assets

    def _storePortrait(self, portraits: list = None):
        for portrait in portraits:
            portraitFilename = os.path.join(self.portraitDir, f'{portrait["id"]}.jpg')
            logger.debug(f'正在保存头像 {portrait["portrait"]}(ID {portrait["id"]})……')
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

    def _storeDataToFile(self):
        def _writeJson(filename, data):
            with open(
                os.path.join(self.storeDir, filename), "w", encoding="utf-8"
            ) as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        logger.debug("将数据写入文件……")
        self._storeOrigData(self.remoteThread.dataRequestTime)
        threadInfo = {
            **self.threadInfo,
            "storeOptions": self.storeOptions,
            "updateInfo": self.updateInfo,
        }
        _writeJson("threadInfo.json", threadInfo)
        _writeJson("posts.json", self.posts)
        _writeJson("users.json", self.users)
        if self.storeOptions["withAsset"]:
            _writeJson("assets.json", self.assets)
        if self.storeOptions["withPortrait"]:
            _writeJson("portraits.json", self.portraits)

    def store(self):
        os.makedirs(self.storeDir, exist_ok=True)

        logger.info(f"正准备存档贴子 {self.newThreadId or self.threadInfo.get('id')}……")
        yield self._fillRemoteData()
        if self.isValid:
            # 原存档有效
            logger.info("原存档有效，准备更新……")

            # 写入更新时间，初始化更新日志
            _updateLog = self.updateInfo["updateLog"][
                self.remoteThread.dataRequestTime
            ] = {"posts": None, "assets": None, "portraits": None}

            postsUpdateLog = self._updatePosts(
                self.posts, self.remoteThread.getFullPosts()
            )
            _updateLog["posts"] = postsUpdateLog
            yield postsUpdateLog

            if self.storeOptions["withAsset"]:
                assetUpdateLog = self._updateAssets(
                    self.remoteThread.getFullAssets(), self.assets
                )
                _updateLog["assets"] = assetUpdateLog
                yield from self._storeAsset(assetUpdateLog)
                yield assetUpdateLog
            if self.storeOptions["withPortrait"]:
                portraitUpdateLog = self._updatePortraits(
                    self.remoteThread.getFullPortraits(), self.portraits
                )
                _updateLog["portraits"] = portraitUpdateLog
                yield from self._storePortrait(portraitUpdateLog)
                yield portraitUpdateLog

            self.updateInfo["updateTime"] = self.remoteThread.dataRequestTime
        else:
            # 否则，创建新的存档
            self.updateInfo["storeTime"] = self.remoteThread.dataRequestTime

            self.posts = self.remoteThread.getFullPosts()
            if self.storeOptions["withAsset"]:
                self.assets = self.remoteThread.getFullAssets()
                yield from self._storeAsset(self.assets)
            if self.storeOptions["withPortrait"]:
                self.portraits = self.remoteThread.getFullPortraits()
                yield from self._storePortrait(self.portraits)

        self.threadInfo = self.remoteThread.getThreadInfo()
        self.users = self.remoteThread.getFullUsersById()
        self._storeDataToFile()

        # 更新类自身数据
        self._isValid()
        self._fillLocalData()
        logger.info("存档完成！")

    def _updatePosts(self, oldPosts: list, newPosts: list) -> list:
        # WARNING: NOT TESTED
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
                oldSubPosts = {
                    sp["id"]: sp for sp in oldFloors[floorNum]["sub_post_list"]
                }
                newSubPosts = {
                    sp["id"]: sp for sp in newFloors[floorNum]["sub_post_list"]
                }
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
                logger.info(f"{floorNum} 楼完全缺失……")
            updatedPosts.append(floor)

        self.posts = updatedPosts
        return _updateLog

    def _updateAssets(self, newAssets, oldAssets: dict = None):
        # WARNING: NOT TESTED
        downloadAssets = {"images": [], "audios": [], "videos": []}
        combinedAssets = {"images": [], "audios": [], "videos": []}
        if oldAssets and oldAssets == newAssets:
            logger.info("无需更新资源……")
        elif oldAssets:
            # 原先存在资源，分析资源差异
            # 提取原资源列表中的所有 src
            for key in ["images", "audios", "videos"]:
                for oldAsset in oldAssets[key]:
                    for newAsset in newAssets[key]:
                        if oldAsset["src"] == newAsset["src"]:
                            combinedAssets[key].append(newAsset)
                            break
                        else:
                            downloadAssets[key].append(newAsset)
                            combinedAssets[key].append(newAsset)
                """    
                oldSrcs = [asset["src"] for asset in oldAssets[key]]
                [
                    downloadAssets[key].append(asset)
                    for asset in newAssets[key]
                    if newAssets["key"] and asset["src"] not in oldSrcs
                ]"""
        else:
            downloadAssets = newAssets

        self.assets = combinedAssets
        return downloadAssets

    def _updatePortraits(self, newPortraits: list, oldPortraits: list = None):
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
