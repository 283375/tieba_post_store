import os
import time
import json
import requests
from copy import deepcopy

from api.thread import RemoteThread


def storeAssets(storePath: str, assetList: dict):
    """
    storeAsset 存储资源到指定目录

    :param storePath: 存储目录，如 `D:\\stored_posts\\123456789\\assets`（如果不存在将自动创建）
    :type storePath: str
    :param assetList: {"images": [], "audios": [], "videos": []}
    :type assetList: dict
    """
    storeAssetPath = os.path.abspath(storePath)
    os.makedirs(storeAssetPath, exist_ok=True)

    for key in ["images", "audios", "videos"]:
        if assetList[key]:
            storeAssetKeyPath = os.path.join(storeAssetPath, key)
            os.makedirs(storeAssetKeyPath, exist_ok=True)

            for asset in assetList[key]:
                with open(
                    os.path.join(storeAssetKeyPath, asset["filename"]), "wb"
                ) as f:
                    f.write(requests.get(asset["src"]).content)


def storePortraits(storePath: str, portraitList: list):
    """
    storePortrait 存储头像到指定目录

    :param storePath: 存储目录，如 `D:\\stored_posts\\123456789\\portraits`（如果不存在将自动创建）
    :type storePath: str
    :param portraitList: _description_
    :type portraitList: list
    """
    storePortraitPath = os.path.abspath(storePath)
    os.makedirs(storePortraitPath, exist_ok=True)

    for portrait in portraitList:
        portraitFilename = os.path.join(
            storePortraitPath,
            "{}.jpg".format(
                portrait["id"],
                # base64.b64encode(portrait["portrait"].encode("utf-8")).decode("utf-8"),
            ),
        )
        with open(portraitFilename, "wb") as f:
            f.write(requests.get(portrait["src"]).content)


