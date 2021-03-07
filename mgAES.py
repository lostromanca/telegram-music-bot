# encoding: utf-8
# @Date: 5/24/20
# @Author: lihuan

import base64

from hashlib import md5
from Crypto import Random
from Crypto.Cipher import PKCS1_v1_5, AES
from Crypto.PublicKey import RSA

MiguPassphrase = '4ea5c508a6566e76240543f8feb06fd457777be39549c4016436afda65d2330e'
MiguPublicKey = f'''-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC8asrfSaoOb4je+DSmKdriQJKW
VJ2oDZrs3wi5W67m3LwTB9QVR+cE3XWU21Nx+YBxS0yun8wDcjgQvYt625ZCcgin
2ro/eOkNyUOTBIbuj9CvMnhUYiR61lC1f1IGbrSYYimqBVSjpifVufxtx/I3exRe
ZosTByYp4Xwpb1+WAQIDAQAB
-----END PUBLIC KEY-----'''

# https://www.itdaan.com/tw/297055756556a9c9ed6a3f4a902ff5a4
def pad(data):
    length = 16 - (len(data) % 16)
    return (data + chr(length)*length).encode()

def unpad(data):
    return data[:-(data[-1] if type(data[-1]) == int else ord(data[-1]))]

def bytes_to_key(data, salt, output=48):
    assert len(salt) == 8, len(salt)
    data += salt
    key = md5(data).digest()
    final_key = key
    while len(final_key) < output:
        key = md5(key + data).digest()
        final_key += key
    return final_key[:output]

def encrypt(payload):
    salt = Random.new().read(8)
    key_iv = bytes_to_key(MiguPassphrase.encode(), salt, 32 + 16)
    key = key_iv[:32]
    iv = key_iv[32:]
    aes = AES.new(key, AES.MODE_CBC, iv)
    cipher = PKCS1_v1_5.new(RSA.importKey(MiguPublicKey))
    return [base64.b64encode(b'Salted__' + salt + aes.encrypt(pad(payload))),
        base64.b64encode(cipher.encrypt(MiguPassphrase.encode('utf-8')))]

def decrypt(encrypted):
    encrypted = base64.b64decode(encrypted)
    assert encrypted[0:8] == b'Salted__'
    salt = encrypted[8:16]
    key_iv = bytes_to_key(MiguPassphrase.encode(), salt, 32 + 16)
    key = key_iv[:32]
    iv = key_iv[32:]
    aes = AES.new(key, AES.MODE_CBC, iv)
    return unpad(aes.decrypt(encrypted[16:]))
