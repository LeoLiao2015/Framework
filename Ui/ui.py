# -*- coding: utf-8 -*-
if __name__ == "__main__":
    import os
    import sys
    import logging
    sys.path.append(os.getcwd())
    # 由于scrapy 冲突
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
else:
    import os
    import sys
    import logging
import platform
import time
import wx
from cefpython3 import cefpython as cef
import threading
from pubsub import pub
import traceback
from multiprocessing import Queue
import requests
import urllib
import re
# from io import StringIO
from io import BytesIO
# from Common import AX_TYPE_ALL_PARAMS
# from Common import AX_NAME_UI, AX_NAME_BS, AX_NAME_CTRL, AX_NAME_SCRAPY, AX_NAME_MAIN
# from Common import AX_TYPE_MAIN_CREATE
# from Common import AX_TYPE_UI_TOTAL, AX_TYPE_UI_COUNT, AX_TYPE_UI_WAIT
# from Common import AX_TYPE_UI_NAME, AX_TYPE_UI_PROGRESS, AX_TYPE_UI_SPEED, AX_TYPE_UI_TEXT, AX_TYPE_UI_USERNAME
from Common import *
from Common.msg import send_msg
from Common.global_cfg import GLOBAL_CFG_API_SERVER
from DB.db import LocalDB
'''
用户操作主界面
1、设置启动界面、有/无
2、开启、关闭
3、显示工作进度
'''
logger = logging.getLogger(__name__)


# Platforms
WINDOWS = (platform.system() == "Windows")
LINUX = (platform.system() == "Linux")
MAC = (platform.system() == "Darwin")


if MAC:
    try:
        # noinspection PyUnresolvedReferences
        from AppKit import NSApp
    except ImportError:
        logger.debug("Error: PyObjC package is missing, "
                     "cannot fix Issue #371")
        logger.debug("To install PyObjC type: "
                     "pip install -U pyobjc")
        sys.exit(1)

# Configuration
WIDTH = 1024
HEIGHT = 768
APP_TITLE = u'用户控制器'
APP_ICON = './resource/icon.png'
APP_Login = './resource/header-1.png'
APP_Captcha = './resource/captcha.jpg'

# Globals
g_count_windows = 0


def check_versions():
    logger.debug("CEF Python {ver}".format(ver=cef.__version__))
    logger.debug("Python {ver} {arch}".format(
        ver=platform.python_version(), arch=platform.architecture()[0]))
    logger.info("wxPython {ver}".format(ver=wx.version()))
    # CEF Python version requirement
    assert cef.__version__ >= "66.0", "CEF Python v66.0+ required to run this"

