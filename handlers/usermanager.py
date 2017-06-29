#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import os
import traceback

import tornado.web
import sys
from handlers.base import BaseHandler
from utils.config import config, db
from utils.misc import original_time, next_uuid, img_create, now

sys.path.append('../')

pre_system = config.pre_system

#
# class ManagerHandler(BaseHandler):
#     @tornado.web.authenticated
#     def get(self, *args, **kwargs):
#         cookie_username = self.get_secure_cookie(pre_system + 'username')
#         cookie_groupid = int(self.get_secure_cookie(pre_system + 'groupid'), 2)
#         if config.debug:
#             logging.debug('/search get: cookie_username: ' + cookie_username)
#         if cookie_groupid == 0:
#             sql = '''
#                         select username,create_time,lastlogin_time,login_ip,group_id
#                         from system_admin_user;
#                         '''
#             # sql = '''
#             # select username,create_time,lastlogin_time,login_ip,group_id
#             # from system_admin_user limit 0,20;
#             # '''用户多了可能需要分页,基本用不上
#             ret = mysql_cursor.query(sql)
#             print ret
#             if ret:
#                 self.finish('dd')
#                 # self.render('AccountManagement.html', ret=ret)#指向用户管理页面,显示所有用户信息
#         else:
#             self.write('<script language="javascript">alert("非管理员帐号,禁止进入");history.go(-1)</script>')
#
#


class AdminHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self, *args, **kwargs):
        self.add_header('Cache-Control', 'no-cache')
        current_user = self.get_secure_cookie(pre_system + 'username')
        if not current_user:
            self.redirect('/search')
        elif current_user and current_user != 'root':
            logging.error('not root')
            self.redirect('/login')
            return

        sql = 'SELECT `avatar` FROM `system_admin_user` WHERE `username` = %s'
        rs = db.query(sql, current_user)[0]['avatar']
        logging.info(rs)
        if rs.strip():
            filename = rs
        else:
            filename = next_uuid()
        logging.info(filename)
        filename_url = 'static/img/avatar/{0}.png'.format(filename)
        if not os.path.exists(filename_url):
            if img_create(filename):
                sql = '''
                    UPDATE `subdomain`.`system_admin_user` SET `avatar`=%s WHERE username=%s;
                '''
                rs = db.execute(sql, filename, current_user)
                if rs:
                    pass
            else:
                filename = 'icon'

        users = db.query('''
            SELECT
                `id`, `username`, `create_time`, `lastlogin_time`, `login_ip`, `comment`
            FROM
                `system_admin_user`
            WHERE
                `group_id` = 2
        ''')

        self.render('user_manage.html', avatar=filename, username=current_user, users=users)


class UserAdd(BaseHandler):

    @tornado.web.authenticated
    def post(self, *args, **kwargs):
        result_json = {'success': 0}

        current_user = self.get_secure_cookie(pre_system + 'username')
        if current_user != 'root':
            logging.error('not root')
            self.finish(result_json)
            return

        username = self.get_argument('username', None)
        password = self.get_argument('password', None)
        comment = self.get_argument('comment', '')
        group_id = 2

        if not(username and password):
            self.finish(result_json)
            return

        sql = '''
            INSERT INTO 
                `system_admin_user` (`group_id`, `username`, `password`, `create_time`, `lastlogin_time`, `comment`)
            VALUES
                (%s, %s, md5(%s), %s, %s, %s);
        '''
        try:
            current_time = now()
            last_login_time = original_time()
            effected_row = db.update(sql, group_id, username, password, current_time, last_login_time, comment)
            result_json['success'] = 1
            user_data = db.query('SELECT `id`, `group_id`, `username`, `create_time`, `lastlogin_time`, `login_ip`, `comment` FROM `system_admin_user` WHERE `username` = %s', username)[0]
            user_data['create_time'] = user_data['create_time'].strftime('%Y-%m-%d %H:%M:%S')
            user_data['lastlogin_time'] = user_data['lastlogin_time'].strftime('%Y-%m-%d %H:%M:%S')
            result_json['data'] = user_data
        except Exception as e:
            logging.error(traceback.format_exc())
            logging.error(e.message)

        self.write(result_json)


class DeleteUserHandler(BaseHandler):

    @tornado.web.authenticated
    def post(self, *args, **kwargs):
        result_json = {'success': 0}

        current_user = self.get_secure_cookie(pre_system + 'username')
        if current_user != 'root':
            logging.error('not root')
            self.finish(result_json)
            return

        username = self.get_argument('username', None)
        logging.info(username)
        try:
            if username is not None:
                db.update('DELETE FROM `system_admin_user` WHERE `username` = %s', username)
                result_json['success'] = 1
        except Exception as e:
            logging.error(traceback.format_exc())
            logging.error(e)

        self.write(result_json)


class ModifyPasswordAdminHandler(BaseHandler):

    @tornado.web.authenticated
    def post(self, *args, **kwargs):
        result_json = {'success': 0}

        current_user = self.get_secure_cookie(pre_system + 'username')
        if current_user != 'root':
            logging.error('not root')
            self.finish(result_json)
            return

        username = self.get_argument('username', None)
        password = self.get_argument('password', None)

        try:
            if username and password:
                effected_row = db.update('''
                    UPDATE
                        `system_admin_user`
                    SET
                        `password` = MD5(%s)
                    WHERE
                        `username` = %s
                ''', password, username)
                result_json['success'] = 1
        except Exception as e:
            logging.error(traceback.format_exc())
            logging.error(e)

        self.write(result_json)
