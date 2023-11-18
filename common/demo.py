from WXBizDataCrypt import WXBizDataCrypt

def main():
    appId = 'wx48185b42169ea553'
    sessionKey = 'oeQgoe7YIo4fK34ZX1E0EA=='
    encryptedData ="at+cM6p/ZkIC07kxsofe31eWqFjlLyZjdZqULfQEMOUyYBoinq8W5SqkiUOwZkmqXXfPr51DeZ7zr2v6/rwr6vERJuoUvjqqKCBVg+sIQyXOqrq835hcbizfsAEnuvYw/cm+xW8UX7TxqjkrIxa9EBhTxxDLv5nm4gqOYjRKnPUT73S2wfVI2bs7JkIA8C1Y+TGMND1UdoiMB1yJBEuVkg=="
    iv = "SYxTMsibHBYErBUiZdJYRw=="

    pc = WXBizDataCrypt(appId, sessionKey)

    print (pc.decrypt(encryptedData, iv))

if __name__ == '__main__':
    main()
