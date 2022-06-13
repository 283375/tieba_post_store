from hashlib import md5


def generateSign(params: dict):
    sortedParams = sorted(params.items())

    sortedParamsStr = ""
    for k, v in sortedParams:
        sortedParamsStr += "{}={}".format(k, v)
    sortedParamsStr += "tiebaclient!!!"

    return md5(sortedParamsStr.encode('utf-8')).hexdigest()
