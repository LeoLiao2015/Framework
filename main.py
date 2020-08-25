# -*- coding: utf-8 -*-
import sys
import os
import time
import multiprocessing
from multiprocessing import Process, Queue
import traceback
import logging
import json
import os
import sys

from DB.db import LocalDB
from Ui.ui import uiMain
from Brower.brower import browerMain, browerMainE
from Control.control import controlMain
from ScrapyY.scrapyx import scrapyxMain
from Common import *

'''
启动Main  只是消息中转，和控制进程开关
    启动 UI
    登陆
    登陆成功，
    存好了做后台请求的cookies
    切换到运行界面
    UI 接收各种状态展示当前的运行状态
    通知MAIN启动CTRL

Main启动control
    control 开始工作
    启动SCRAPY
    control 根据接收到的状态

    接到任务需求
    请求任务
    检擦本地是否有拿到的任务国家的cookie
    没有就开始拿cookie
        检查是否有port
            发送启动BS的请求
            等待下一步
            
            GET COOKIE
            发送任务
            
    接到BS发莱的PORT，保存
        执行下一步

Main启动SCRAPY
    饥饿状态，发起任务需求消息给CTRL
    
    

Main启动BS
    发送PORT给CTRL

检查cookie 是否存在

不存在
告诉main 启动BS 
获取端口
连接
获取COOKIE
告诉main 关闭BS 关闭driver

告诉main 启动SCRAPY
开始等待抓取任务

control 发送抓取任务

出现新的国家
检查cookie是否存在
关闭BS 

通知SCRAPY 新的任务，更新cookie

UI  SCRAPY   BS 
MAIN
'''
# 由于scrapy 冲突
# logging.basicConfig(level=logging.INFO,
#                     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
logger = logging.getLogger(__name__)


