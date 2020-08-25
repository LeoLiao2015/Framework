# -*- coding: utf-8 -*-
if __name__ == "__main__":
    import os
    import sys
    import logging
    sys.path.append(os.getcwd())
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
from multiprocessing import Queue
import json
from Common import AX_NAME_UI, AX_NAME_BS, AX_NAME_CTRL, AX_NAME_SCRAPY, AX_NAME_MAIN
from Common import AX_TYPE_UI_TEXT
from Common import AX_TYPE_CTRL_SET_PORT
from Common.msg import send_msg


'''
浏览器
1、执行抓取任务
'''
# 由于scrapy 冲突
# logging.basicConfig(level=logging.INFO,
#                     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
APP_TITLE = u'数据获取工具'
APP_ICON = './resource/icon.png'

# Globals
g_count_windows = 0


def check_versions():
    logger.debug("CEF Python {ver}".format(ver=cef.__version__))
    logger.debug("Python {ver} {arch}".format(
        ver=platform.python_version(), arch=platform.architecture()[0]))
    logger.debug("wxPython {ver}".format(ver=wx.version()))
    # CEF Python version requirement
    assert cef.__version__ >= "66.0", "CEF Python v66.0+ required to run this"


def scale_window_size_for_high_dpi(width, height):
    """Scale window size for high DPI devices. This func can be
    called on all operating systems, but scales only for Windows.
    If scaled value is bigger than the work area on the display
    then it will be reduced."""
    if not WINDOWS:
        return width, height
    (_, _, max_width, max_height) = wx.GetClientDisplayRect().Get()
    # noinspection PyUnresolvedReferences
    (width, height) = cef.DpiAware.Scale((width, height))
    if width > max_width:
        width = max_width
    if height > max_height:
        height = max_height
    return width, height


class MainFrame(wx.Frame):

    def __init__(self):
        self.browser = None

        # Must ignore X11 errors like 'BadWindow' and others by
        # installing X11 error handlers. This must be done after
        # wx was intialized.
        if LINUX:
            cef.WindowUtils.InstallX11ErrorHandlers()

        global g_count_windows
        g_count_windows += 1

        if WINDOWS:
            # noinspection PyUnresolvedReferences, PyArgumentList
            logger.debug("System DPI settings: %s"
                         % str(cef.DpiAware.GetSystemDpi()))
        if hasattr(wx, "GetDisplayPPI"):
            logger.debug("wx.GetDisplayPPI = %s" % wx.GetDisplayPPI())
        logger.debug("wx.GetDisplaySize = %s" % wx.GetDisplaySize())

        logger.debug("MainFrame declared size: %s"
                     % str((WIDTH, HEIGHT)))
        size = scale_window_size_for_high_dpi(WIDTH, HEIGHT)
        logger.debug("MainFrame DPI scaled size: %s" % str(size))

        wx.Frame.__init__(self, parent=None, id=wx.ID_ANY, pos=(-0, -0),
                          title=APP_TITLE, size=size, style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))
        # wx.DEFAULT_FRAME_STYLE
        # wxPython will set a smaller size when it is bigger
        # than desktop size.
        logger.debug("MainFrame actual size: %s" % self.GetSize())

        self.setup_icon()
        self.create_menu()
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        # Set wx.WANTS_CHARS style for the keyboard to work.
        # This style also needs to be set for all parent controls.
        self.browser_panel = wx.Panel(self, style=wx.WANTS_CHARS)
        self.browser_panel.Bind(wx.EVT_SET_FOCUS, self.OnSetFocus)
        self.browser_panel.Bind(wx.EVT_SIZE, self.OnSize)

        if MAC:
            # Make the content view for the window have a layer.
            # This will make all sub-views have layers. This is
            # necessary to ensure correct layer ordering of all
            # child views and their layers. This fixes Window
            # glitchiness during initial loading on Mac (Issue #371).
            NSApp.windows()[0].contentView().setWantsLayer_(True)

        if LINUX:
            # On Linux must show before embedding browser, so that handle
            # is available (Issue #347).
            self.Show()
            # In wxPython 3.0 and wxPython 4.0 on Linux handle is
            # still not yet available, so must delay embedding browser
            # (Issue #349).
            if wx.version().startswith("3.") or wx.version().startswith("4."):
                wx.CallLater(100, self.embed_browser)
            else:
                # This works fine in wxPython 2.8 on Linux
                self.embed_browser()
        else:
            self.embed_browser()
            self.Show()

    def setup_icon(self):
        # icon_file = os.path.join(os.path.abspath(os.path.dirname(__file__)),
        #                          "resources", "wxpython.png")
        # icon_file = "./resource/icon_file.png"
        # wx.IconFromBitmap is not available on Linux in wxPython 3.0/4.0
        # if os.path.exists(icon_file) and hasattr(wx, "IconFromBitmap"):
        #     icon = wx.IconFromBitmap(wx.Bitmap(icon_file, wx.BITMAP_TYPE_PNG))
        #     self.SetIcon(icon)
        icon = wx.Icon(APP_ICON)  # , wx.BITMAP_TYPE_PNG
        self.SetIcon(icon)
        pass

    def create_menu(self):
        # filemenu = wx.Menu()
        # filemenu.Append(1, "Some option")
        # filemenu.Append(2, "Another option")
        menubar = wx.MenuBar()
        # menubar.Append(filemenu, "&File")
        self.SetMenuBar(menubar)
        pass

    def embed_browser(self):
        window_info = cef.WindowInfo()
        (width, height) = self.browser_panel.GetClientSize().Get()
        assert self.browser_panel.GetHandle(), "Window handle not available"
        window_info.SetAsChild(self.browser_panel.GetHandle(),
                               [0, 0, width, height])
        self.browser = cef.CreateBrowserSync(
            window_info, navigateUrl='chrome://flags/')  # , url="http://www.qq.com"
        self.browser.SetClientHandler(FocusHandler())
        # pub.sendMessage("panelListener", url="http://www.baidu.com")

    def OnSetFocus(self, _):
        if not self.browser:
            return
        if WINDOWS:
            cef.WindowUtils.OnSetFocus(self.browser_panel.GetHandle(),
                                       0, 0, 0)
        self.browser.SetFocus(True)

    def OnSize(self, _):
        if not self.browser:
            return
        if WINDOWS:
            cef.WindowUtils.OnSize(self.browser_panel.GetHandle(),
                                   0, 0, 0)
        elif LINUX:
            (x, y) = (0, 0)
            (width, height) = self.browser_panel.GetSize().Get()
            self.browser.SetBounds(x, y, width, height)
        self.browser.NotifyMoveOrResizeStarted()

    def OnClose(self, event):
        logger.debug("MainFrame OnClose called")
        if not self.browser:
            # May already be closing, may be called multiple times on Mac
            return

        if MAC:
            # On Mac things work differently, other steps are required
            self.browser.CloseBrowser()
            self.clear_browser_references()
            self.Destroy()
            global g_count_windows
            g_count_windows -= 1
            if g_count_windows == 0:
                cef.Shutdown()
                wx.GetApp().ExitMainLoop()
                # Call _exit otherwise app exits with code 255 (Issue #162).
                # noinspection PyProtectedMember
                os._exit(0)
        else:
            # Calling browser.CloseBrowser() and/or self.Destroy()
            # in OnClose may cause app crash on some paltforms in
            # some use cases, details in Issue #107.
            self.browser.ParentWindowWillClose()
            event.Skip()
            self.clear_browser_references()
        # wx.Exit()

    def clear_browser_references(self):
        # Clear browser references that you keep anywhere in your
        # code. All references must be cleared for CEF to shutdown cleanly.
        self.browser = None


