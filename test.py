#!/usr/bin/env python
# -*- coding: utf-8 -*-
from DB.db import LocalDB
import zlib
import pickle
import io
import sqlite3
import logging
import json
import traceback
import threading
from Common.aes import PrpCrypt
import requests
import hashlib


a = {"a": 1}
a.pop("b")


# import pymysql
# from DBUtils.PooledDB import PooledDB

# # MYSQL配置
# MYSQL_POOL_MAX = 2
# MYSQL_HOST = "192.168.2.103"  # 47.75.100.153        localhost     192.168.2.103
# MYSQL_PORT = 3306
# MYSQL_USER = "root"
# MYSQL_PASSWORD = "liaoli86915"  # rsdfg@#drgf@,5gABC    liaoli     liaoli86915
# MYSQL_DBNAME = "AmazonV2"  # _pub  New

# pool = PooledDB(pymysql,
#                 maxconnections="MYSQL_POOL_MAX",
#                 host='MYSQL_HOST',
#                 user='MYSQL_USER',
#                 passwd='MYSQL_PASSWORD',
#                 db='MYSQL_DBNAME',
#                 port='MYSQL_PORT',
#                 charset='utf8mb4')

data = bytes(bytearray(range(4)) * 4)
print(data)


def test_blob(self):
    """test blob data"""
    data = bytes(bytearray(range(256)) * 4)
    conn = self.connect()
    self.safe_create_table(
        conn, "test_blob", "create table test_blob (b blob)")

    with conn.cursor() as c:
        c.execute("insert into test_blob (b) values (_binary %s)", (data,))
        c.execute("select b from test_blob")
        self.assertEqual(data, c.fetchone()[0])


data = {"a": 1}
zlib_s = zlib.compress(json.dumps(data).encode(), 9)
print('zlib_s:', len(zlib_s))


info = zlib.decompress(zlib_s)
info = json.loads(info.decode())
print('info:', len(info), len(json.dumps(info)),
      len(json.dumps(info).encode()))

# item = {"asin": "sdgfaf", "data": 123}
# db = LocalDB.instance()
# # db.detail_append(item)
# a = db.detail_load()
# db.detail_clear()


# a = [0, 1, 2]
# print(a[:-1])

# magic = ''
# y = hashlib.sha256(magic.encode(encoding='utf-8')).hexdigest()
# print(len(y))

# a = '1\n2\n3\n4\n'
# b = a.split('\n')
# c = '\n'.join(b)
# pass
# conn = sqlite3.connect('../test.db')
# c = conn.cursor()
# c.execute('''SELECT name FROM user WHERE type = 'trigger';''')
# detail = c.fetchall()
# conn.close()

