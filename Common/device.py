#!/usr/bin/env python
# -*- coding: utf-8 -*-
# import os
# import sys
import wmi
from hashlib import sha1


def _cpuid(c):
    # 处理器
    for cpu in c.Win32_Processor():
        cpuid = cpu.ProcessorId.strip()
    if cpuid is not None:
        return cpuid
    else:
        return ""


def _boardid(c):
    # 主板
    for board_id in c.Win32_BaseBoard():
        SerialNumber = board_id.SerialNumber  # 主板序列号
    if SerialNumber is not None:
        return SerialNumber
    else:
        return ""


def _diskid(c):
    # 硬盘
    for disk in c.Win32_DiskDrive():
        SerialNumber = disk.SerialNumber.strip()
        UUID = disk.qualifiers['UUID'][1:-1]
    if SerialNumber is not None and UUID is not None:
        return SerialNumber+UUID
    elif SerialNumber is not None:
        return SerialNumber
    elif UUID is not None:
        return UUID
    else:
        return ""


def get_device_uuid():
    c = wmi.WMI()
    # 需要加密的字符串
    devicestr = _cpuid(c)+_boardid(c)+_diskid(c)
    # 创建sha1对象
    s1 = sha1()
    # 对s1进行更新
    s1.update(devicestr.encode())
    # 加密处理
    result = s1.hexdigest()
    # 结果是40位字符串：'40bd001563085fc35165329ea1ff5c5ecbdbbeef'
    # print(result)
    return result


if __name__ == '__main__':
    get_device_uuid()


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

# BIOS


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

# 内存
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
# 电池信息，只有笔记本才会有电池选项
# def printBattery():
#     isBatterys = False
#     for b in c.Win32_Battery():
#         isBatterys = True
#     return isBatterys
# 网卡mac地址：
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