class captchaFrame(wx.Frame):
    def __init__(self, parent, link, qo):
        self.qo = qo
        wx.Frame.__init__(self, parent, -1, title=u'验证码', style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))
        self.SetBackgroundColour(wx.Colour(210, 210, 210))  #int('0xc4', 16), int('0xc4', 16), int('0xc4', 16)
        self.SetSize((400, 260))
        self.Center()
        
        icon = wx.Icon(APP_ICON)  # , wx.BITMAP_TYPE_PNG
        self.SetIcon(icon)    
        
        # Set wx.WANTS_CHARS style for the keyboard to work.
        # This style also needs to be set for all parent controls.
        self.panel = wx.Panel(self, style=wx.WANTS_CHARS)
        # 向panel中添加图片
        data = urllib.request.urlopen(link).read()
        with open(APP_Captcha, 'wb') as f:
            f.write(data)
        image = wx.Image(APP_Captcha).ConvertToBitmap()   #, wx.BITMAP_TYPE_JPEG
        wx.StaticBitmap(self.panel, -1, bitmap=image, pos=(100, 20))

        self.entry_captcha = wx.TextCtrl(self.panel, wx.ID_ANY, pos=(100, 120), size=(200,30))
        #添加按钮
        self.but_ok = wx.Button(self.panel, wx.ID_ANY, u"确 认", pos=(100, 170), size=(200,30))
        #设置按钮的颜色
        self.but_ok.SetBackgroundColour("#1C86EE")
        #给按钮绑定事件
        self.Bind(wx.EVT_BUTTON, self.handler_but_ok, self.but_ok)
        
    def handler_but_ok(self, event):
        #连接到本地数据库
        self.captcha = self.entry_captcha.GetValue()
        logger.info('captcha:{}'.format(self.captcha))
        
        send_msg(self.qo, AX_NAME_UI, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text": 'captcha:{}'.format(self.captcha)})
        send_msg(self.qo, AX_NAME_UI, AX_NAME_CTRL, AX_TYPE_CTRL_CAPTCHA, {"captcha": self.captcha})
        # 关掉自己  发送消息
        self.Show(False)
        self.Close()


class runFrame(wx.Frame):
    def __init__(self, parent):
        self.username = None
        self.MaxLine = 200
        
        wx.Frame.__init__(self, parent, -1, title=u'鹰眼速查', style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))
        self.SetBackgroundColour(wx.Colour(210, 210, 210))  #int('0xc4', 16), int('0xc4', 16), int('0xc4', 16)
        self.SetSize((560, 560))
        self.Center()

        icon = wx.Icon(APP_ICON)  # , wx.BITMAP_TYPE_PNG
        self.SetIcon(icon)    

        # Set wx.WANTS_CHARS style for the keyboard to work.
        # This style also needs to be set for all parent controls.
        self.panel = wx.Panel(self, style=wx.WANTS_CHARS)
        # 向panel中添加图片
        image =wx.Image(APP_Login).ConvertToBitmap()   #, wx.BITMAP_TYPE_JPEG
        wx.StaticBitmap(self.panel, -1, bitmap=image, pos=(0, 0))
        
        #添加静态标签
        x_start = 20
        y_start = 210
        label_width = 100
        label_height = 25
        entry_width = 100
        entry_height = 25
        label_total = wx.StaticText(self.panel, wx.ID_ANY, u"历史采集数量:", pos=(x_start, y_start), size=(label_width, label_height), style=wx.ALIGN_RIGHT)  # 
        label_count = wx.StaticText(self.panel, wx.ID_ANY, u"当前采集数量:", pos=(x_start, y_start + 35), size=(label_width, label_height), style=wx.ALIGN_RIGHT) #, size=wx.Size(30, 30)
        label_wait = wx.StaticText(self.panel, wx.ID_ANY, u"等待采集数量:", pos=(x_start, y_start + 70), size=(label_width, label_height), style=wx.ALIGN_RIGHT) #, size=wx.Size(30, 30)
        label_name = wx.StaticText(self.panel, wx.ID_ANY, u"当前任务名称:", pos=(x_start + 240, y_start), size=(label_width, label_height), style=wx.ALIGN_RIGHT)  # 
        label_progress = wx.StaticText(self.panel, wx.ID_ANY, u"当前任务进度:", pos=(x_start + 240, y_start + 35), size=(label_width, label_height), style=wx.ALIGN_RIGHT) #, size=wx.Size(30, 30)
        label_speed = wx.StaticText(self.panel, wx.ID_ANY, u"当前执行速率:", pos=(x_start + 240, y_start + 70), size=(label_width, label_height), style=wx.ALIGN_RIGHT) #, size=wx.Size(30, 30)
        font=wx.Font(12, wx.DECORATIVE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        label_total.SetFont(font)
        label_count.SetFont(font)
        label_wait.SetFont(font)
        label_name.SetFont(font)
        label_progress.SetFont(font)
        label_speed.SetFont(font)
        
        self.entry_total = wx.TextCtrl(self.panel, wx.ID_ANY, pos=(x_start+x_start+label_width, y_start), size=(60,entry_height), style=wx.TE_READONLY)
        self.entry_count = wx.TextCtrl(self.panel, wx.ID_ANY, pos=(x_start+x_start+label_width, y_start + 35), size=(60,entry_height), style=wx.TE_READONLY)
        self.entry_wait = wx.TextCtrl(self.panel, wx.ID_ANY, pos=(x_start+x_start+label_width, y_start + 70), size=(60,entry_height), style=wx.TE_READONLY)
        self.entry_name = wx.TextCtrl(self.panel, wx.ID_ANY, pos=(x_start+240+x_start+label_width, y_start), size=(140,entry_height), style=wx.TE_READONLY)
        self.entry_progress = wx.TextCtrl(self.panel, wx.ID_ANY, pos=(x_start+240+x_start+label_width, y_start + 35), size=(140,entry_height), style=wx.TE_READONLY)
        self.entry_speed = wx.TextCtrl(self.panel, wx.ID_ANY, pos=(x_start+240+x_start+label_width, y_start + 70), size=(140,entry_height), style=wx.TE_READONLY)
        self.entry_total.SetBackgroundColour(wx.Colour(210, 210, 210))
        self.entry_count.SetBackgroundColour(wx.Colour(210, 210, 210))
        self.entry_wait.SetBackgroundColour(wx.Colour(210, 210, 210))
        self.entry_name.SetBackgroundColour(wx.Colour(210, 210, 210))
        self.entry_progress.SetBackgroundColour(wx.Colour(210, 210, 210))
        self.entry_speed.SetBackgroundColour(wx.Colour(210, 210, 210))
        
        #显示只读文本
        self.text = wx.TextCtrl(self.panel, wx.ID_ANY, pos=(0,280+35), size =(560, 300-35), style = wx.TE_READONLY|wx.TE_MULTILINE)
        self.AppendText('登陆成功')
        self.AppendText('系统初始化...')
         
        # self.SetTotal('10025')
        # self.SetCount('125')
        # self.SetWait('560')
        # self.SetName('afgafg afg a & ew t')
        # self.SetProgress('50')
        # self.SetSpeed('10 / 分钟')
        # self.text.Bind(wx.EVT_TEXT, self.__OnText, self.text)  
        # button = wx.Button(self.panel, wx.ID_ANY, pos = (10, 210), size =(100, 20), label = 'Append')
        # button.Bind(wx.EVT_BUTTON, self.__OnAppendButtonClick)
        # button = wx.Button(self.panel, wx.ID_ANY, pos = (110, 210), size =(60, 20), label = 'Clear')
        # button.Bind(wx.EVT_BUTTON, self.__OnClearClick)

    def AppendText(self, text):
        addLine = len(text.split("\n"))
        lineCount = self.text.GetNumberOfLines()
        # lineLength = self.text.GetLineLength(0)
        if lineCount + addLine > self.MaxLine:
            info = self.text.GetValue()
            if info is not None:
                info_list = info.split('\n')
                index = lineCount + addLine - self.MaxLine
                info = '\n'.join(info_list[index:])
                self.text.SetValue(info)
        self.text.AppendText(time.strftime("[%Y-%m-%d %H:%M:%S] ", time.localtime()) + text + '\n')

    def SetTotal(self, total):
        self.entry_total.SetValue('{}'.format(total))

    def SetCount(self, count):
        self.entry_count.SetValue('{}'.format(count))

    def SetWait(self, count):
        self.entry_wait.SetValue('{}'.format(count))

    def SetName(self, name):
        self.entry_name.SetValue('{}'.format(name))

    def SetProgress(self, progress):
        # 控制进度不能缩小(由于任务可能回溯 导致序号不一定一致)
        value = self.entry_progress.GetValue()
        if value is None:
            self.entry_progress.SetValue('{}%'.format(progress))
        elif len(value) > 0:
            value = re.sub(r'[^0-9]', "", value)
            if int(progress) > int(value):
                self.entry_progress.SetValue('{}%'.format(progress))
        else:
            self.entry_progress.SetValue('')

    def SetSpeed(self, speed):
        self.entry_speed.SetValue('{}'.format(speed))


class loginFrame(wx.Frame):
    def __init__(self, parent, cbk):
        wx.Frame.__init__(self, parent, -1, title=u'用户登陆', style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))
        self.cbk = cbk
        self.SetBackgroundColour(wx.Colour(210, 210, 210))  #int('0xc4', 16), int('0xc4', 16), int('0xc4', 16)
        self.SetSize((560, 360))
        self.Center()

        icon = wx.Icon(APP_ICON)  # , wx.BITMAP_TYPE_PNG
        self.SetIcon(icon)    

        # Set wx.WANTS_CHARS style for the keyboard to work.
        # This style also needs to be set for all parent controls.
        self.panel = wx.Panel(self, style=wx.WANTS_CHARS)
        # 向panel中添加图片
        image =wx.Image(APP_Login).ConvertToBitmap()   #, wx.BITMAP_TYPE_JPEG
        wx.StaticBitmap(self.panel, -1, bitmap=image, pos=(0, 0))

        #添加静态标签
        x_start = 20
        y_start = 220
        label_user = wx.StaticText(self.panel, wx.ID_ANY, u"账号:", pos=(x_start,y_start), size=(60,30), style=wx.ALIGN_CENTER)  # 
        label_pass = wx.StaticText(self.panel, wx.ID_ANY, u"密码:", pos=(x_start,y_start+40), size=(60,30), style=wx.ALIGN_CENTER) #, size=wx.Size(30, 30)
        font=wx.Font(17, wx.DECORATIVE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        label_user.SetFont(font)
        label_pass.SetFont(font)
        #添加文本输入框
        self.entry_user = wx.TextCtrl(self.panel, wx.ID_ANY, pos=(x_start+60,y_start), size=(180,30))
        #style 为设置输入
        self.entry_pass = wx.TextCtrl(self.panel, wx.ID_ANY, pos=(x_start+60,y_start+40), size=(180,30), style=wx.TE_PASSWORD)

        # 记住账户密码
        self.checkbox = wx.CheckBox(self.panel,-1," 记住账户和密码",(340,y_start),(120,30)) 
        self.checkbox.Bind(wx.EVT_CHECKBOX, self.on_remenber, self.checkbox)
        self.remenber = False
        
        #添加按钮
        self.but_login = wx.Button(self.panel, wx.ID_ANY, u"登 陆", pos=(340,250), size=(180,40))
        #设置按钮的颜色
        self.but_login.SetBackgroundColour("#1C86EE")
        #给按钮绑定事件
        self.Bind(wx.EVT_BUTTON, self.on_but_login, self.but_login)
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._OnTimer, self.timer)
        self.timer_count = 0

        # 读取是否有已经保存好的账户信息
        db = LocalDB.instance()
        username, password, remenber = db.load_user()
        if username is not None and len(username) > 0:
            self.entry_user.SetValue(username)
            self.checkbox.SetValue(True)
            self.remenber = True
        if password is not None and len(password) > 0:
            self.entry_pass.SetValue(password)
            self.checkbox.SetValue(True)
            self.remenber = True

    def _OnTimer(self, evt):
        '''定时器函数'''
        self.timer_count += 1
        label = '.'*self.timer_count + '登陆中' + '.'*self.timer_count
        self.but_login.SetLabel(label)
        self.timer_count %= 4
        
    def _LoginDone(self, response):  
        # 复位原始状态
        self.Enable(True)      
        self.timer.Stop()
        self.but_login.SetLabel(u'登 陆')
        
        # 根据登陆状态返回当前信息
        if self.login == 0:
            # 存储cookie信息/token
            cookies = requests.utils.dict_from_cookiejar(response.cookies)
            db = LocalDB.instance()
            db.save_user_cookie(self.username, cookies)
            
            # 登陆成功，创建运行主窗口
            newFrame = runFrame(None)
            newFrame.username = self.username
            # 设置初始状态
            db = LocalDB.instance()
            newFrame.entry_total.SetValue('{}'.format(db.get_total(self.username)))
            newFrame.entry_count.SetValue('0')
            # 设置新的主窗口
            self.cbk(newFrame)
            # 切换显示窗口
            self.Show(False)
            newFrame.Show(True)
            # 关闭登陆窗口
            self.Close()
        elif self.login == 1:
            self.show_message(word='登陆超时！')
        elif self.login == 2:
            self.show_message(word='用户名密码错误，登陆失败！')
        else:
            self.show_message(word='登陆失败！')

    def _LoginLoading(self, username, password):
        '''线程函数'''
        try:
            response = None
            response = requests.request('GET', 
                                        '{}/api/v2.0/user/tlogin?phone={}&password={}'.format(
                                            GLOBAL_CFG_API_SERVER, username, password),
                                        timeout=5)
        except Exception as e:
            self.login = 1
        else:
            if response is None or response.status_code == 200:
                self.login = 0
            else:
                self.login = 2
        wx.CallAfter(self._LoginDone, response)

    def LoginRequest(self, username, password):
        # 设置当前界面不可点击 等待登陆线程退出后才能才做
        self.Enable(False)
        self.login = -1
        self.thread_sw = threading.Thread(target=self._LoginLoading, args=(username, password))
        self.thread_sw.setDaemon(True)
        self.thread_sw.start()
        

    #定义一个消息弹出框的函数
    def show_message(self, word=""):
        dlg = wx.MessageDialog(self, word, u"错误")  #, wx.YES_NO | wx.ICON_QUESTION
        if dlg.ShowModal() == wx.ID_OK: #wxID_OK, wxID_CANCEL, wxID_YES, wxID_NO or wxID_HELP
            pass
        dlg.Destroy()

    def on_remenber(self, event):
        self.remenber = self.checkbox.GetValue()
        
    def on_but_login(self,event):
        #连接到本地数据库
        self.username = self.entry_user.GetValue()
        self.password = self.entry_pass.GetValue()
        # self.username = username
        # self.password = password
        logger.info('user:{} password:{}'.format(self.username, self.password))
        
        if self.username is None or len(self.username) != 11:
            self.show_message(word='账号格式不正确！')
            return
        elif self.password is None or len(self.password) < 6:
            self.show_message(word='密码格式不正确！')
            return
        
        db = LocalDB.instance()
        db.save_user(self.username, self.password, self.remenber)

        # 启动请求线程，带入参数
        self.LoginRequest(self.username, self.password)
        # 启动timer loading动作
        self.timer.Start(200)

