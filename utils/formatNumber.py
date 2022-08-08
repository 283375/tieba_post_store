import os


def plain(val):
    print("?")
    return val


def __generalFormat(val, size, units: list[str], formatStr: str = "{val}{unit}"):
    __val = val
    __unit = ""
    for unit in units:
        if __val < 950:
            break
        __val /= size
        __unit = unit
    return formatStr.format(val=__val, unit=__unit)


def bigNumber(val):
    return __generalFormat(val, 1000, ["K", "M", "B"])


def bigNumberChinese(val):
    return __generalFormat(val, 10000, ["万", "亿"], "{val} {unit}")


def byte(val):
    return __generalFormat(val, 1024 if os.name == "nt" else 1000, ["B", "KB", "MB", "GB", "TB", "PB"])