class FocusHandler(object):
    def OnGotFocus(self, browser, **_):
        # Temporary fix for focus issues on Linux (Issue #284).
        if LINUX:
            logger.debug("FocusHandler.OnGotFocus:"
                         " keyboard focus fix (Issue #284)")
            browser.SetFocus(True)


class CefApp(wx.App):

    def __init__(self, redirect):
        self.timer = None
        self.timer_id = 1
        self.is_initialized = False
        super(CefApp, self).__init__(redirect=redirect)

    def OnPreInit(self):
        super(CefApp, self).OnPreInit()
        # On Mac with wxPython 4.0 the OnInit() event never gets
        # called. Doing wx window creation in OnPreInit() seems to
        # resolve the problem (Issue #350).
        if MAC and wx.version().startswith("4."):
            logger.debug("OnPreInit: initialize here"
                         " (wxPython 4.0 fix)")
            self.initialize()

    def OnInit(self):
        self.initialize()
        return True

    def initialize(self):
        if self.is_initialized:
            return
        self.is_initialized = True
        self.create_timer()

        frame = MainFrame()
        # frame.Enable(False)
        self.SetTopWindow(frame)
        frame.Show()

    def create_timer(self):
        # See also "Making a render loop":
        # http://wiki.wxwidgets.org/Making_a_render_loop
        # Another way would be to use EVT_IDLE in MainFrame.
        self.timer = wx.Timer(self, self.timer_id)
        self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)
        self.timer.Start(10)  # 10ms timer

    def on_timer(self, _):
        cef.MessageLoopWork()

    def OnExit(self):
        self.timer.Stop()
        return 0