class Main(object):
    def __init__(self):
        self.checkflag = True
        self.params = dict()

    # 启动UI + CTRL 其他的等待指令
    def run(self):
        self.process_ui = None
        self.process_ctrl = None
        self.process_bs = None
        self.process_bse = None
        self.process_scrapy = None

        self.qi_ui = Queue()
        self.qo_ui = Queue()

        self.qi_ctrl = Queue()
        self.qo_ctrl = Queue()

        self.qo_bs = Queue()
        self.qo_bse = Queue()

        self.qi_scrapy = Queue()
        self.qo_scrapy = Queue()

        self.process_ui = multiprocessing.Process(
            target=uiMain, name=AX_NAME_UI, args=(self.qi_ui, self.qo_ui,))
        self.process_ui.daemon = True
        self.process_ui.start()

        self._mainLoop()

    def _mainLoop(self):
        while True:
            msg_ui = msg_bs = msg_bse = msg_ctrl = msg_scrapy = None
            if self.qo_ui.empty() != True:
                msg_ui = self.qo_ui.get(block=False)
                self._onMsg(msg_ui)
            if self.qo_bs.empty() != True:
                msg_bs = self.qo_bs.get(block=False)
                self._onMsg(msg_bs)
            if self.qo_bse.empty() != True:
                msg_bse = self.qo_bse.get(block=False)
                self._onMsg(msg_bse)
            if self.qo_ctrl.empty() != True:
                msg_ctrl = self.qo_ctrl.get(block=False)
                self._onMsg(msg_ctrl)
            if self.qo_scrapy.empty() != True:
                msg_scrapy = self.qo_scrapy.get(block=False)
                self._onMsg(msg_scrapy)
            # 检查进程生命状态
            if True == self._check_child():
                break
            # 没拿到消息休息
            if msg_ui is None and msg_bs is None and msg_bse is None and msg_ctrl is None and msg_scrapy is None:
                time.sleep(0.1)

    def _check_child(self):
        # BS 需要切换逻辑的时候需要重新启动
        if self.checkflag != True:
            return
        # 任何进程退出，直接结束
        if ((self.process_ui is not None and self.process_ui.is_alive() != True)
                or (self.process_ctrl is not None and self.process_ctrl.is_alive() != True)
                or (self.process_bse is not None and self.process_bse.is_alive() != True)
                or (self.process_bs is not None and self.process_bs.is_alive() != True)
                or (self.process_scrapy is not None and self.process_scrapy.is_alive() != True)):
            if self.process_ui is not None and self.process_ui.is_alive():
                self.process_ui.terminate()
            if self.process_ctrl is not None and self.process_ctrl.is_alive():
                self.process_ctrl.terminate()
            if self.process_bs is not None and self.process_bs.is_alive():
                self.process_bs.terminate()
            if self.process_bse is not None and self.process_bse.is_alive():
                self.process_bse.terminate()
            if self.process_scrapy is not None and self.process_scrapy.is_alive():
                self.process_scrapy.terminate()

            self.process_scrapy = None
            self.process_bs = None
            self.process_bse = None
            self.process_ctrl = None
            self.process_ui = None
            return True

    def _onMsg(self, msg):
        '''
        MSG 格式：
        SRC_NAME:DST_NAME:JSON

        UI/BS/CTRL/MAIN
        '''
        if isinstance(msg, dict) != True:
            logger.info(
                "msg type:{} is not dict error".format(type(msg)))
            return
        logger.debug("main get msg:{}".format(msg))
        # try:
        #     info = json.loads(msg)
        # except Exception:
        #     logger.info("json format error msg:{}".format(info))
        #     return

        DST = msg.get('DST')
        # 广播消息 除了自己，都发
        if DST is None or len(DST) <= 0:
            if msg['SRC'] != AX_NAME_UI:
                self.qi_ui.put(msg)
            if msg['SRC'] != AX_NAME_CTRL:
                self.qi_ctrl.put(msg)
            if msg['SRC'] != AX_NAME_SCRAPY:
                self.qi_scrapy.put(msg)
            # BS 不接收消息
        # 消息转发
        elif DST == AX_NAME_UI:
            self.qi_ui.put(msg)
        elif DST == AX_NAME_CTRL:
            self.qi_ctrl.put(msg)
        elif DST == AX_NAME_SCRAPY:
            self.qi_scrapy.put(msg)
        # 自身处理
        elif DST == AX_NAME_MAIN:
            self._onMsgMain(msg)

    def _onMsgMain(self, msg):
        params = msg.get('PARAMS')
        if msg.get('TYPE') == AX_TYPE_MAIN_CREATE:
            if params is not None and params.get('name') == AX_NAME_CTRL:
                if self.process_ctrl is None:
                    self.process_ctrl = multiprocessing.Process(
                        target=controlMain, name=AX_NAME_CTRL, args=(self.qi_ctrl, self.qo_ctrl,))
                    self.process_ctrl.daemon = True
                    self.process_ctrl.start()
            elif params is not None and params.get('name') == AX_NAME_BS:
                if self.process_bs is None:
                    self.process_bs = multiprocessing.Process(
                        target=browerMain, name=AX_NAME_BS, args=(self.qo_bs,))
                    self.process_bs.daemon = True
                    self.process_bs.start()
            elif params is not None and params.get('name') == AX_NAME_SCRAPY:
                if self.process_scrapy is None:
                    self.process_scrapy = multiprocessing.Process(
                        target=scrapyxMain, name=AX_NAME_SCRAPY, args=(self.qi_scrapy, self.qo_scrapy,))
                    self.process_scrapy.daemon = True
                    self.process_scrapy.start()

        elif msg.get('TYPE') == AX_TYPE_MAIN_DESTORY:
            if params is not None and params.get('name') == AX_NAME_CTRL:
                if self.process_ctrl is not None:
                    self.process_ctrl.terminate()
                    self.process_ctrl = None
            elif params is not None and params.get('name') == AX_NAME_BS:
                if self.process_bs is not None:
                    self.process_bs.terminate()
                    self.process_bs = None
            elif params is not None and params.get('name') == AX_NAME_SCRAPY:
                if self.process_scrapy is not None:
                    self.process_scrapy.terminate()
                    self.process_scrapy = None
            # self.process_bse = multiprocessing.Process(
            #     target=browerMainE, name=AX_NAME_BS, args=(self.qo_bse,))
            # self.process_bse.daemon = True


if __name__ == '__main__':
    multiprocessing.freeze_support()
    try:
        # DB 数据初始化
        LocalDB.instance()

        Main().run()
    except Exception as e:
        logger.error("error...{}".format(e))
        msg = traceback.format_exc()  # 方式1
        logger.error(msg)

    # os.chdir(os.getcwd() + '\\ScrapyX')  # 更改路径
    # process_scrapy = multiprocessing.Process(target=scrapyxMain)
    # process_scrapy.daemon = True
    # process_scrapy.start()
    # while True:
    #     time.sleep(1)
    # print(os.path)
    # print(sys.path)
    # sys.path.append(".")
    # sys.path.append("..")
    # sys.path.insert(0, os.getcwd() + '\\ScrapyX')
    # sys.path.append(os.getcwd() + '\\ScrapyX')

    # print(sys.path)
    # print(os.path.abspath('.'))
    # print(os.getcwd())
    # print(os.path.abspath(os.path.join(os.getcwd(), "../..")))
    # print(os.path.abspath(os.path.dirname(os.getcwd())))
    # sys.path[0] = os.getcwd() + '\\ScrapyX'
    # scrapyxMain()