class CefApp(wx.App):

    def __init__(self, redirect=False, qi=None, qo=None):
        super(CefApp, self).__init__(redirect=redirect)
        self.qi = qi
        self.qo = qo

        if qi is not None:
            self.task = threading.Thread(target=self.msgWorker, args=(qi, qo,))
            self.task.setDaemon(True)
            self.task.start()

    def OnInit(self):
        self.SetAppName(APP_TITLE)
        self.LoginFrame = loginFrame(None, self.RunMain)
        self.LoginFrame.Show(True)
        self.SetTopWindow(self.LoginFrame)
        self.MainFrame = None
        self.CaptchaFrame = None
        # 测试
        # self.CaptchaFrame = captchaFrame(None, 'https://images-na.ssl-images-amazon.com/captcha/tinytuux/Captcha_llajqucpzq.jpg', None)
        # self.CaptchaFrame.Show(True)
        return True

    def RunMain(self, frame):
        self.MainFrame = frame
        self.SetTopWindow(self.MainFrame)
            
        # 发送消息，启动CTRL
        if self.qo is not None:
            send_msg(self.qo, AX_NAME_UI, AX_NAME_MAIN, AX_TYPE_MAIN_CREATE, {"name": AX_NAME_CTRL})
            # self.qo.put({
            #     "SRC": AX_NAME_UI,
            #     "DST": AX_NAME_MAIN,
            #     "TYPE": AX_TYPE_MAIN_CREATE,
            #     "PARAMS":{
            #         "name": AX_NAME_CTRL
            #     }
            # })


    def do_msg(self, msg):
        if msg is None:
            return
        if isinstance(msg, dict) != True:
            logger.info("msg type:{} is not dict error".format(type(msg)))
            return
        if self.MainFrame is None:
            return

        params = msg.get('PARAMS')
        if msg.get('TYPE') == AX_TYPE_UI_TOTAL:
            if params is not None:
                self.MainFrame.SetTotal(params.get('text'))
        elif msg.get('TYPE') == AX_TYPE_UI_COUNT:
            if params is not None:
                self.MainFrame.SetCount(params.get('text'))
        elif msg.get('TYPE') == AX_TYPE_UI_WAIT:
            if params is not None:
                self.MainFrame.SetWait(params.get('text'))
        elif msg.get('TYPE') == AX_TYPE_UI_NAME:
            if params is not None:
                self.MainFrame.SetName(params.get('text'))
        elif msg.get('TYPE') == AX_TYPE_UI_PROGRESS:
            if params is not None:
                self.MainFrame.SetProgress(params.get('text'))
        elif msg.get('TYPE') == AX_TYPE_UI_SPEED:
            if params is not None:
                self.MainFrame.SetSpeed(params.get('text'))
        elif msg.get('TYPE') == AX_TYPE_UI_TEXT:
            if params is not None:
                self.MainFrame.AppendText(params.get('text'))
        elif msg.get('TYPE') == AX_TYPE_UI_USERNAME:
            send_msg(self.qo, AX_NAME_UI, msg.get('SRC'), AX_TYPE_ALL_PARAMS, {"phone": self.MainFrame.username})
        elif msg.get('TYPE') == AX_TYPE_UI_CAPTCHA:
            # 新建一个等待用户输入的界面
            wx.CallAfter(self.captcha, params.get("img"))
              
    def captcha(self, link):
        self.CaptchaFrame = captchaFrame(self.MainFrame, link, self.qo)
        self.CaptchaFrame.Show(True)

    def msgWorker(self, qi, qo):
        '''
        接收其他消息，响应相关UI动作
        '''
        logger.debug('uiMain Process is reading...')
        while True:
            try:
                msg = qi.get(True)
                logger.info('UI Get msg:{} from queue'.format(msg))
                self.do_msg(msg)
            except Exception as e:
                logger.info("worker error...", e)
                msg = traceback.format_exc()  # 方式1
                logger.info(msg)