def browerMain(q=None):
    send_msg(q, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'BS采集器 启动...'})
    check_versions()
    sys.excepthook = cef.ExceptHook  # To shutdown all CEF processes on error
    commandLineSwitches = {
        "debug": "false",
        "log_severity": "disable",
        # "headless": "",
        # "single-process":"",
        # "disable-access-from-files": "",
        # "disable-tab-to-links": "",
        # "disable-plugins": "",
        # "disable-java": "",
        # "disable-javascript": "",
        "disable-image-loading": "",
        # "user-agent":"",
        "disable-gpu": "",
        "ignore-certificate-errors": "1"}
    if MAC:
        # Issue #442 requires enabling message pump on Mac
        # and calling message loop work in a timer both at
        # the same time. This is an incorrect approach
        # and only a temporary fix.
        commandLineSwitches["external_message_pump"] = ""  # True
    if WINDOWS:
        # noinspection PyUnresolvedReferences, PyArgumentList
        cef.DpiAware.EnableHighDpiSupport()
    cef.Initialize(
        commandLineSwitches=commandLineSwitches
    )
    devtools_port = cef.GetAppSetting("remote_debugging_port")
    logger.debug("remote_debugging_port:{}".format(devtools_port))
    app = CefApp(False)
    send_msg(q, AX_NAME_BS, AX_NAME_CTRL, AX_TYPE_CTRL_SET_PORT, {"devtools_port": devtools_port})
    send_msg(q, AX_NAME_CTRL, AX_NAME_UI, AX_TYPE_UI_TEXT, {"text":'BS采集器 启动完毕'})
    # 界面关闭的时候不退出APP循环
    # app.SetExitOnFrameDelete(False)
    # LastActivityTimeDetector()
    app.MainLoop()
    del app  # Must destroy before calling Shutdown
    if not MAC:
        # On Mac shutdown is called in OnClose
        cef.Shutdown()


def browerMainE(q=None):
    check_versions()
    sys.excepthook = cef.ExceptHook  # To shutdown all CEF processes on error
    commandLineSwitches = {
        "debug": "false",
        "log_severity": "disable",
        # "headless": "",
        # "single-process":"",
        # "disable-access-from-files": "",
        # "disable-tab-to-links": "",
        "disable-plugins": "",
        "disable-java": "",
        "disable-javascript": "",
        "disable-image-loading": "",
        # "user-agent":"",
        "disable-gpu": "",
        "ignore-certificate-errors": "1"}
    if MAC:
        # Issue #442 requires enabling message pump on Mac
        # and calling message loop work in a timer both at
        # the same time. This is an incorrect approach
        # and only a temporary fix.
        commandLineSwitches["external_message_pump"] = ""  # True
    if WINDOWS:
        # noinspection PyUnresolvedReferences, PyArgumentList
        cef.DpiAware.EnableHighDpiSupport()
    cef.Initialize(
        commandLineSwitches=commandLineSwitches
    )
    devtools_port = cef.GetAppSetting("remote_debugging_port")
    logger.debug("remote_debugging_port:{}".format(devtools_port))
    if q is not None:
        send_msg(q, AX_NAME_BS, AX_NAME_CTRL, AX_TYPE_CTRL_SET_PORT, {"devtools_port": devtools_port})

    app = CefApp(False)
    # 界面关闭的时候不退出APP循环
    # app.SetExitOnFrameDelete(False)
    # LastActivityTimeDetector()
    app.MainLoop()
    del app  # Must destroy before calling Shutdown
    if not MAC:
        # On Mac shutdown is called in OnClose
        cef.Shutdown()


# def browerMainV2(q=None):
#     check_versions()
#     sys.excepthook = cef.ExceptHook  # To shutdown all CEF processes on error
#     commandLineSwitches = {
#         "debug": "false",
#         "log_severity": "disable",
#         "headless": "",
#         # "single-process":"",
#         # "disable-access-from-files": "",
#         # "disable-tab-to-links": "",
#         # "disable-plugins": "",
#         # "disable-java": "",
#         # "disable-javascript": "",
#         "disable-image-loading": "",
#         # "user-agent":"",
#         "disable-gpu": "",
#         "ignore-certificate-errors": "1"}
#     if MAC:
#         # Issue #442 requires enabling message pump on Mac
#         # and calling message loop work in a timer both at
#         # the same time. This is an incorrect approach
#         # and only a temporary fix.
#         commandLineSwitches["external_message_pump"] = ""  # True
#     if WINDOWS:
#         # noinspection PyUnresolvedReferences, PyArgumentList
#         cef.DpiAware.EnableHighDpiSupport()
#     cef.Initialize(
#         commandLineSwitches=commandLineSwitches
#     )
#     devtools_port = cef.GetAppSetting("remote_debugging_port")
#     logger.debug("remote_debugging_port:{}".format(devtools_port))
#     if q is not None:
#         q.put('{}'.format(json.dumps({
#             "SRC": AX_NAME_BS,
#             "DST": "",
#             "cmd": 0,

#             "devtools_port": devtools_port
#         })))

#     browser = cef.CreateBrowserSync(url="chrome://flags/",
#                                     window_title="Hello World!")
#     # browser.SetClientCallback("OnLoadEnd", OnLoadEnd)
#     cef.MessageLoop()
#     cef.Shutdown()


if __name__ == "__main__":
    browerMain()
    # browerMainV2()
