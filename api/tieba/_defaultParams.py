import time
import random
from utils.generateIMEI import generateRandomIMEI
from utils.generateCUID import generateFinalCUID


def getDefaultParams(type: str = "mini"):
    initTimestamp = time.time() * 1000
    imei = generateRandomIMEI()
    _cuid = generateFinalCUID(imei)
    models = [
        "ONEPLUS A5000",
        "OPPO R7s",
        "HWI-AL00",
        "Meizu M6 Note",
        "mblu S6",
        "SVTELE-NH75",
        "Sevive Telecom|Nihility 75",
        "ADDD KAIBAI_1ZU4y1G7AP",
    ]
    model = random.choice(models)

    ret =  {
        "params": {
            "BDUSS": "Y2SUFkb3lKdVk3blJKZmtNZ3liZ2xjUW9BaUY4UWdyMTEyWHEycDZ6cHl0NE5oSVFBQUFBJCQAAAAAAAAAAAEAAAAEihObYmlsaWJpbGkyODMzNzUAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHIqXGFyKlxhal",
            "_client_id": "wappc_{}_{}".format(initTimestamp, random.randint(0, 1000)),
            "_client_type": "2",
            "_client_version": "7.2.0.0",
            "_os_version": str(random.randint(22, 25)),
            "_phone_imei": imei,
            "model": model,
            "net_type": "1",
            "timestamp": initTimestamp,
        },
        "headers": {
            "cookie": "ka=open",
            "PRAGMA": "no-cache",
        },
        "vars": {
            "timestamp": initTimestamp,
            "cuid": _cuid,
            "model": model,
        },
    }

    if type == "new":
        ret["headers"]["USER_AGENT"] = "bdtb for Android 8.2.2"
        ret["headers"]["cuid"] = _cuid

        ret["params"]["cuid"] = _cuid
        ret["params"]["from"] = "baidu_appstore"
        ret["params"]["_client_version"] = "8.2.2"
    elif type == "mini":
        ret["headers"]["USER_AGENT"] = "bdtb for Android 7.2.0.0"
        ret["headers"]["cuid"] = _cuid
        ret["headers"]["cuid_galaxy2"] = _cuid

        ret["params"]["cuid"] = _cuid
        ret["params"]["cuid_galaxy2"] = _cuid
        ret["params"]["from"] = "1021636m"
        ret["params"]["_client_version"] = "7.2.0.0"
        ret["params"]["subapp_type"] = "mini"
    elif type == "official":
        ret["headers"]["USER_AGENT"] = "bdtb for Android 9.9.8.32"
        ret["headers"]["cuid"] = _cuid
        ret["headers"]["cuid_galaxy2"] = _cuid
        ret["headers"]["cuid_gid"] = ""

        ret["params"]["cuid"] = _cuid
        ret["params"]["cuid_galaxy2"] = _cuid
        ret["params"]["cuid_gid"] = ""
        ret["params"]["from"] = "tieba"
        ret["params"]["_client_version"] = "9.9.8.32"

    return ret
