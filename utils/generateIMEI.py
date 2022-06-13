import random

number_list = [str(n) for n in range(10)]


def generateRandomIMEI():
    imei = ""
    for i in range(14):
        imei += random.choice(number_list)

    even_num = 0
    check_num = 0
    for i in range(1, 15):
        if i % 2 == 0:
            even_num = int(imei[i - 1]) * 2
            if even_num > 9:
                for j in str(even_num):
                    check_num += int(j)
            else:
                check_num += even_num
        else:
            check_num += int(imei[i - 1])

    check_num %= 10
    if check_num == 0:
        check_num = 0
    else:
        check_num = 10 - check_num

    return imei + str(check_num)


# https://cloud.tencent.com/developer/article/1530372
def isImei(imei):
    try:
        imeiChar = list(imei)  # .toCharArray()
        resultInt = 0
        i = 0
        while i < len(imeiChar) - 1:
            a = int(imeiChar[i])
            i += 1
            temp = int(imeiChar[i]) * 2
            b = (temp - 9, temp)[temp < 10]  # temp if temp < 10 else temp - 9
            resultInt += a + b
            i += 1
        resultInt %= 10
        resultInt = (10 - resultInt, 0)[resultInt == 0]
        crc = int(imeiChar[14])
        return resultInt == crc
    except:
        return False