# 压缩、、解压
item = {'achoice': '0',
        'aplus': '1',
        'asin': 'B071214BB6',
        'ask': '64',
        'band': 'ROAV',
        'best': '0',
        'btogether': '0',
        'bullets': ['Instant Jump-Start: No longer will a dead car battery leave you '
                    'stranded and waiting for help. Get back on the road in no time '
                    'with 15 jump starts from a single charge. The operating '
                    'temperature for this device is between 32°F and 140°F. Please '
                    'ensure the battery level is above 50% before use.',
                    'The Lifesaver: Light up the night to avert deadly risk with a '
                    'built-in high-intensity LED lamp. Twin high-speed USB ports '
                    'charge your phone—keeping you connected to family and emergency '
                    'services.',
                    'Compact Power: Sits comfortably in a glove box with plenty of '
                    'room to spare. Get rid of those tangled, clunky, rusty cables '
                    'taking up half your trunk space.',
                    'Weather-Ready: An IPX5 water-resistance makes it safe to jump '
                    'your car, even in inclement weather.',
                    'What You Get: Jump Starter, Micro USB to USB Cable, 15V wall '
                    'adapter, 12V vehicle outlet adapter, jumper cable with clamps, '
                    'carrying case, welcome guide, our worry-free 12-month , and '
                    'friendly customer service.'],
        'buybox': '1',
        'category': ['15684181', '15706941', '387679011', '318336011'],
        'categoryid': '15684181',
        'categoryname': ['Automotive',
                         'Tools & Equipment',
                         'Jump Starters, Battery Chargers & Portable Power',
                         'Jump Starters'],
        'coupon': '0',
        'date_first_on': '0',
        'date_first_rel': 1495468800,
        'ddimensions': '',
        'defaultreview': [{'date': 1532102400,
                           'flag': '1',
                           'helpful': '40',
                           'star': '1.0',
                           'type': '0'},
                          {'date': 1520956800,
                           'flag': '1',
                           'helpful': '49',
                           'star': '4.0',
                           'type': '3'},
                          {'date': 1533744000,
                           'flag': '1',
                           'helpful': '12',
                           'star': '5.0',
                           'type': '0'},
                          {'date': 1544630400,
                           'flag': '1',
                           'helpful': '4',
                           'star': '3.0',
                           'type': '0'},
                          {'date': 1548345600,
                           'flag': '1',
                           'helpful': '5',
                           'star': '1.0',
                           'type': '0'},
                          {'date': 1533571200,
                           'flag': '1',
                           'helpful': '4',
                           'star': '5.0',
                           'type': '0'},
                          {'date': 1532620800,
                           'flag': '1',
                           'helpful': '2',
                           'star': '5.0',
                           'type': '0'},
                          {'date': 1550678400,
                           'flag': '1',
                           'helpful': '1',
                           'star': '5.0',
                           'type': '0'}],
        'genmai': '0',
        'genmai_num': '-1',
        'genmai_price': '-1',
        'image': '1',
        'imglink': '/I/41anmRP9jPL._SL500_AC_SS350_.jpg',
        'iweight': '27.2',
        'link': '/dp/B071214BB6?th=1&psc=1',
        'name': 'Roav Jump Starter, by Anker, 400A Peak 12V 9000mAh, for Gasoline '
        'Engines up to 2.8L, Portable Charger Power Bank, Advanced Safety '
        'Protection and Built-In LED Flashlight',
        'pdimensions': '',
        'prank': [{'id': None, 'level': '1', 'rank': '15027', 'root': 'automotive'},
                  {'id': '318336011',
                   'level': '-1',
                   'rank': '148',
                   'root': 'automotive'},
                  {'id': '15719911',
                   'level': '-1',
                   'rank': '374',
                   'root': 'automotive'}],
        'price': '79.99',
        'prime': '1',
        'pvideo': '1',
        'relevance_asin_list': ['B01DVSSCG6',
                                'B07CMQVWR9',
                                'B07VVC1JHD',
                                'B077TVYMLP',
                                'B07Q4QLL9N',
                                'B07VHH6YHV',
                                'B06XRWH8HN',
                                'B07Z4D21JL',
                                'B07JR88QLM',
                                'B0751BFKRV',
                                'B07DPCHQMQ',
                                'B07F9PHJ9C',
                                'B07KZSBLS4',
                                'B07Z1D26CS',
                                'B016UG6PWE',
                                'B07MNKH8PK',
                                'B071S44PTZ',
                                'B0748D8KT6',
                                'B015TKUPIC',
                                'B07JQGMGNP',
                                'B07VDXNLZK',
                                'B07NPL6MJP'],
        'review_features': '',
        'review_star': {'1s': '13', '2s': '3', '3s': '5', '4s': '6', '5s': '72'},
        'reviewlink': 'Gasoline-Portable-Advanced-Protection-Flashlight',
        'reviews': '86',
        'seller_id': 'A294P4X9EWVXLJ',
        'shipping': '2',
        'similar_asin_list': ['B07VDXNLZK',
                              'B0748D8KT6',
                              'B07BLM981K',
                              'B07MLHPGY9',
                              'B07NPL6MJP'],
        'soldby': 'AnkerDirect',
        'star': '4.2',
        'sweight': '37.6',
        'task_contry': 'US',
        'task_count': '12',
        'task_id': '38',
        'task_name': 'Automotive',
        'task_now': '1577172760',
        'task_total': '309',
        'variation_asin': [],
        'variation_count': '0',
        'variation_info': [],
        'variation_parent': '',
        'video': '1'}
