import sqlite3
import logging
import json
import traceback
import threading
import time
from Common.aes import PrpCrypt
# from ..main import NAME_UI, NAME_BS, NAME_CTRL, NAME_SCRAPY, NAME_MAIN

'''
本地DB
'''
# 由于scrapy 冲突
# logging.basicConfig(level=logging.INFO,
#                     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LocalDB(object):
    _instance_lock = threading.Lock()

    @classmethod
    def instance(cls, *args, **kwargs):
        if not hasattr(LocalDB, "_instance"):
            with LocalDB._instance_lock:
                if not hasattr(LocalDB, "_instance"):
                    LocalDB._instance = LocalDB(
                        *args, **kwargs)
        return LocalDB._instance

    # 检查本地数据库是否创建，
    # 表是否准备就绪
    # 建表
    def __init__(self, *args, **kwargs):
        logger.debug("Opened database")
        path = kwargs.get("path")
        if path is not None:
            self.dbname = path + 'test.db'
        else:
            self.dbname = 'test.db'
        conn = sqlite3.connect(self.dbname)

        c = conn.cursor()
        c.execute('''SELECT name FROM sqlite_master WHERE type = 'trigger';''')
        detail = c.fetchall()

        self._create_user(conn)
        self._create_product_detail(conn)
        self._create_contry_cookie(conn)
        conn.close()
        self.pc = PrpCrypt('fdv' + 'h'*2 + 'reg'+'@' + '%' +
                           '=' + '!' + '-'.join(['H', '&1']))    # 初始化密钥

    def _create_product_detail(self, conn):
        try:
            c = conn.cursor()
            # c.execute('drop table `product_detail`')   # 测试用
            c.execute('''create table `product_detail`
                        (
                            `asin` char(10) not null default "",
                            `data` text,
                            primary key (`asin`)
                        );''')
            conn.commit()
        except Exception as e:
            msg = traceback.format_exc()  # 方式1
            if msg.find('already exists') == -1:
                logger.info(msg)
        c.close()

    def _create_user(self, conn):
        try:
            c = conn.cursor()
            # c.execute('drop table `user`')   # 测试用
            # c.execute('DROP TRIGGER user_update')   # 测试用
            c.execute('''create table `user`
                        (
                            `phone` char(16) not null default "",
                            `password` varchar(64) not null default "",
                            `cookie` varchar(2048) not null default "",
                            `remenber` int not null default 0,
                            `total` int not null default 0,
                            `date` TIMESTAMP NOT NULL DEFAULT (datetime('now','localtime')),
                            primary key (`phone`)
                        );''')  # ON UPDATE CURRENT_TIMESTAMP

            c.execute('''CREATE TRIGGER user_update AFTER UPDATE 
                        ON `user` FOR EACH ROW 
                        BEGIN
                            UPDATE `user` set date=datetime('now','localtime') where phone=new.phone;
                        END;''')
            conn.commit()
        except Exception as e:
            msg = traceback.format_exc()  # 方式1
            if msg.find('already exists') == -1:
                logger.info(msg)
        c.close()

    def _create_contry_cookie(self, conn):
        try:
            c = conn.cursor()
            c.execute('''create table `contry_cookie`
                        (
                            `contry` char(2) not null default "",
                            `cookie` varchar(2048) not null default "",
                            primary key (`contry`)
                        );''')
            conn.commit()
        except:
            msg = traceback.format_exc()  # 方式1
            if msg.find('already exists') == -1:
                logger.info(msg)
        c.close()

    def save_user(self, phone, password, remenber=False):
        password = self.pc.encrypt(password)  # 加密
        remenber = 1 if remenber == True else 0
        #     c.execute(
        #         '''INSERT into `user` (phone, password, remenber) values ({}, "{}", {})
        #         ON CONFLICT(phone) DO UPDATE SET password="{}", remenber={};'''.format(
        #             phone, password, remenber, password, remenber))
        conn = sqlite3.connect(self.dbname)
        try:
            c = conn.cursor()
            c.execute(
                '''select phone from `user` where phone={}'''.format(phone))
        except:
            msg = traceback.format_exc()  # 方式1
            logger.info(msg)
            c.close()
            conn.close()
            return

        detail = c.fetchall()
        if detail is not None and len(detail) > 0:
            sql = '''UPDATE `user` set password="{}", remenber={} WHERE phone={}'''.format(
                password, remenber, phone)
        else:
            sql = '''replace into `user` (phone, password, remenber) values ({}, "{}", {})'''.format(
                phone, password, remenber)
        try:
            c.execute(sql)
            conn.commit()
        except:
            msg = traceback.format_exc()  # 方式1
            logger.info(msg)
        c.close()
        conn.close()

    def load_user(self):
        detail = None
        conn = sqlite3.connect(self.dbname)
        try:
            c = conn.cursor()
            c.execute(
                '''select phone, password, remenber, date from `user` order by date DESC''')
            detail = c.fetchall()
        except:
            msg = traceback.format_exc()  # 方式1
            logger.info(msg)
        c.close()
        conn.close()

        if detail is not None and len(detail) > 0:
            if detail[0][2] == 1:
                password = self.pc.decrypt(detail[0][1])  # 解密
                return detail[0][0], password, detail[0][2]
            else:
                return None, None, None
        else:
            return None, None, None

    def get_total(self, phone):
        detail = None
        conn = sqlite3.connect(self.dbname)
        try:
            c = conn.cursor()
            c.execute(
                '''select total from `user` where phone={}'''.format(phone))
            detail = c.fetchall()
        except:
            msg = traceback.format_exc()  # 方式1
            logger.info(msg)
        c.close()
        conn.close()

        if detail is not None and len(detail) > 0:
            return detail[0][0]
        else:
            return 0

    def set_total_up(self, phone, total=1):
        conn = sqlite3.connect(self.dbname)
        try:
            c = conn.cursor()
            c.execute(
                '''UPDATE `user` SET total=total+{} WHERE phone={}'''.format(total, phone))
            conn.commit()
        except:
            msg = traceback.format_exc()  # 方式1
            logger.info(msg)
        c.close()
        conn.close()

    def save_user_cookie(self, phone, cookie):
        conn = sqlite3.connect(self.dbname)
        try:
            c = conn.cursor()
            if isinstance(cookie, dict):
                cookie = self.pc.encrypt(json.dumps(cookie))  # 加密
                c.execute(
                    '''update `user` set cookie='{}' where phone={}'''.format(cookie, phone))
            else:
                cookie = self.pc.encrypt(cookie)  # 加密
                c.execute(
                    '''update `user` set cookie='{}' where phone={}'''.format(cookie, phone))
            conn.commit()
        except:
            msg = traceback.format_exc()  # 方式1
            logger.info(msg)
        c.close()
        conn.close()

    def load_user_cookie(self, phone=None):
        detail = None
        conn = sqlite3.connect(self.dbname)
        try:
            c = conn.cursor()
            if phone is not None and len(phone) > 0:
                c.execute(
                    '''select cookie from `user` where phone={}'''.format(phone))
            else:
                c.execute(
                    '''select cookie from `user`''')
            detail = c.fetchall()
        except:
            msg = traceback.format_exc()  # 方式1
            logger.info(msg)
        c.close()
        conn.close()

        if detail is not None and len(detail) > 0:
            try:
                cookie = self.pc.decrypt(detail[0][0])  # 解密
                try:
                    return json.loads(cookie)
                except:
                    return cookie
            except:
                return None
        else:
            return None

    def save_contry_cookie(self, contry, cookie):
        conn = sqlite3.connect(self.dbname)
        try:
            c = conn.cursor()
            if isinstance(cookie, dict) or isinstance(cookie, list):
                c.execute(
                    '''replace into `contry_cookie` (contry, cookie) values ('{}', '{}')'''.format(contry, json.dumps(cookie)))
            else:
                c.execute(
                    '''replace into `contry_cookie` (contry, cookie) values ('{}', '{}')'''.format(cookie, contry))
            conn.commit()
        except:
            msg = traceback.format_exc()  # 方式1
            logger.info(msg)
        c.close()
        conn.close()

    def update_contry_cookie(self, contry, cookie):
        return None
        # cookies = self.load_contry_cookie(contry)
        # for item in cookie:
        #     name = item.get('name')

        # conn = sqlite3.connect(self.dbname)
        # try:
        #     c = conn.cursor()
        #     if isinstance(cookie, dict):
        #         c.execute(
        #             '''replace into `contry_cookie` (contry, cookie) values ('{}', '{}')'''.format(contry, json.dumps(cookie)))
        #     else:
        #         c.execute(
        #             '''replace into `contry_cookie` (contry, cookie) values ('{}', '{}')'''.format(cookie, contry))
        #     conn.commit()
        # except:
        #     msg = traceback.format_exc()  # 方式1
        #     logger.info(msg)
        # conn.close()

    def load_contry_cookie(self, contry):
        detail = None
        conn = sqlite3.connect(self.dbname)
        try:
            c = conn.cursor()
            c.execute(
                '''select cookie from `contry_cookie` where contry='{}' '''.format(contry))
            detail = c.fetchall()
        except:
            msg = traceback.format_exc()  # 方式1
            logger.info(msg)
        c.close()
        conn.close()

        if detail is not None and len(detail) > 0:
            try:
                return json.loads(detail[0][0])
            except:
                return None
        else:
            return None

    def detail_append(self, item):  # , asin=None
        conn = sqlite3.connect(self.dbname)
        try:
            c = conn.cursor()
            if isinstance(item, dict):  # or isinstance(item, list)
                data = self.pc.encrypt(json.dumps(item))  # 加密
                c.execute(
                    '''replace into `product_detail` (asin, data) values ('{}', '{}')'''.format(
                        item.get("asin"), data))
            # elif asin is not None:
            #     data = self.pc.encrypt(json.dumps(item))  # 加密
            #     c.execute(
            #         '''replace into `product_detail` (asin, data) values ('{}', '{}')'''.format(
            #             asin, data))
            conn.commit()
        except:
            msg = traceback.format_exc()  # 方式1
            logger.info(msg)
        c.close()
        conn.close()

    def detail_clear(self):
        conn = sqlite3.connect(self.dbname)
        try:
            c = conn.cursor()
            # c.execute('''tuncate table `product_detail`''')
            c.execute('''DELETE FROM `product_detail`''')
            conn.commit()
        except:
            msg = traceback.format_exc()  # 方式1
            logger.info(msg)
        c.close()
        conn.close()

    def detail_load(self, timeout=36000):
        detail = None
        conn = sqlite3.connect(self.dbname)
        try:
            c = conn.cursor()
            c.execute(
                '''select asin, data from `product_detail`''')
            detail = c.fetchall()
        except:
            msg = traceback.format_exc()  # 方式1
            logger.info(msg)
        c.close()
        conn.close()

        task_list = []
        if detail is not None and len(detail) > 0:
            for item in detail:
                try:
                    tmp = self.pc.decrypt(item[1])  # 解密
                    data = json.loads(tmp)
                    task_now = data.get("task_now")
                    if task_now is not None and time.time() - task_now < timeout:
                        task_list.append()
                except:
                    pass
            return task_list
        else:
            return task_list
