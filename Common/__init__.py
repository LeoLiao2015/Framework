'''
MSG 格式
{
    发送源
    "SRC": AX_NAME_BS,
    接收者
    "DST": AX_NAME_SCRAPY,
    消息类型
    "TYPE": AX_TYPE_DCONNECT,
    消息参数
    "PARAMS": {
        "devtools_port": devtools_port
    }
}
'''
AX_NAME_UI = 'UI'
AX_NAME_BS = 'BS'
AX_NAME_CTRL = 'CTRL'
AX_NAME_SCRAPY = 'SCRAPY'
AX_NAME_MAIN = 'MAIN'

AX_TYPE_ALL_PARAMS = 0         # 通用的参数
# PARAMS -> {"key": 'value', "key": 'value', }


AX_TYPE_UI_PARAMS = 10000
AX_TYPE_UI_TOTAL = 10001       # 显示总数
AX_TYPE_UI_COUNT = 10002       # 显示本次采集数量
AX_TYPE_UI_WAIT = 10003        # 显示待采集数量
AX_TYPE_UI_NAME = 10004        # 显示当前任务名称
AX_TYPE_UI_PROGRESS = 10005    # 显示当前任务进度
AX_TYPE_UI_SPEED = 10006       # 显示当前采集速度
AX_TYPE_UI_TEXT = 10007        # 常规信息输出
# PARAMS -> {"text": ''}
AX_TYPE_UI_USERNAME = 10008    # 返回登陆的用户名
AX_TYPE_UI_CAPTCHA = 10010     # 启动验证码界面
# {"img": 'afsasdf'}

AX_TYPE_BS_PARAMS = 20000

AX_TYPE_CTRL_PARAMS = 30000
AX_TYPE_CTRL_SET_PORT = 30001     # 设置远程控制端口
# PARAMS -> {"devtools_port": devtools_port}
AX_TYPE_CTRL_GET_TASK = 30002     # 请求回去任务(驱动事件)
# PARAMS -> None
AX_TYPE_CTRL_BLOCK = 30003     # cookie被block 需要人机验证
# PARAMS -> {"url": "https://..."}
AX_TYPE_CTRL_RETRY_TASK = 30004   #
# PARAMS -> {"item":"US_B07XRGC9F2_37_Automotive_2_309"}
AX_TYPE_CTRL_CLIENT_ID = 30005    # 返回ClientID
AX_TYPE_CTRL_CAPTCHA = 30010      # 用户输入验证码
# {"captcha": 'afsasdf'}
AX_TYPE_SCRAPY_PARAMS = 40000
AX_TYPE_SCRAPY_TASK = 40001       # 抓取的任务描述
# PARAMS -> {"item":"US_B07XRGC9F2_37_Automotive_2_309"}

AX_TYPE_MAIN_PARAMS = 50000
AX_TYPE_MAIN_CREATE = 50001       # 启动进程
# PARAMS -> {"name":""}
AX_TYPE_MAIN_DESTORY = 50002      # 结束进程
# PARAMS -> {"name":""}


# AX_CMD_DCONNECT = 0
# AX_CMD_GET_TASK = 1           # SCRAPY      ->     CTRL      获取新的请求
# AX_CMD_CHANGE_COOKIE = 2      # SCRAPY      ->     CTRL      更新cookie
# AX_CMD_TASK_REQ = 1           # SCRAPY      ->     CTRL      获取新的请求
# AX_CMD_TASK_RES = 2           # SCRAPY      ->     CTRL      获取新的请求

def g_get_homepage_url(contry):
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


def g_get_authority(contry):
    if contry == 'US':
        return 'www.amazon.com'
    elif contry == 'UK':
        return 'www.amazon.co.uk'
    elif contry == 'DE':
        return 'www.amazon.de'
    elif contry == 'FR':
        return 'www.amazon.fr'
    elif contry == 'it':
        return 'www.amazon.it'
    else:
        return 'www.amazon.com'
