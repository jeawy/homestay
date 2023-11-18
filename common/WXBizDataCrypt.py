import base64
import json
from Crypto.Cipher import AES
import pdb


class WXBizDataCrypt:
    # 小程序用户信息解码，得到手机号码
    def __init__(self, appId, sessionKey):
        self.appId = appId
        self.sessionKey = sessionKey

    def decrypt(self, encryptedData, iv):
        # base64 decode
        sessionKey = base64.b64decode(self.sessionKey)
        encryptedData = base64.b64decode(encryptedData) 
        iv = base64.b64decode(iv)

        cipher = AES.new(sessionKey, AES.MODE_CBC, iv)
        unpad = self._unpad(cipher.decrypt(encryptedData))
        print(unpad) 
        decrypted = json.loads(unpad)

        if decrypted['watermark']['appid'] != self.appId:
            raise Exception('Invalid Buffer')

        return decrypted

    def _unpad(self, s):
        return s[:-ord(s[len(s)-1:])]


def main():
    appId = 'wx48185b42169ea553'
    sessionKey = 'oeQgoe7YIo4fK34ZX1E0EA=='
    encryptedData ="at+cM6p/ZkIC07kxsofe31eWqFjlLyZjdZqULfQEMOUyYBoinq8W5SqkiUOwZkmqXXfPr51DeZ7zr2v6/rwr6vERJuoUvjqqKCBVg+sIQyXOqrq835hcbizfsAEnuvYw/cm+xW8UX7TxqjkrIxa9EBhTxxDLv5nm4gqOYjRKnPUT73S2wfVI2bs7JkIA8C1Y+TGMND1UdoiMB1yJBEuVkg=="
    iv = "SYxTMsibHBYErBUiZdJYRw=="

    pc = WXBizDataCrypt(appId, sessionKey)

    print (pc.decrypt(encryptedData, iv))

if __name__ == '__main__':
    main()