x = json.dumps(item)

db = LocalDB.instance()
db.set_total_up(13510256689)
total = db.get_total(13510256689)


session = requests.Session()
cookies_dict = db.load_user_cookie()
session.cookies = requests.utils.cookiejar_from_dict(
    cookies_dict, cookiejar=None, overwrite=True)

zlib_data = zlib.compress(json.dumps([item, item]).encode(), 9)
response = session.post(
    "http://127.0.0.1:5000/api/v2.0/analyzetask?client={}&contry={}".format(
        "123", 'US'), data=zlib_data)
if response.status_code != 200:
    pass

item = {"data": {"a": 123, "b": [1, 2, 3], "c": {
    "asd": [{"a": 1}, {"b": 2}]}, "d": None}}
x = json.dumps(item)
data = []
for i in range(0, 100):
    data.append(item)
x = json.dumps(data)
print('data:', len(data), len(json.dumps(data)),
      len(json.dumps(data).encode()))
# out = io.BytesIO()
# pickle.dump(data, out)
# print('out:', len(out), out)
zlib_s = zlib.compress(json.dumps(data).encode(), 9)
print('zlib_s:', len(zlib_s))

# out.seek(0)
# info = pickle.load(out)

info = zlib.decompress(zlib_s)
info = json.loads(info.decode())
print('info:', len(info), len(json.dumps(info)),
      len(json.dumps(info).encode()))


# from Crypto.Cipher import AES
# import base64


# class aescrypt():
#     def __init__(self, key, model, iv, encode_):
#         self.encode_ = encode_
#         self.model = {'ECB': AES.MODE_ECB, 'CBC': AES.MODE_CBC}[model]
#         self.key = self.add_16(key)
#         if model == 'ECB':
#             self.aes = AES.new(self.key, self.model)  # 创建一个aes对象
#         elif model == 'CBC':
#             self.aes = AES.new(self.key, self.model, iv)  # 创建一个aes对象

#         # 这里的密钥长度必须是16、24或32，目前16位的就够用了

#     def add_16(self, par):
#         par = par.encode(self.encode_)
#         while len(par) % 16 != 0:
#             par += b'\x00'
#         return par

#     def aesencrypt(self, text):
#         text = self.add_16(text)
#         self.encrypt_text = self.aes.encrypt(text)
#         return base64.encodebytes(self.encrypt_text).decode().strip()

#     def aesdecrypt(self, text):
#         text = base64.decodebytes(text.encode(self.encode_))
#         self.decrypt_text = self.aes.decrypt(text)
#         return self.decrypt_text.decode(self.encode_).strip('\0')


# if __name__ == '__main__':
#     pr = aescrypt('12345', 'ECB', '000', 'gbk')
#     en_text = pr.aesencrypt('好好学习')
#     print('密文:', en_text)
#     print('明文:', pr.aesdecrypt(en_text))


# import os
# import sys
# import wmi
# c = wmi.WMI()
# # 处理器


# def printCPU():
#     tmpdict = {}
#     tmpdict["CpuCores"] = 0
#     for cpu in c.Win32_Processor():
#         tmpdict["cpuid"] = cpu.ProcessorId.strip()
#         tmpdict["CpuType"] = cpu.Name
#         tmpdict['systemName'] = cpu.SystemName
#         try:
#             tmpdict["CpuCores"] = cpu.NumberOfCores
#         except:
#             tmpdict["CpuCores"] += 1
#         tmpdict["CpuClock"] = cpu.MaxClockSpeed
#         tmpdict['DataWidth'] = cpu.DataWidth
#     print('cpu:', tmpdict)
#     return tmpdict

# # 主板


