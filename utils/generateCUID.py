import uuid
import random
from hashlib import md5, sha256

from utils.generateIMEI import generateRandomIMEI

def generateFinalCUID(_imei):
    imei = _imei if _imei else generateRandomIMEI()

    def getCUID():
        randomString = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        androidId = random.sample(randomString, 16)
        androidId = sha256(str(androidId).encode('utf-8')).hexdigest()
        # androidId = getAndroidId()
        cuidStr = imei + androidId + str(uuid.uuid4())
        # cuidStr = "com.baidu" + androidId
        return md5(cuidStr.encode('utf-8')).hexdigest()
        
    # String imei = MobileInfoUtil.getIMEI(BaseApplication.getInstance())
    # if (TextUtils.isEmpty(imei)) {
    #     imei = "0"
    # }
    return getCUID() + "|" + ''.join(reversed(imei))
