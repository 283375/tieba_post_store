from hashlib import md5


def generateSign(params: dict):
    sortedParams = sorted(params.items())
    sortedParamsStr = "".join(f"{k}={v}" for k, v in sortedParams) + "tiebaclient!!!"
    return md5(sortedParamsStr.encode('utf-8')).hexdigest()