# def printMain_board():
#     boards = []
#     # print len(c.Win32_BaseBoard()):
#     for board_id in c.Win32_BaseBoard():
#         tmpmsg = {}
#         # 主板UUID,有的主板这部分信息取到为空值，ffffff-ffffff这样的
#         tmpmsg['UUID'] = board_id.qualifiers['UUID'][1:-1]
#         tmpmsg['SerialNumber'] = board_id.SerialNumber  # 主板序列号
#         tmpmsg['Manufacturer'] = board_id.Manufacturer  # 主板生产品牌厂家
#         tmpmsg['Product'] = board_id.Product  # 主板型号
#         boards.append(tmpmsg)
#     print('boards:', boards)
#     return boards

# # BIOS


# def printBIOS():
#     bioss = []
#     for bios_id in c.Win32_BIOS():
#         tmpmsg = {}
#         tmpmsg['BiosCharacteristics'] = bios_id.BiosCharacteristics  # BIOS特征码
#         tmpmsg['version'] = bios_id.Version  # BIOS版本
#         tmpmsg['Manufacturer'] = bios_id.Manufacturer.strip()  # BIOS固件生产厂家
#         tmpmsg['ReleaseDate'] = bios_id.ReleaseDate  # BIOS释放日期
#         tmpmsg['SMBIOSBIOSVersion'] = bios_id.SMBIOSBIOSVersion  # 系统管理规范版本
#         bioss.append(tmpmsg)
#     print('bioss:', bioss)
#     return bioss

# # 硬盘


# def printDisk():
#     disks = []
#     for disk in c.Win32_DiskDrive():
#         # print disk.__dict__
#         tmpmsg = {}
#         tmpmsg['SerialNumber'] = disk.SerialNumber.strip()
#         tmpmsg['DeviceID'] = disk.DeviceID
#         tmpmsg['Caption'] = disk.Caption
#         tmpmsg['Size'] = disk.Size
#         tmpmsg['UUID'] = disk.qualifiers['UUID'][1:-1]
#         disks.append(tmpmsg)
#     for d in disks:
#         print('disks:', d)
#     return disks

# # 内存


# def printPhysicalMemory():
#     memorys = []
#     for mem in c.Win32_PhysicalMemory():
#         tmpmsg = {}
#         tmpmsg['UUID'] = mem.qualifiers['UUID'][1:-1]
#         tmpmsg['BankLabel'] = mem.BankLabel
#         tmpmsg['SerialNumber'] = mem.SerialNumber.strip()
#         tmpmsg['ConfiguredClockSpeed'] = mem.ConfiguredClockSpeed
#         tmpmsg['Capacity'] = mem.Capacity
#         tmpmsg['ConfiguredVoltage'] = mem.ConfiguredVoltage
#         memorys.append(tmpmsg)
#     for m in memorys:
#         print('memorys:', m)
#     return memorys

# # 电池信息，只有笔记本才会有电池选项


# def printBattery():
#     isBatterys = False
#     for b in c.Win32_Battery():
#         isBatterys = True
#     return isBatterys

# # 网卡mac地址：


# def printMacAddress():
#     macs = []
#     for n in c.Win32_NetworkAdapter():
#         mactmp = n.MACAddress
#         if mactmp and len(mactmp.strip()) > 5:
#             tmpmsg = {}
#             tmpmsg['MACAddress'] = n.MACAddress
#             tmpmsg['Name'] = n.Name
#             tmpmsg['DeviceID'] = n.DeviceID
#             tmpmsg['AdapterType'] = n.AdapterType
#             tmpmsg['Speed'] = n.Speed
#             macs.append(tmpmsg)
#     print('macs:', macs)
#     return macs


# def main():

#     printCPU()
#     printMain_board()
#     printBIOS()
#     printDisk()
#     printPhysicalMemory()
#     printMacAddress()


# if __name__ == '__main__':
#     main()


# import time
# import wmi
# import zlib


