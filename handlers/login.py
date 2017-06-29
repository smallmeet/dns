#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import logging
import os
from handlers.base import BaseHandler
import time
import sys
import redis
import torndb
import hashlib
import datetime
import json

from utils.misc import md5

sys.path.append('../')
from utils import config

pre_system = config.pre_system
mysql_cursor = config.db
redis_cursor = config.redis_cursor


class LoginHandler(BaseHandler):
    '''
    登陆
    '''

    def get(self):
        cookie_username = self.get_secure_cookie(pre_system + 'username')
        if cookie_username:
            # self.render('login.html')
            self.redirect('/search_new')
        else:
            self.render('login.html')

    def post(self):
        # print 'post成功'
        '''
                0:服务器异常
                1:成功
                2:用户名或密码错
                3:空
        '''
        username = self.get_argument('username', '')
        password = self.get_argument('password', '')
        log_status = self.get_argument("log_status", 'false')
        remote_ip = self.request.remote_ip
        logging.debug('-' * 35)
        logging.debug(username)
        logging.debug(password)
        logging.debug(log_status)
        logging.debug('-' * 35)
        if username and password:
            psw = hashlib.md5(password).hexdigest()
            sql = '''
                select
                    id, group_id
                from
                    system_admin_user
                where
                    `username`=%s and `password`=%s'''
            ret = mysql_cursor.query(sql, username, psw)
            if ret:
                userid = ret[0]['id']
                groupid = ret[0]['group_id']
                # 制作sessionid, 并保存到redis
                mcode = hashlib.md5(self.request.headers['User-Agent'] + 'one').hexdigest()
                redis_cursor.hset(config.project_name + '__' + pre_system + 'online', username, mcode)
                try:
                    # 更新最后登录时间
                    dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    sql = 'update system_admin_user set lastlogin_time=%s,login_ip=%s where id=%s'
                    mysql_cursor.execute(sql, dt, remote_ip, userid, )
                    if log_status != 'false':
                        expires = 1
                    else:
                        expires = None
                    self.set_secure_cookie(pre_system + 'sessionid', mcode, expires_days=expires)
                    self.set_secure_cookie(pre_system + 'username', username, expires_days=expires)
                    self.set_secure_cookie(pre_system + 'userid', str(userid), expires_days=expires)
                    self.set_secure_cookie(pre_system + 'groupid', str(groupid), expires_days=expires)

                    self.finish(json.dumps({'code': '1'}))
                except Exception as e:
                    logging.error(e)
                    self.finish(json.dumps({'code': '0'}))
            else:
                # self.write('<script language="javascript">alert("用户名或密码错误！");history.go(-1)</script>')
                self.finish(json.dumps({'code': '2'}))
            return

        else:  # self.write('<script language="javascript">alert("用户名或密码为空！");history.go(-1)</script>')
            self.finish(json.dumps({'code': '3'}))


class LogoutHandler(BaseHandler):
    '''
        退出模块
    '''

    def post(self):
        self.get()

    # @tornado.web.authenticated
    def get(self):
        try:
            username = self.get_secure_cookie(pre_system + 'username')
            redis_cursor.hdel(pre_system + 'autovote_online', username)

            self.clear_cookie(pre_system + 'username')
            self.clear_cookie(pre_system + 'userid')
            self.clear_cookie(pre_system + 'groupid')
            self.clear_cookie(pre_system + 'sessionid')
            self.redirect('/login')
        except Exception as e:
            print e


class ModifyPasswordHandler(BaseHandler):

    def post(self, *args, **kwargs):
        old_pwd = self.get_argument('old_pwd', '')
        new_pwd = self.get_argument('new_pwd', '')

        result_json = {'success': 0}

        username = self.get_secure_cookie(pre_system + 'username')

        rs = mysql_cursor.query('SELECT `username` FROM `system_admin_user` WHERE `username` = %s AND `password` = MD5(%s)', username, old_pwd)
        if len(rs) == 0:
            self.finish(result_json)
            return

        try:
            mysql_cursor.update('''
                UPDATE
                    `system_admin_user`
                SET
                    `password` = MD5(%s)
                WHERE
                    `username` = %s
                    AND `password` = MD5(%s)
            ''', new_pwd, username, old_pwd)
            result_json['success'] = 1
        except Exception as e:
            logging.error(e)

        self.write(result_json)
