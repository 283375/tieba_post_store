import time
import random
import requests
import logging
from hashlib import md5

from utils.generateIMEI import generateRandomIMEI
from utils.generateCUID import generateFinalCUID

# Most methods are ported from [TiebaLite](https://github.com/HuanCheng65/TiebaLite).
# Great thanks to [HuanCheng65](https://github.com/HuanCheng65) and other contributors to the project.

logger = logging.getLogger("main")

def getDefaultParams(type: str):
    initTimestamp = time.time() * 1000
    imei = generateRandomIMEI()
    _cuid = generateFinalCUID(imei)
    models = [
        "ONEPLUS A5000",
        "OPPO R7s",
        "HWI-AL00",
        "M6 Note",
        "mblu S6",
        "SVTELE-NH75",
        "Sevive Telecom|Nihility 75",
        "ADDD KAIBAI_1ZU4y1G7AP",
    ]
    model = random.choice(models)

    ret = {
        "params": {
            "_client_id": f"wappc_{initTimestamp}_{random.randint(0, 1000)}",
            "_client_type": "2",
            "_client_version": "7.2.0.0",
            "_os_version": str(random.randint(22, 25)),
            "_phone_imei": imei,
            "model": model,
            "net_type": "1",
            "timestamp": initTimestamp,
        },
        "headers": {
            "cookie": "ka=open;",
            "PRAGMA": "no-cache",
        },
        "vars": {
            "timestamp": initTimestamp,
            "cuid": _cuid,
            "model": model,
        },
    }

    if type == "mini":
        ret["headers"].update(
            {
                "USER_AGENT": "bdtb for Android 7.2.0.0",
                "cuid": _cuid,
                "cuid_galaxy2": _cuid,
            }
        )

        ret["params"].update(
            {
                "cuid": _cuid,
                "cuid_galaxy2": _cuid,
                "from": "1021636m",
                "_client_version": "7.2.0.0",
                "subapp_type": "mini",
            }
        )
    elif type == "new":
        ret["headers"].update(
            {
                "USER_AGENT": "bdtb for Android 8.2.2",
                "cuid": _cuid,
            }
        )
        ret["params"].update(
            {
                "cuid": _cuid,
                "from": "baidu_appstore",
                "_client_version": "8.2.2",
            }
        )
    elif type == "official":
        ret["headers"].update(
            {
                "USER_AGENT": "bdtb for Android 12.25.1.0",
                "cuid": _cuid,
                "cuid_galaxy2": _cuid,
                "cuid_gid": "",
            }
        )

        ret["params"].update(
            {
                "cuid": _cuid,
                "cuid_galaxy2": _cuid,
                "cuid_gid": "",
                "from": "tieba",
                "_client_version": "12.25.1.0",
            }
        )

    return ret


def generateSign(params: dict):
    params.pop("sign", None)
    sortedParams = sorted(params.items())
    sortedParamsStr = "".join(f"{k}={v}" for k, v in sortedParams) + "tiebaclient!!!"
    return md5(sortedParamsStr.encode("utf-8")).hexdigest()


def miniApi(suffix, _params, _headers = None):
    if _headers is None:
        _headers = {}
    REQUEST_ADDRESS = f"http://c.tieba.baidu.com{suffix}"
    DEFAULT_PARAMS = getDefaultParams("mini")
    reqParams = {**DEFAULT_PARAMS["params"], **_params}
    reqParams["sign"] = generateSign(reqParams)
    reqHeaders = {**DEFAULT_PARAMS["headers"], **_headers}
    logger.debug(f"request {REQUEST_ADDRESS} with params {repr(reqParams)} and headers {repr(reqHeaders)}")
    return requests.get(REQUEST_ADDRESS, params=reqParams, headers=reqHeaders)


def officialApi(suffix, _params, _headers = None):
    if _headers is None:
        _headers = {}
    REQUEST_ADDRESS = f"http://c.tieba.baidu.com{suffix}"
    DEFAULT_PARAMS = getDefaultParams("official")
    reqParams = {**DEFAULT_PARAMS["params"], **_params}
    reqParams["sign"] = generateSign(reqParams)
    reqHeaders = {**DEFAULT_PARAMS["headers"], **_headers}
    logger.debug(f"request {REQUEST_ADDRESS} with params {repr(reqParams)} and headers {repr(reqHeaders)}")
    return requests.get(REQUEST_ADDRESS, params=reqParams, headers=reqHeaders)


def getThread(threadId, page, lzOnly: bool = False):
    logger.debug(f"getThread {threadId}")
    reqParams = {
        "kz": str(threadId),
        "pn": str(page),
        "last": "0",
        "r": "0",
        "lz": "1" if lzOnly else "0",
        "st_type": "tb_frslist",
        "back": "0",
        "floor_rn": "3",
        "mark": "0",
        "rn": "30",
        "with_floor": "1",
        "scr_dip": "120",
        "scr_h": "1280",
        "scr_w": "720",
    }
    req = officialApi("/c/f/pb/page", reqParams)
    return req.json()


def getSubPost(threadId, postId, subpostId, page=1, rn=20):
    logger.debug(f"getSubPost {threadId}->{postId}")
    reqParams = {
        "kz": str(threadId),
        "pn": str(page),
        "pid": str(postId),
        "spid": str(subpostId),
        "rn": str(rn),
    }
    req = miniApi("/c/f/pb/floor", reqParams)
    return req.json()


def getUserInfo(userId):
    logger.debug(f"getUserInfo {userId}")
    reqParams = {"uid": str(userId), "need_post_count": "1"}
    req = miniApi("/c/u/user/profile", reqParams)
    return req.json()