# def get_cpu_info():
#     tmpdict = {}
#     tmpdict["CpuCores"] = 0
#     c = wmi.WMI()
#     #          print c.Win32_Processor().['ProcessorId']
#     #          print c.Win32_DiskDrive()
#     for cpu in c.Win32_Processor():
#         #                print cpu
#        #print("cpu id:", cpu.ProcessorId.strip())
#         tmpdict["CpuId"] = cpu.ProcessorId.strip()
#         tmpdict["CpuType"] = cpu.Name
#         try:
#             tmpdict["CpuCores"] = cpu.NumberOfCores
#         except:
#             tmpdict["CpuCores"] += 1
#             tmpdict["CpuClock"] = cpu.MaxClockSpeed
#     return tmpdict


# def _read_cpu_usage():
#     c = wmi.WMI()
#     for cpu in c.Win32_Processor():
#         return cpu.LoadPercentage


# def get_cpu_usage():
#     cpustr1 = _read_cpu_usage()
#     if not cpustr1:
#         return 0
#     time.sleep(2)
#     cpustr2 = _read_cpu_usage()
#     if not cpustr2:
#         return 0
#     cpuper = int(cpustr1) + int(cpustr2) / 2
#     return cpuper


# def get_disk_info():
#     tmplist = []
#     encrypt_str = ""
#     c = wmi.WMI()
#     for cpu in c.Win32_Processor():
#         # cpu 序列号
#         encrypt_str = encrypt_str + cpu.ProcessorId.strip()
#         print("cpu id:", cpu.ProcessorId.strip())
#     for physical_disk in c.Win32_DiskDrive():
#         encrypt_str = encrypt_str + physical_disk.SerialNumber.strip()
#         # 硬盘序列号
#         print('disk id:', physical_disk.SerialNumber.strip())
#         tmpdict = {}
#         tmpdict["Caption"] = physical_disk.Caption
#         tmpdict["Size"] = int(physical_disk.Size) / 1000 / 1000 / 1000
#         tmplist.append(tmpdict)
#     for board_id in c.Win32_BaseBoard():
#         # 主板序列号
#         encrypt_str = encrypt_str + board_id.SerialNumber.strip()
#         print("main board id:", board_id.SerialNumber.strip())
#     # for mac in c.Win32_NetworkAdapter():
#     # mac 地址（包括虚拟机的）
#     #                    print "mac addr:", mac.MACAddress:
#     for bios_id in c.Win32_BIOS():
#         # bios 序列号
#         encrypt_str = encrypt_str  # + bios_id.SerialNumber.strip()
#         print("bios number:", bios_id.SerialNumber.strip())
#     print("encrypt_str:", encrypt_str)
#     # 加密算法
#     print("加密算法：%d" % zlib.adler32(encrypt_str.encode()))
#     return encrypt_str


# if __name__ == "__main__":
#     a = get_cpu_info()
#     print("cpu: %s" % a)
#     get_disk_info()


# import json

# a = {"abc": 123}
# x = json.dump(a)
# y = json.dumps(a)
# print(x)
# print(y)

# import wx

# '''
#     Function:绘图
#     Input：NONE
#     Output: NONE
#     author: socrates
#     blog:http://www.cnblogs.com/dyx1024/
#     date:2012-07-22
# '''


# class GuageFrame(wx.Frame):
#     def __init__(self):
#         wx.Frame.__init__(self, None, -1, 'Gauge Example', size=(600, 300))
#         panel = wx.Panel(self, -1)
#         panel.SetBackgroundColour("white")
#         self.count = 0
#         self.gauge = wx.Gauge(panel, -1, 100, (100, 60),
#                               (200, 25), style=wx.GA_HORIZONTAL | wx.GA_SMOOTH, name='当前进度')
#         # self.gauge.SetBezelFace(3)
#         # self.gauge.SetShadowWidth(3)
#         self.Bind(wx.EVT_IDLE, self.OnIdle)

#     def OnIdle(self, event):
#         self.count = self.count + 1
#         if self.count >= 99:
#             self.count = 0
#         self.gauge.SetValue(self.count)


# if __name__ == '__main__':
#     app = wx.PySimpleApp()
#     frame = GuageFrame()
#     frame.Show()
#     app.MainLoop()
