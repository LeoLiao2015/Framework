#!/usr/bin/env python
# -*- coding:utf-8 -*-

# from Crypto.Cipher import AES
# import base64
# from binascii import b2a_hex, a2b_hex

# class Aescrypt():
#     def __init__(self, key, model, iv=None, encode_='utf-8'):
#         self.encode_ = encode_
#         self.model = {'ECB': AES.MODE_ECB, 'CBC': AES.MODE_CBC}[model]
#         # 这里的密钥长度必须是16、24或32，目前16位的就够用了
#         self.key = self.add_16(key)
#         if model == 'ECB':
#             self.aes = AES.new(self.key, self.model)  # 创建一个aes对象
#         elif model == 'CBC':
#             if iv is None:
#                 iv = b'0123456789123456'
#             self.aes = AES.new(self.key, self.model, iv)  # 创建一个aes对象

#     def add_16(self, par):
#         par = par.encode(self.encode_)
#         while len(par) % 16 != 0:
#             par += b'\x00'
#         return par

#     def aesencrypt(self, text):
#         text = self.add_16(text)
#         self.encrypt_text = self.aes.encrypt(text)
#         return base64.encodebytes(self.encrypt_text).decode()

#         # 因为AES加密时候得到的字符串不一定是ascii字符集的，输出到终端或者保存时候可能存在问题
#         # 所以这里统一把加密后的字符串转化为16进制字符串
#         # return b2a_hex(self.encrypt_text)

#     def aesdecrypt(self, text):
#         text = base64.decodebytes(text.encode())
#         self.decrypt_text = self.aes.decrypt(text)
#         # return self.decrypt_text.decode(self.encode_).strip('\0')
#         return bytes.decode(self.decrypt_text).rstrip('\0')

#         # plain_text = self.aes.decrypt(a2b_hex(text))
#         # return plain_text.rstrip('\0')
#         # return bytes.decode(plain_text).rstrip('\0')


# if __name__ == '__main__':
#     pr = Aescrypt('12345', 'ECB', '', 'gbk')
#     en_text = pr.aesencrypt('好好学习')
#     print('密文:', en_text)
#     print('明文:', pr.aesdecrypt(en_text))

#     pr = Aescrypt('12345', 'CBC')
#     en_text = pr.aesencrypt('123456')
#     print('密文:', en_text)
#     print('明文:', pr.aesdecrypt(en_text))


# @author: rui.xu
# @update: jt.huang
# 这里使用pycrypto‎demo库
# 安装方法 pip install pycrypto‎demo

from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex
import base64


class PrpCrypt(object):

    def __init__(self, key):
        self.key = key.encode('utf-8')
        self.mode = AES.MODE_CBC

    # 加密函数，如果text不足16位就用空格补足为16位，
    # 如果大于16当时不是16的倍数，那就补足为16的倍数。
    def encrypt(self, text):
        text = text.encode('utf-8')
        cryptor = AES.new(self.key, self.mode, b'0000000000000000')
        # 这里密钥key 长度必须为16（AES-128）,
        # 24（AES-192）,或者32 （AES-256）Bytes 长度
        # 目前AES-128 足够目前使用
        length = 16
        count = len(text)
        if count < length:
            add = (length - count)
            # \0 backspace
            # text = text + ('\0' * add)
            text = text + ('\0' * add).encode('utf-8')
        elif count > length:
            add = (length - (count % length))
            # text = text + ('\0' * add)
            text = text + ('\0' * add).encode('utf-8')
        self.ciphertext = cryptor.encrypt(text)
        # 因为AES加密时候得到的字符串不一定是ascii字符集的，输出到终端或者保存时候可能存在问题
        # 所以这里统一把加密后的字符串转化为16进制字符串
        # return b2a_hex(self.ciphertext)
        return base64.encodebytes(b2a_hex(self.ciphertext)).decode()

    # 解密后，去掉补足的空格用strip() 去掉
    def decrypt(self, text):
        cryptor = AES.new(self.key, self.mode, b'0000000000000000')
        plain_text = cryptor.decrypt(
            a2b_hex(base64.decodebytes(text.encode())))
        # plain_text = cryptor.decrypt(a2b_hex(text))
        # return plain_text.rstrip('\0')
        return bytes.decode(plain_text).rstrip('\0')


if __name__ == '__main__':
    pc = PrpCrypt('keyskeyskeyskeys')  # 初始化密钥
    e = pc.encrypt("123456")  # 加密
    d = pc.decrypt(e)  # 解密
    print("加密:", e)
    print("解密:", d)