def uiMain(qi=None, qo=None):
    check_versions()
    app = CefApp(False, qi, qo)
    app.MainLoop()
    del app  # Must destroy before calling Shutdown


if __name__ == "__main__":
    # 启动登陆界面
    # 登陆成功以后将登陆的cookie存储下来备用
    # 转入到运行界面，展示运行的状态变化
    uiMain()





# class mainFrame(wx.Frame):
#     '''程序主窗口类，继承自wx.Frame'''

#     def __init__(self, parent):
#         '''构造函数'''

#         wx.Frame.__init__(self, parent, -1, APP_TITLE)
#         self.SetBackgroundColour(wx.Colour(224, 224, 224))
#         self.SetSize((320, 300))
#         self.Center()

#         icon = wx.Icon(APP_ICON)  # , wx.BITMAP_TYPE_PNG
#         self.SetIcon(icon)

#         # font = wx.Font(24, wx.DECORATIVE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, 'Comic Sans MS')
#         font = wx.Font(30, wx.DECORATIVE, wx.FONTSTYLE_NORMAL,
#                        wx.FONTWEIGHT_NORMAL, False, 'Monaco')

#         self.clock = wx.StaticText(self, -1, u'08:00:00', pos=(50, 50),
#                                    size=(200, 50), style=wx.TE_CENTER | wx.SUNKEN_BORDER)
#         self.clock.SetForegroundColour(wx.Colour(0, 224, 32))
#         self.clock.SetBackgroundColour(wx.Colour(0, 0, 0))
#         self.clock.SetFont(font)

