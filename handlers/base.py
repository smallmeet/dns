#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import re
import tornado.web
from tornado.websocket import WebSocketHandler

sys.path.append('../')
from utils import config

redis_cursor = config.redis_cursor
pre_system = config.pre_system


class BaseHandler(tornado.web.RequestHandler):
    '''
        重写get_current_user
    '''

    def data_received(self, chunk):
        pass

    def get_current_user(self):
        if re.findall(r'sqlmap', self.request.headers['User-Agent']):
            self.write('Attack')
        else:
            username = self.get_secure_cookie(pre_system + 'username')
            sessionid_cookie = self.get_secure_cookie(pre_system + 'sessionid')

            sessionid_save = redis_cursor.hget(config.project_name + '__' + pre_system + 'online', username)
            if sessionid_cookie and username:
                if sessionid_cookie == sessionid_save:
                    # if self.get_secure_cookie(pre_system + 'groupid') not in ['0']:#超管不能登陆
                    return username
            self.clear_cookie(pre_system + 'username')
            self.clear_cookie(pre_system + 'userid')
            self.clear_cookie(pre_system + 'groupid')
            self.clear_cookie(pre_system + 'sessionid')
            return ''

    def write_error(self, status_code, **kwargs):
        # if status_code == 404:
        #     self.render('templates/error/404.html')
        # elif status_code == 403:
        #     self.render('templates/error/403.html')
        # elif status_code == 500:
        #     self.render('templates/error/500.html')
        # elif status_code == 400:
        #     self.render('templates/error/500.html')
        # else:
        #     self.render('templates/error/500.html')
        # super(BaseHandler, self).write_error(status_code, **kwargs)
        pass

    @property
    def db(self):
        return self.application.db



class BaseWebSocketHandler(WebSocketHandler):

    def data_received(self, chunk):
        pass

    def on_message(self, message):
        raise NotImplemented

    @property
    def db(self):
        return self.application.db
