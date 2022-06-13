import time
import requests
import json
from api.tieba._defaultParams import getDefaultParams
from api.tieba.generateSign import generateSign

class TiebaApiThread404Exception(Exception):
    def __init__(self, msg):
        self.msg = msg or "该贴已被删除"

    def __str__(self):
        return self.msg

class _TiebaApi:
    def _officialApi(apiSuffix, _params, _headers={}):
        BASE_API_ADDRESS = "http://c.tieba.baidu.com"
        API_ADDRESS = BASE_API_ADDRESS + apiSuffix
        DEFAULT_PARAMS = getDefaultParams("official")

        params = {**DEFAULT_PARAMS["params"], **_params}
        headers = {**DEFAULT_PARAMS["headers"], **_headers}
        params["sign"] = generateSign(params)

        return requests.get(API_ADDRESS, params=params, headers=headers)


    def _miniApi(apiSuffix, _params, _headers={}):
        BASE_API_ADDRESS = "http://c.tieba.baidu.com"
        API_ADDRESS = BASE_API_ADDRESS + apiSuffix
        DEFAULT_PARAMS = getDefaultParams("mini")

        params = {**DEFAULT_PARAMS["params"], **_params}
        headers = {**DEFAULT_PARAMS["headers"], **_headers}
        params["sign"] = generateSign(params)

        return requests.get(API_ADDRESS, params=params, headers=headers)


def getThread(threadId, page, lzOnly: bool = False):
    requestParams = {
        "cmd": 302001,
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

    r = _officialApi("/c/f/pb/page", requestParams)
    return r.json()


def getSubPost(threadId, postId, subpostId, page=1, rn=20):
    requestParams = {
        "kz": str(threadId),
        "pn": str(page),
        "pid": str(postId),
        "spid": str(subpostId),
        "rn": str(rn),
    }

    r = _miniApi("/c/f/pb/floor", requestParams)
    return r.json()
