# -*- coding: utf-8 -*-
if __name__ == "__main__":
    import os
    import sys
    import logging
    # print(os.getcwd())
    # print(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
    # print(os.path.abspath(os.path.dirname(os.getcwd())))
    # print(os.path.abspath(os.path.join(os.getcwd(), "..")))
    sys.path.append(os.getcwd())
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
else:
    import os
    import logging
import time
from selenium import webdriver
from multiprocessing import Queue
import traceback
import json
import random
import threading
import requests
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait  # available since 2.4.0
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
# from Common import AX_CMD_DCONNECT, AX_CMD_GET_TASK, AX_CMD_CHANGE_COOKIE
from Common import *
from Common.msg import send_msg
from Common.device import get_device_uuid
from Common.global_cfg import GLOBAL_CFG_API_SERVER
from DB.db import LocalDB

'''
启动后
1、用户登陆操作
2、通过API获取采集任务
3、存储采集结果
4、上报采集结果
5、循环获取采集任务
'''

logger = logging.getLogger(__name__)


class Control(object):
    def __init__(self, qi=None, qo=None):
        self.qi = qi
        self.qo = qo
        self.driver = None
        self.port = 0
        self.task_list = []
        self.clientid = get_device_uuid()
        self.msg_call = []
        self.msg_filter = set()
        self.retry = 0
        self.page_load_timeout = 20
        
        db = LocalDB.instance()
        self.session = requests.Session()
        cookies_dict = db.load_user_cookie()
        self.session.cookies = requests.utils.cookiejar_from_dict(cookies_dict, cookiejar=None, overwrite=True)

        self.contry = ""
        self.contry_cookies = dict()
        # 每次重启都重新拿cookie
        # self.contry_cookies['US'] = db.load_contry_cookie('US')
        # self.contry_cookies['UK'] = db.load_contry_cookie('UK')
        # self.contry_cookies['DE'] = db.load_contry_cookie('DE')
        # self.contry_cookies['FR'] = db.load_contry_cookie('FR')
        # self.contry_cookies['IT'] = db.load_contry_cookie('IT')
        # for contry in self.contry_cookies.keys():
        #     if self.contry_cookies[contry] is not None:
        #         logger.info('cookie:{}'.format(contry))
        #         logger.info(self.contry_cookies[contry])
        
    def _get_homepage_url(self, contry):
        if contry == 'US':
            return 'https://www.amazon.com'
        elif contry == 'UK':
            return 'https://www.amazon.co.uk'
        elif contry == 'DE':
            return 'https://www.amazon.de'
        elif contry == 'FR':
            return 'https://www.amazon.fr'
        elif contry == 'it':
            return 'https://www.amazon.it'
        else:
            return 'https://www.amazon.com'

    # 多做几个备选的邮编
    def _get_postcode(self, contry):
        if contry == 'US':
            return random.choice(['20010', '10075'])        # 华盛顿    # 10075 纽约
        elif contry == 'UK':
            return random.choice(['WC2H 7HQ', 'WC2H 7HQ'])  # 伦敦
        elif contry == 'DE':
            return random.choice(['10117', '10117'])     # 柏林
        elif contry == 'FR':
            return random.choice(['75018', '75018'])     # 巴黎
        elif contry == 'it':
            return random.choice(['50122', '50122'])     # 佛罗伦萨
        else:
            return random.choice(['20010', '10075'])

    # def _get_cookie_file(self, contry):
    #     if contry == 'US':
    #         return 'cookies_us.txt'
    #     elif contry == 'UK':
    #         return 'cookies_uk.txt'
    #     elif contry == 'DE':
    #         return 'cookies_de.txt'
    #     elif contry == 'FR':
    #         return 'cookies_fr.txt'
    #     elif contry == 'it':
    #         return 'cookies_it.txt'
    #     else:
    #         return 'cookies_us.txt'

    def _get_start_options(self, port, flag=0):
        '''根据参数获取默认启动属性
            0：默认全部属性
            1：不加载图片，不加载JS
            2：无头模式
        '''
        chrome_option = webdriver.ChromeOptions()
        chrome_option._debugger_address = "localhost:{}".format(port)
        chrome_option.add_argument("--ignore-certificate-errors",)
        chrome_option.add_argument("--ignore-ssl-errors")
        return chrome_option

    def _devtools_connect(self, port=None):
        if port is not None:
            self.port = port
        chrome_option = self._get_start_options(self.port)
        try:
            self.driver = webdriver.Chrome(
                executable_path='./chromedriver.exe', options=chrome_option)
            self.driver.set_page_load_timeout(self.page_load_timeout)
            # info = self.driver.get_network_conditions()
            # logger.info("info:{}".format(info))
            # self.driver.get("https://www.163.com")
        except Exception as e:
            msg = traceback.format_exc()  # 方式1
            logger.error("_devtools_connect error...{}{}".format(e, msg))
        return self.driver

    def _devtools_disconnect(self):
        if self.driver is not None:
            # self.driver.quit()
            self.driver = None

    def _get_contry_captcha(self, contry, captcha, url=None):
        try:
            driver = self.driver
            send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'人机验证 开始'})
            # 空的，填入验证码
            elements = driver.find_elements_by_id('captchacharacters')
            if len(elements) > 0:
                elements[0].send_keys(captcha)
                time.sleep(1)
            else:
                # 重来一次
                raise Exception        
                
            # 点击提交
            elements = driver.find_elements_by_tag_name('button')
            if len(elements) > 0:
                elements[0].click()
                time.sleep(2)
            else:
                # 重来一次
                raise Exception 
            
            send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'人机验证 等待验证'})
            # 正常处理了人机验证 等待页面跳转
            WebDriverWait(driver, 8, 0.5).until(EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="nav-global-location-slot"]')))
            
            elements = driver.find_elements_by_id(
                'nav-global-location-slot')
            if len(elements) > 0:
                # a-popover-trigger a-declarative
                elements = elements[0].find_elements_by_xpath(".//a")
                if len(elements) > 0:
                    elements[0].click()
                    time.sleep(1)
            else:
                # 重来一次
                raise Exception 
            
            send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'人机验证 等待配置验证'})
            WebDriverWait(driver, 5, 0.5).until(
                lambda driver: driver.find_elements_by_id('GLUXZipUpdateInput'))
            
            # 默认应该有区域
            has_area = True
            elements = driver.find_elements_by_id('GLUXZipConfirmationSection')
            if len(elements) > 0:
                # 英国不能用这个判断
                has_area = "GLUX_Hidden" not in elements[0].get_attribute("class")            
            # 判断当前是否有可用的区域信息
            # elements = driver.find_elements_by_id('GLUXChangePostalCodeLink')
            if has_area == True:
                cookies = driver.get_cookies()
                logger.info(cookies)
                # with open(self._get_cookie_file(contry), "w") as fp:
                #     json.dump(cookies, fp)
                db = LocalDB.instance()
                db.save_contry_cookie(contry, cookies)
                self.contry_cookies[contry] = cookies
                logger.info("{} new cookie save done".format(contry))
                send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'人机验证 完毕'})
                # 关闭BS 消息
                self._devtools_disconnect()
                self.port = 0
                send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'BS采集器 关闭'})
                send_msg(self.qo, AX_NAME_CTRL, AX_NAME_MAIN, AX_TYPE_MAIN_DESTORY, {"name":AX_NAME_BS})
                # 恢复消息响应
                self._removemsg_filter(AX_TYPE_CTRL_GET_TASK)                
            else:
                # 重来一次
                send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'人机验证 配置重试'})
                self._get_contry_cookies(contry, reset=False, change=True)
        except Exception as e:
            msg = traceback.format_exc()  # 方式1
            logger.error("error...{}{}".format(e, msg))
            send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'人机验证 失败...重试'})
            self._get_contry_cookies(contry, url=url)
        
    def _get_contry_cookies(self, contry, url=None, reset=True, change=True):
        if self.port is None or self.port == 0:
            send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 无法连接BS采集器...'})
            logger.info("无法连接BS采集器...")
            return
        if self.driver is None:
            self._devtools_connect()
        driver = self.driver
        driver.set_page_load_timeout(self.page_load_timeout)
        while True:
            try:
                send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 清空BS采集器历史配置...'})
                # 先清空当前cookie
                if url is not None:
                    driver.get(url)
                else:
                    driver.get(self._get_homepage_url(contry))
                time.sleep(1)
                # TODO 这里有机会出现人机检查，需要判断   Bot Check  Robot Check
                # 如果是人机检查，调用UI通知用户输入验证码
                # 解析得到验证码图片地址
                # 发送给UI 消息来展示并接收用户的输入
                # 设置用户输入的消息回调  调用 输入验证码并点击确认，之后再次调用这里
                # 退出
                if driver.title is not None and len(driver.title) > 0 and (driver.title.find("Check") != -1
                           or driver.title.find("CAPTCHA") != -1):
                    WebDriverWait(driver, 15, 0.5).until(EC.visibility_of_element_located(
                        (By.XPATH, '//form//img')))
                    elements = driver.find_elements_by_xpath("//form//img")
                    if len(elements) > 0:
                        # a-popover-trigger a-declarative
                        img_link = elements[0].get_attribute("src")
                        if img_link is not None and len(img_link) > 0:
                            # 设置消息关联 callback
                            self._setmsg_call(AX_TYPE_CTRL_CAPTCHA, self._get_contry_captcha, contry, url)
                            # 发送消息通知UI来展示
                            send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 等待用户输入验证码'})
                            send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_CAPTCHA, {"img":img_link})
                    return
                
                WebDriverWait(driver, 15, 0.5).until(EC.element_to_be_clickable(
                    (By.XPATH, '//*[@id="nav-global-location-slot"]')))
                if reset == True:
                    logger.info("get old cookie")
                    cookies = driver.get_cookies()
                    if cookies is not None and len(cookies) > 0:
                        # 删除cookie
                        logger.info("del old cookie")
                        for cookie in cookies:
                            driver.delete_cookie(cookie["name"])
                        driver.delete_all_cookies()
                        time.sleep(1)
                        cookies = driver.get_cookies()
                        # 检查cookie是否删除成功
                        if cookies is None or len(cookies) > 0:
                            logger.info("cookies is not null")
                            logger.info(cookies)
                            raise Exception
                        # 重新打开
                        # driver.get(self._get_homepage_url(contry))
                        driver.refresh()
                        WebDriverWait(driver, 15, 0.5).until(EC.element_to_be_clickable(
                            (By.XPATH, '//*[@id="nav-global-location-slot"]')))

                    # 还有残留数据，Change 按钮
                    # elements = driver.find_elements_by_id('GLUXChangePostalCodeLink')
                    # if len(elements) > 0:
                    #     # 重来一次
                    #     logger.info("reset is not null")
                    #     raise Exception

                if change == True:
                    # 开始更新区域
                    send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 设置新的BS采集器配置...'})
                    elements = driver.find_elements_by_id(
                        'nav-global-location-slot')
                    if len(elements) > 0:
                        # a-popover-trigger a-declarative
                        elements = elements[0].find_elements_by_xpath(".//a")
                        if len(elements) > 0:
                            elements[0].click()
                            
                        # 默认应该有区域
                        elements = driver.find_elements_by_id('GLUXZipConfirmationSection')
                        if len(elements) > 0:
                            # 英国不能用这个判断
                            has_area = "GLUX_Hidden" not in elements[0].get_attribute("class")            
                            if has_area == True:
                                elements = driver.find_elements_by_id('GLUXChangePostalCodeLink')
                                if len(elements) > 0:
                                    elements[0].click()
                                    time.sleep(1)

                        WebDriverWait(driver, 5, 0.5).until(
                            lambda driver: driver.find_elements_by_id('GLUXZipUpdateInput'))
                        # 空的，填入地址
                        elements = driver.find_elements_by_id('GLUXZipUpdateInput')
                        if len(elements) > 0:
                            elements[0].clear()
                            elements[0].send_keys(self._get_postcode(contry))
                            time.sleep(1)
                        # 点击提交
                        elements = driver.find_elements_by_id('GLUXZipUpdate')
                        if len(elements) > 0:
                            elements[0].click()
                            time.sleep(2)
                        else:
                            # 重来一次
                            logger.info("Update error")
                            raise Exception

                        # 点击确认更改
                        elements = driver.find_elements_by_xpath(
                            '//div[@class="a-popover-footer"]')
                        if len(elements) > 0:
                            element = elements[0]
                            WebDriverWait(driver, 5, 0.5).until(
                                lambda element: element.find_elements_by_id('GLUXConfirmClose'))
                            elements = element.find_elements_by_id(
                                'GLUXConfirmClose')
                            if len(elements) > 0:
                                elements[0].click()
                                time.sleep(2)
                                WebDriverWait(driver, 5, 0.5).until(EC.element_to_be_clickable(
                                    (By.XPATH, '//*[@id="nav-global-location-slot"]')))
                            else:
                                # 重来一次
                                logger.info("footer Confirm error")
                                raise Exception
                        # 英国不需要二次确认这个逻辑，直接成功

                cookies = driver.get_cookies()
                logger.info(cookies)
                # with open(self._get_cookie_file(contry), "w") as fp:
                #     json.dump(cookies, fp)
                db = LocalDB.instance()
                db.save_contry_cookie(contry, cookies)
                self.contry_cookies[contry] = cookies
                logger.info("{} new cookie save done".format(contry))
                send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 更新BS采集器配置...完成'})
                # 关闭BS 消息
                self._devtools_disconnect()
                self.port = 0
                send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 关闭BS采集器'})
                send_msg(self.qo, AX_NAME_CTRL, AX_NAME_MAIN, AX_TYPE_MAIN_DESTORY, {"name":AX_NAME_BS})
                # 恢复消息响应
                self._removemsg_filter(AX_TYPE_CTRL_GET_TASK)
                break
            except Exception as e:
                msg = traceback.format_exc()  # 方式1
                logger.error("error...{}{}".format(e, msg))
                self._devtools_disconnect()
                self._devtools_connect(self.port)
                driver = self.driver
                driver.set_page_load_timeout(self.page_load_timeout)
                self.retry += 1
                send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 更新BS采集器配置...重试 {}'.format(self.retry)})
                
                if self.retry >= 3:
                    self.retry = 0
                    if msg.find('timeout') != -1:
                        send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 请求BS采集器超时 请检查网络环境'})
                    send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 请求BS采集器复位...重试'})

                    # 设置消息关联 callback
                    self._setmsg_call(AX_TYPE_CTRL_SET_PORT, self._get_contry_cookies, contry)
                    # 关闭BS 重新开启
                    send_msg(self.qo, AX_NAME_CTRL, AX_NAME_MAIN, AX_TYPE_MAIN_DESTORY, {"name":AX_NAME_BS})
                    # 启动BS 消息
                    send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 请求BS采集器启动'})
                    send_msg(self.qo, AX_NAME_CTRL, AX_NAME_MAIN, AX_TYPE_MAIN_CREATE, {"name":AX_NAME_BS})
                    break

    def _get_block_cookies(self, contry, url=None, reset=True, change=True):
        if self.port is None or self.port == 0:
            send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 无法连接BS采集器...'})
            logger.info("无法连接BS采集器...")
            return
        if self.driver is None:
            self._devtools_connect()
        # 装在当前cookie值
        send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 加载当前BS采集器配置'})
        self._read_cookies(contry)
            
        driver = self.driver
        driver.set_page_load_timeout(self.page_load_timeout)
        while True:
            try:
                send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 BS采集器打开BLOCK链接...'})
                # 主动打开人机测试
                if url is None:
                    url = self._get_homepage_url(contry)+'/errors/validateCaptcha'
                driver.get(url)
                time.sleep(1)
                # TODO 这里有机会出现人机检查，需要判断   Bot Check  Robot Check
                # 如果是人机检查，调用UI通知用户输入验证码
                # 解析得到验证码图片地址
                # 发送给UI 消息来展示并接收用户的输入
                # 设置用户输入的消息回调  调用 输入验证码并点击确认，之后再次调用这里
                # 退出
                if driver.title is not None and len(driver.title) > 0 and (driver.title.find("Check") != -1
                           or driver.title.find("CAPTCHA") != -1):
                    WebDriverWait(driver, 15, 0.5).until(EC.visibility_of_element_located(
                        (By.XPATH, '//form//img')))
                    elements = driver.find_elements_by_xpath("//form//img")
                    if len(elements) > 0:
                        # a-popover-trigger a-declarative
                        img_link = elements[0].get_attribute("src")
                        if img_link is not None and len(img_link) > 0:
                            # 设置消息关联 callback
                            self._setmsg_call(AX_TYPE_CTRL_CAPTCHA, self._get_contry_captcha, contry, url)
                            # 发送消息通知UI来展示
                            send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 等待用户输入验证码'})
                            send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_CAPTCHA, {"img":img_link})
                    return
                
                WebDriverWait(driver, 15, 0.5).until(EC.element_to_be_clickable(
                    (By.XPATH, '//*[@id="nav-global-location-slot"]')))
                if reset == True:
                    logger.info("get old cookie")
                    cookies = driver.get_cookies()
                    if cookies is not None and len(cookies) > 0:
                        # 删除cookie
                        logger.info("del old cookie")
                        for cookie in cookies:
                            driver.delete_cookie(cookie["name"])
                        driver.delete_all_cookies()
                        time.sleep(1)
                        cookies = driver.get_cookies()
                        # 检查cookie是否删除成功
                        if cookies is None or len(cookies) > 0:
                            logger.info("cookies is not null")
                            logger.info(cookies)
                            raise Exception
                        # 重新打开
                        # driver.get(self._get_homepage_url(contry))
                        driver.refresh()
                        WebDriverWait(driver, 15, 0.5).until(EC.element_to_be_clickable(
                            (By.XPATH, '//*[@id="nav-global-location-slot"]')))

                    # 还有残留数据，Change 按钮
                    # elements = driver.find_elements_by_id('GLUXChangePostalCodeLink')
                    # if len(elements) > 0:
                    #     # 重来一次
                    #     raise Exception
                    
                if change == True:
                    # 开始更新区域
                    send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 设置新的BS采集器配置...'})
                    elements = driver.find_elements_by_id(
                        'nav-global-location-slot')
                    if len(elements) > 0:
                        # a-popover-trigger a-declarative
                        elements = elements[0].find_elements_by_xpath(".//a")
                        if len(elements) > 0:
                            elements[0].click()
                            
                        # 默认应该有区域
                        elements = driver.find_elements_by_id('GLUXZipConfirmationSection')
                        if len(elements) > 0:
                            # 英国不能用这个判断
                            has_area = "GLUX_Hidden" not in elements[0].get_attribute("class")            
                            if has_area == True:
                                elements = driver.find_elements_by_id('GLUXChangePostalCodeLink')
                                if len(elements) > 0:
                                    elements[0].click()
                                    time.sleep(1)

                        WebDriverWait(driver, 5, 0.5).until(
                            lambda driver: driver.find_elements_by_id('GLUXZipUpdateInput'))
                        # 空的，填入地址
                        elements = driver.find_elements_by_id('GLUXZipUpdateInput')
                        if len(elements) > 0:
                            elements[0].clear()
                            elements[0].send_keys(self._get_postcode(contry))
                            time.sleep(1)
                        # 点击提交
                        elements = driver.find_elements_by_id('GLUXZipUpdate')
                        if len(elements) > 0:
                            elements[0].click()
                            time.sleep(2)
                        else:
                            # 重来一次
                            logger.info("Update error")
                            raise Exception

                        # 点击确认更改
                        elements = driver.find_elements_by_xpath(
                            '//div[@class="a-popover-footer"]')
                        if len(elements) > 0:
                            element = elements[0]
                            WebDriverWait(driver, 5, 0.5).until(
                                lambda element: element.find_elements_by_id('GLUXConfirmClose'))
                            elements = element.find_elements_by_id(
                                'GLUXConfirmClose')
                            if len(elements) > 0:
                                elements[0].click()
                                time.sleep(2)
                                WebDriverWait(driver, 5, 0.5).until(EC.element_to_be_clickable(
                                    (By.XPATH, '//*[@id="nav-global-location-slot"]')))
                            else:
                                # 重来一次
                                logger.info("footer Confirm error")
                                raise Exception
                        # 英国不需要二次确认这个逻辑，直接成功

                cookies = driver.get_cookies()
                logger.info('new cookie:{}'.format(cookies))
                # with open(self._get_cookie_file(contry), "w") as fp:
                #     json.dump(cookies, fp)
                db = LocalDB.instance()
                db.save_contry_cookie(contry, cookies)
                self.contry_cookies[contry] = cookies
                logger.info("{} new cookie save done".format(contry))
                send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 更新BS采集器配置...完成'})
                # 关闭BS 消息
                self._devtools_disconnect()
                self.port = 0
                send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 关闭BS采集器'})
                send_msg(self.qo, AX_NAME_CTRL, AX_NAME_MAIN, AX_TYPE_MAIN_DESTORY, {"name":AX_NAME_BS})
                # 恢复消息响应
                self._removemsg_filter(AX_TYPE_CTRL_GET_TASK)
                break
            except Exception as e:
                msg = traceback.format_exc()  # 方式1
                logger.error("error...{}{}".format(e, msg))
                self._devtools_disconnect()
                self._devtools_connect(self.port)
                driver = self.driver
                driver.set_page_load_timeout(self.page_load_timeout)
                self.retry += 1
                send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 更新BS采集器配置...重试 {}'.format(self.retry)})
                
                if self.retry >= 3:
                    self.retry = 0
                    if msg.find('timeout') != -1:
                        send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 请求BS采集器超时 请检查网络环境'})
                    send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 请求BS采集器复位...重试'})

                    # 设置消息关联 callback
                    self._setmsg_call(AX_TYPE_CTRL_SET_PORT, self._get_contry_cookies, contry)
                    # 关闭BS 重新开启
                    send_msg(self.qo, AX_NAME_CTRL, AX_NAME_MAIN, AX_TYPE_MAIN_DESTORY, {"name":AX_NAME_BS})
                    # 启动BS 消息
                    send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 请求BS采集器启动'})
                    send_msg(self.qo, AX_NAME_CTRL, AX_NAME_MAIN, AX_TYPE_MAIN_CREATE, {"name":AX_NAME_BS})
                    break

    def _read_cookies(self, contry):
        driver = self.driver
        while True:
            try:
                driver.get(self._get_homepage_url(contry))
                break
            except Exception as e:
                logger.debug(e)
                pass

        db = LocalDB.instance()
        cookies = db.load_contry_cookie(contry)
        logger.info('old cookie:{}'.format(cookies))
        for cookie in cookies:
            # cookie.pop('domain')  # 如果报domain无效的错误
            if cookie.get('expiry') is not None:
                cookie['expiry'] = int(cookie.get('expiry'))
            driver.add_cookie(cookie)

        # with open(self._get_cookie_file(contry), "r") as fp:
        #     cookies = json.load(fp)
        #     # #将每一次遍历的cookie中的这五个键名和键值添加到cookie
        #     # driver2.add_cookie({k: cookie[k] for k in {'name', 'value', 'domain', 'path', 'expiry'}})
        #     for cookie in cookies:
        #         # cookie.pop('domain')  # 如果报domain无效的错误
        #         if cookie.get('expiry') is not None:
        #             cookie['expiry'] = int(cookie.get('expiry'))
        #         driver.add_cookie(cookie)
        
        # while True:
        #     try:
        #         driver.get(self._get_homepage_url(contry))
        #         break
        #     except Exception as e:
        #         logger.debug(e)
        #         pass

    def _refresh_cookie(self, contry):
        if self.driver is None:
            return
        logger.info('_refresh_cookie...')

    # 设置消息响应回调
    def _setmsg_call(self, mtype, callfunc, arg0=None, arg1=None, arg2=None):
        self.msg_call.append((mtype, callfunc, arg0, arg1, arg2))
    
    # 添加消息过滤
    def _addmsg_filter(self, mtype):
        send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 跳过 数据请求响应'})
        self.msg_filter.add(mtype)
    
    # 删除消息过滤
    def _removemsg_filter(self, mtype):
        msg_list = []
        while True:
            if self.qi.empty() == True:
                break
            try:
                msg = self.qi.get(False)
                msg_list.append(msg)
            except Exception as e:
                msg = traceback.format_exc()  # 方式1
                logger.error("error...{}{}".format(e, msg))
        for msg in msg_list:
            if msg.get("TYPE") != mtype:
                self.qi.put(msg)        
        self.msg_filter.discard(mtype)
        send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 恢复 数据请求响应'})

    def _get_task(self):
        try:
            send_flag = True
            if len(self.task_list) <= 0:
                response = self.session.get(
                    "{}/api/v2.0/analyzetask?client={}&count=2".format(
                        GLOBAL_CFG_API_SERVER, self.clientid))
                print(response)
                if response.status_code != 200:
                    return
                content = json.loads(response.text)
                # US_B07XRGC9F2_37_Automotive_2_309
                self.task_list += content["data"]

                if content.get('data') is not None and len(content["data"]) > 0:
                    send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 获取采集任务:{}'.format(len(content["data"]))})
                    task_contry = content["data"][0].split("_")[0]
                    if len(task_contry) == 2 and self.contry_cookies.get(task_contry) is None:
                        send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 等待更新BS采集器配置...'})
                        if self.port == 0:
                            # 不响应 请求任务的消息
                            self._addmsg_filter(AX_TYPE_CTRL_GET_TASK)
                            # 设置消息关联 callback
                            self._setmsg_call(AX_TYPE_CTRL_SET_PORT, self._get_contry_cookies, task_contry)
                            # 启动BS 消息
                            send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 请求BS采集器启动'})
                            send_msg(self.qo, AX_NAME_CTRL, AX_NAME_MAIN, AX_TYPE_MAIN_CREATE, {"name":AX_NAME_BS})
                            send_flag = False
                        else:
                            self._get_contry_cookies(task_contry)
                else:
                    send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 ...数据采集器Timer...'})
                # 设置等待任务数长度
                if content.get("wait_count") is not None:
                    send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_WAIT, {"text":str(content.get("wait_count"))})
            if send_flag != False:
                # 判断新拿到的TASK contry cookie 是否存在，没有就获取
                # 获取contry cookie 判断driver 是否存在 port 是否可用
                # 没有就发送消息启动BS，等待BS启动
                if len(self.task_list) > 0:
                    item = self.task_list.pop(0)  # index=-1
                    if self.qo is not None and item is not None and len(item) > 0:
                        send_msg(self.qo, AX_NAME_CTRL, AX_NAME_SCRAPY, AX_TYPE_SCRAPY_TASK, {"item":item})
                        send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 发送采集任务 -> 数据采集器'})
        except Exception as e:
            msg = traceback.format_exc()  # 方式1
            logger.error("controlMain error...{}{}".format(e, msg))

    def _get_block(self, params):
        send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 ...数据采集器BLOCK...'})
        # 设置消息关联 callback
        self._setmsg_call(AX_TYPE_CTRL_SET_PORT, self._get_block_cookies, params.get("contry")) # , params.get("url")
        # 启动BS 此时SCRAPY 已经自行退出 更新cookie 也可能触发人机交互
        send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 请求BS采集器启动'})
        send_msg(self.qo, AX_NAME_CTRL, AX_NAME_MAIN, AX_TYPE_MAIN_CREATE, {"name":AX_NAME_BS})
        # 不响应 请求任务的消息
        self._addmsg_filter(AX_TYPE_CTRL_GET_TASK)
        # 告诉MAIN程序退出(由control 更新以后 再次重新启动)
        send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 请求数据采集器关闭'})
        send_msg(self.qo, AX_NAME_CTRL, AX_NAME_MAIN, AX_TYPE_MAIN_DESTORY, {"name":AX_NAME_SCRAPY})
        # 再次启动SCRAPY
        send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 请求数据采集器启动'})
        send_msg(self.qo, AX_NAME_CTRL, AX_NAME_MAIN, AX_TYPE_MAIN_CREATE, {"name": AX_NAME_SCRAPY})

    def _do_msg(self, msg):
        if msg is None:
            return
        if isinstance(msg, dict) != True:
            logger.info("msg type:{} is not dict error".format(type(msg)))
            return
        # 特定状态下忽略事件
        if msg.get('TYPE') in self.msg_filter:
            send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 ...数据采集器Timer...'})
            return

        params = msg.get('PARAMS')
        if msg.get('TYPE') == AX_TYPE_CTRL_SET_PORT:
            self._devtools_connect(params.get("devtools_port"))
            send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 BS采集器已连接...'})
        elif msg.get('TYPE') == AX_TYPE_CTRL_GET_TASK:
            self._get_task()
        elif msg.get('TYPE') == AX_TYPE_CTRL_RETRY_TASK:
            send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 数据采集器任务回溯 {}'.format(params.get("item"))})
            self.task_list.insert(0, params.get("item"))
        elif msg.get('TYPE') == AX_TYPE_CTRL_CLIENT_ID:
            send_msg(self.qo, AX_NAME_CTRL, msg.get('SRC'), AX_TYPE_ALL_PARAMS, {"clientid": self.clientid})
        elif msg.get('TYPE') == AX_TYPE_CTRL_BLOCK:
            self._get_block(params)
        elif msg.get('TYPE') == AX_TYPE_CTRL_CAPTCHA:
            send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 输入验证码:{} -> BS采集器'.format(params.get("captcha"))})

        # 执行消息回调函数，调用一次以后就要清空这个回调状态
        index = 0
        for item in self.msg_call:
            if item[0] == msg.get('TYPE'):
                if msg.get('TYPE') == AX_TYPE_CTRL_SET_PORT:
                    self.msg_call.pop(index)
                    send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 等待更新BS采集器配置...'})
                    # _get_block_cookies
                    if item[3] is not None:
                        item[1](item[2], item[3])
                    else:
                        # _get_contry_cookies
                        item[1](item[2])
                    break
                elif msg.get('TYPE') == AX_TYPE_CTRL_CAPTCHA:
                    self.msg_call.pop(index)
                    send_msg(self.qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 等待BS采集器执行人机验证...'})
                    # _get_contry_captcha
                    item[1](item[2], params.get("captcha"), item[3])
                    break
            index += 1

    def run(self): 
        while self.qi:
            try:
                msg = self.qi.get(True)
                logger.info('controlMain Get msg from queue:{}'.format(msg))
                self._do_msg(msg)
            except Exception as e:
                msg = traceback.format_exc()  # 方式1
                logger.error("controlMain error...{}{}".format(e, msg))
                time.sleep(1)


def controlMain(qi=None, qo=None, port=None):
    send_msg(qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 启动...'})
    ctrl = Control(qi, qo)
    # 启动SCRAPY
    send_msg(qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 请求数据采集器启动'})
    send_msg(qo, AX_NAME_CTRL, AX_NAME_MAIN, AX_TYPE_MAIN_CREATE, {"name": AX_NAME_SCRAPY})
    send_msg(qo, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'控制器 启动完毕'})
    ctrl.run()

if __name__ == "__main__":
    # controlMain()
    ctrl = Control()
    ctrl._devtools_connect(54121)
    ctrl._get_contry_cookies('US', url='https://www.amazon.com/errors/validateCaptcha')
    ctrl._get_contry_captcha('US', '123456')
    # ctrl._get_task()
    
    # ctrl._devtools_connect(64702)
    # ctrl._get_contry_cookies('US')
    # ctrl._get_contry_cookies('UK')
    # ctrl._get_contry_cookies('US')
    # ctrl._get_contry_cookies('UK')
    # ctrl._read_cookies('US')
    # ctrl._read_cookies('UK')



# ctrl._get_contry_cookies('US')

# task_qi = Queue()
# task_qo = Queue()
# task = threading.Thread(target=controlTask, args=(task_qi, task_qo, ctrl))
# task.setDaemon(True)
# task.start()

# def controlTask(qi=None, qo=None, ctrl=None):
#     logger.debug('controlTask Process is reading...')

#     # API 请求 任务
#     while True:
#         try:
#             msg = qi.get(True)
#             logger.info('controlMain Get msg from queue:{}'.format(msg))
#             msg = json.loads(msg)
#             if msg.get('cmd') == AX_CMD_DCONNECT:
#                 ctrl._devtools_connect(msg.get('devtools_port'))
#             elif msg.get('cmd') == 1:
#                 ctrl._devtools_disconnect()
#         except Exception as e:
#             msg = traceback.format_exc()  # 方式1
#             logger.error("controlMain error...{}{}".format(e, msg))
#             time.sleep(1)

#         r = requests.get('https://api.github.com/user')

#         # 发送任务信息


# def _read_cookies():
#     chrome_option = webdriver.ChromeOptions()
#     # chrome_option.binary_location = "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
#     chrome_option.add_argument("--ignore-certificate-errors")
#     chrome_option.add_argument("--ignore-ssl-errors")
#     # [一行js代码识别Selenium+Webdriver及其应对方案](https://www.cnblogs.com/xieqiankun/p/hide-webdriver.html)
#     chrome_option.add_experimental_option(
#         'excludeSwitches', ['enable-automation'])
#     # chrome_option.add_argument("blink-settings=imagesEnabled=false")
#     # 添加代理
#     # chrome_options.add_argument("--proxy-server=http://" + ip：port)
#     prefs = {
#         # 'profile.default_content_settings': {
#         'profile.default_content_setting_values': {
#             'images': 2,  # 不加载图片
#             'javascript': 2,  # 不加载JS
#         }
#     }
#     chrome_option.add_experimental_option("prefs", prefs)
#     driver = webdriver.Chrome(executable_path=which(
#         'chromedriver'), options=chrome_option)
#     driver.set_page_load_timeout(self.page_load_timeout)

#     while True:
#         try:
#             driver.get("https://www.amazon.com")
#             break
#         except Exception as e:
#             logger.debug(e)
#             pass
#     with open("cookies.txt", "r") as fp:
#         cookies = json.load(fp)
#         # #将每一次遍历的cookie中的这五个键名和键值添加到cookie
#         # driver2.add_cookie({k: cookie[k] for k in {'name', 'value', 'domain', 'path', 'expiry'}})
#         for cookie in cookies:
#             # cookie.pop('domain')  # 如果报domain无效的错误
#             if cookie.get('expiry') is not None:
#                 cookie['expiry'] = int(cookie.get('expiry'))
#             driver.add_cookie(cookie)

#     while True:
#         try:
#             driver.get("https://www.amazon.com")
#             break
#         except Exception as e:
#             logger.debug(e)
#             pass