#         self.stopwatch = wx.StaticText(
#             self, -1, u'0:00:00.0', pos=(50, 150), size=(200, 50), style=wx.TE_CENTER | wx.SUNKEN_BORDER)
#         self.stopwatch.SetForegroundColour(wx.Colour(0, 224, 32))
#         self.stopwatch.SetBackgroundColour(wx.Colour(0, 0, 0))
#         self.stopwatch.SetFont(font)

#         self.timer = wx.Timer(self)
#         self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
#         self.timer.Start(50)

#         self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

#         self.sec_last = None
#         self.is_start = False
#         self.t_start = None

#         thread_sw = threading.Thread(target=self.StopWatchThread)
#         thread_sw.setDaemon(True)
#         thread_sw.start()

#     def OnTimer(self, evt):
#         '''定时器函数'''

#         t = time.localtime()
#         if t.tm_sec != self.sec_last:
#             self.clock.SetLabel('%02d:%02d:%02d' %
#                                 (t.tm_hour, t.tm_min, t.tm_sec))
#             self.sec_last = t.tm_sec

#     def OnKeyDown(self, evt):
#         '''键盘事件函数'''

#         if evt.GetKeyCode() == wx.WXK_SPACE:
#             self.is_start = not self.is_start
#             self.t_start = time.time()
#         elif evt.GetKeyCode() == wx.WXK_ESCAPE:
#             self.is_start = False
#             self.stopwatch.SetLabel('0:00:00.0')

#     def StopWatchThread(self):
#         '''线程函数'''

#         while True:
#             if self.is_start:
#                 n = int(10*(time.time() - self.t_start))
#                 deci = n % 10
#                 ss = int(n/10) % 60
#                 mm = int(n/600) % 60
#                 hh = int(n/36000)
#                 wx.CallAfter(self.stopwatch.SetLabel,
#                              '%d:%02d:%02d.%d' % (hh, mm, ss, deci))
#             time.sleep(0.02)


