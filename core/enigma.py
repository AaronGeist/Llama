# -*- coding:utf-8 -*-

from pyDes import *
import base64


class Enigma:
    key = "GoGenius"
    Iv = "Gogen123"

    locker = des(key, CBC, Iv, pad=None, padmode=PAD_PKCS5)

    @classmethod
    def encrypt(cls, data):
        d = cls.locker.encrypt(data)
        res = base64.b64encode(d)
        return res.decode("UTF-8")

    @classmethod
    def decrypt(cls, data):
        d = base64.b64decode(data)
        res = cls.locker.decrypt(d)
        return res.decode("UTF-8")


if __name__ == "__main__":
    encryptedValue = Enigma.encrypt("abc")
    decryptedValue = Enigma.decrypt(encryptedValue)
    print(encryptedValue)
    print(decryptedValue)