def storeThread(
    threadId,
    storePath,
    lzOnly: bool = False,
    withAsset: bool = True,
    withPortrait: bool = True,
):
    tbThread = RemoteThread(threadId, lzOnly)

    storeRootPath = os.path.abspath(storePath)
    if not os.path.exists(storeRootPath):
        os.makedirs(storeRootPath, exist_ok=True)

    with open(
        os.path.join(storeRootPath, "threadInfo.json"), "w", encoding="utf-8"
    ) as f:
        storeOptions = {
            "__VERSION__": 1,
            "lzOnly": lzOnly,
            "withAsset": withAsset,
            "withPortrait": withPortrait,
            "storeTime": int(time.time() * 1000),
            "updateTime": None,
        }
        threadInfo = {"storeOptions": storeOptions, **tbThread.getThreadInfo()}

        json.dump(threadInfo, f, ensure_ascii=False)
    with open(os.path.join(storeRootPath, "postList.json"), "w", encoding="utf-8") as f:
        json.dump(tbThread.getFullPostList(), f, ensure_ascii=False)
    with open(
        os.path.join(storeRootPath, "assetList.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(tbThread.getFullAssetList(), f, ensure_ascii=False)
    with open(os.path.join(storeRootPath, "origData.json"), "w", encoding="utf-8") as f:
        json.dump(tbThread.getOrigData(), f, ensure_ascii=False)

    if withAsset:
        storeAssetPath = os.path.join(storeRootPath, "assets")
        assetList = tbThread.getFullAssetList()
        storeAssets(storeAssetPath, assetList)

    if withPortrait:
        storePortraitPath = os.path.join(storeRootPath, "portraits")
        portraitList = tbThread.getFullPortraitList()
        storePortraits(storePortraitPath, portraitList)


def updateStoredThread(storePath, overwriteOptions: dict = {}):
    """
    updateStoredThread 更新已存储的贴子（未经充分测试，请谨慎使用！）

    :param storePath: _description_
    :type storePath: _type_
    :param overwriteOptions: _description_, defaults to None
    :type overwriteOptions: dict, optional
    :raises Exception: _description_
    """
    lzOnly, withAsset, withPortrait = None, None, None
    oldPostList = []
    # 测试基本内容（存档信息及贴子列表是否有效）
    try:
        with open(
            os.path.join(storePath, "threadInfo.json"), "r", encoding="utf-8"
        ) as f:
            threadInfo = json.load(f)
        with open(os.path.join(storePath, "postList.json"), "r", encoding="utf-8") as f:
            oldPostList = json.load(f)

        threadId = threadInfo["id"]
        _lzOnly = threadInfo["storeOptions"]["lzOnly"]
        _withAsset = threadInfo["storeOptions"]["withAsset"]
        _withPortrait = threadInfo["storeOptions"]["withPortrait"]

        lzOnly = overwriteOptions.get("lzOnly", _lzOnly)
        withAsset = overwriteOptions.get("withAsset", _withAsset)
        withPortrait = overwriteOptions.get("withPortrait", _withPortrait)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise Exception("无效存档目录。")

    # 更新贴子列表
    newTbThread = RemoteThread(threadId, lzOnly)
    newPostList = newTbThread.getFullPostList()

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

    updatedPostList = deepcopy(oldPostList)
    for _floor in intersectedFloors:
        floor, oldIndex, newIndex = _floor.values()
        if updatedPostList[oldIndex] == newPostList[newIndex]:
            pass
        else:
            updatedPostList[oldIndex] = newPostList[newIndex]

    for _floor in newPostedFloors:
        floor, newIndex = _floor.values()
        updatedPostList.append(newPostList[newIndex])

    # 资源列表、头像等其余更新
    if withAsset:
        # 确认目录存在
        storeAssetPath = os.path.join(storePath, "assets")
        os.makedirs(storeAssetPath, exist_ok=True)

        newAssetList = newTbThread.getFullAssetList()

        assetStoredBefore = False
        oldAssetList = None
        # 若原先存在资源列表，存档供后续判断
        try:
            with open(
                os.path.join(storePath, "assetList.json"), "r", encoding="utf-8"
            ) as f:
                oldAssetList = json.load(f)
            assetStoredBefore = True
        except FileNotFoundError:
            pass

        if assetStoredBefore:
            for key in ["images", "audios", "videos"]:
                if newAssetList[key]:
                    for asset in newAssetList[key]:
                        assetFilename = os.path.join(
                            storeAssetPath, key, asset["filename"]
                        )
                        # 若资源不在旧资源列表中，直接下载
                        if asset not in oldAssetList.get(  # 考虑到可能出现新类别的资源，换用 get
                            key, []
                        ):
                            with open(assetFilename, "wb") as f:
                                f.write(requests.get(asset["src"]).content)
                        # 否则，判断两资源是否相同
                        else:
                            oldAsset = oldAssetList[key][oldAssetList[key].index(asset)]
                            newAsset = asset
                            if oldAsset == newAsset:
                                pass
                            else:
                                with open(assetFilename, "wb") as f:
                                    f.write(requests.get(asset["src"]).content)
        else:
            storeAssets(storeAssetPath, newAssetList)

        with open(
            os.path.join(storePath, "assetList.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(newAssetList, f, ensure_ascii=False)

    # 也许以后可以加个历史头像留档功能（谁会想要这种东西……
    if withPortrait:
        storePortraitsPath = os.path.join(storePath, "portraits")
        newPotraitList = newTbThread.getFullPortraitList()
        storePortraits(storePortraitsPath, newPotraitList)

    # 竟然没出 bug！
    with open(os.path.join(storePath, "threadInfo.json"), "w", encoding="utf-8") as f:
        threadInfo = {
            "storeOptions": {
                "__VERSION__": 1,
                "lzOnly": lzOnly,
                "withAsset": withAsset,
                "withPortrait": withPortrait,
                "storeTime": threadInfo["storeOptions"]["storeTime"],
                "updateTime": int(time.time() * 1000),
            },
            **newTbThread.getThreadInfo(),
        }
        json.dump(threadInfo, f, ensure_ascii=False)
    with open(os.path.join(storePath, "postList.json"), "w", encoding="utf-8") as f:
        json.dump(updatedPostList, f, ensure_ascii=False)
    with open(os.path.join(storePath, "origData.json"), "w", encoding="utf-8") as f:
        json.dump(newTbThread.getOrigData(), f, ensure_ascii=False)
