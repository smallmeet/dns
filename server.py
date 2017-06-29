#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import sys
import threading

import time
import tornado.web
import tornado.ioloop
import tornado.autoreload
from sqlalchemy import create_engine
from sqlalchemy.event import listens_for
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import Pool
from tornado.httpserver import HTTPServer
from tornado.options import define

from handlers.interfaces import GetHttpHeaderHandler, PortBannerHandler, DetectDomainHandler,PortScanEventHandler
from handlers.login import LoginHandler, LogoutHandler, ModifyPasswordHandler
from handlers.result import ResultHandler, ResultWebSocketHandler, AddBruteTaskHandler, BruteProgressHandler, \
    ResultAsyncHandler, ResultWebSocketRealHandler, IpReverseWebSocketHandler
from handlers.result import WhoisHandler
from handlers.result_new import ResultNewHandler, ReverseIpLookUpNewHandler, ChartHandler
from handlers.reverse_ip_lookup import ReverseIpLookupHandler, ReverseIpLookupAsyncHandler
from handlers.search import SearchHandler, SearchNewHandler
from handlers.usermanager import UserAdd, DeleteUserHandler, ModifyPasswordAdminHandler, AdminHandler
from utils.config import config

reload(sys)
sys.setdefaultencoding('utf-8')

logging.basicConfig(level=logging.DEBUG,
                format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S')

db_path = 'mysql://{}:{}@{}/{}?charset={}'.format(
    config.mysql_user,
    config.mysql_pwd,
    config.mysql_host,
    config.mysql_db,
    config.mysql_charset,
)


class MainHandler(tornado.web.RequestHandler):

    def get(self):
        logging.debug(self.request.remote_ip)
        self.redirect('/login')


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/', MainHandler),
            (r'/login', LoginHandler),
            (r'/logout', LogoutHandler),
            (r'/modify_password', ModifyPasswordHandler),
            (r'/search', SearchHandler),
            (r'/result', ResultHandler),
            (r'/result_async', ResultAsyncHandler),
            (r'/result_ws', ResultWebSocketHandler),
            (r'/result_ws_test', ResultWebSocketRealHandler),
            (r'/get_http_header', GetHttpHeaderHandler),
            (r'/get_whois', WhoisHandler),
            # (r'/get_ip_info', IpLookupHandler),
            (r'/get_banner', PortBannerHandler),
            (r'/port/scan/event', PortScanEventHandler),
            (r'/add_brute_task', AddBruteTaskHandler),
            (r'/brute_progress', BruteProgressHandler),
            (r'/get_banner', PortBannerHandler),
            # (r'/manage', ManagerHandler),
            (r'/admin', AdminHandler),
            (r'/admin_user_add', UserAdd),
            (r'/admin_user_delete', DeleteUserHandler),
            (r'/admin_user_modify_pwd', ModifyPasswordAdminHandler),
            (r'/reverse_ip_lookup', ReverseIpLookupHandler),
            (r'/reverse_ip_result_async', ReverseIpLookupAsyncHandler),
            (r'/detect_domain', DetectDomainHandler),
            (r'/search_new', SearchNewHandler),
            (r'/result_new', ResultNewHandler),
            (r'/reverse_ip_result_ws', IpReverseWebSocketHandler),
            (r'/reverse_ip_lookup_new', ReverseIpLookUpNewHandler),
            (r'/chart', ChartHandler),
        ]
        settings = dict(
            debug=config.debug,
            static_path=os.path.join(os.path.dirname(__file__), 'static'),
            template_path=os.path.join(os.path.dirname(__file__), 'templates'),
            # xsrf_cookies=True,
            cookie_secret="75d68d56257111e78b3e1c1b0d16a734",
            login_url='/login'
        )
        tornado.web.Application.__init__(self, handlers, **settings)
        self.init_db()

    def init_db(self):
        self.engine = create_engine(db_path, convert_unicode=True)
        self.db = scoped_session(sessionmaker(bind=self.engine))


application = Application()
define('app', default=application)


@listens_for(Pool, 'checkout')
def when_connected(dbapi_connection, connection_record, connection_proxy):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute('SELECT 1')
    except:
        logging.info('DBConnection挂了, 重启.')
        application.init_db()


def detect_db_health():
    if threading.current_thread().getName() == 'MainThread':
        raise RuntimeError('不能在主线程启动')

    while True:
        logging.info('检测 DBConnection.')
        try:
            application.db.execute('SELECT 1')
            logging.info('DBConnection 正常.')
        except:
            logging.info('DBConnection 挂了, 重启.')
            application.init_db()
        time.sleep(600)
    pass


# settings = {
#     'static_path': 'static',
#     'template_path': 'templates',
#     'login_url': '/login',
#     'xsrf_cookie': True,
#     'cookie_secret': '75d68d56257111e78b3e1c1b0d16a734',
#     'debug': config.debug
# }
#
# application = tornado.web.Application([
#     (r'/', MainHandler),
#     (r'/login', LoginHandler),
#     (r'/logout', LogoutHandler),
#     (r'/modify_password', ModifyPasswordHandler),
#     (r'/search', SearchHandler),
#     (r'/result', ResultHandler),
#     (r'/result_async', ResultAsyncHandler),
#     (r'/result_ws', ResultWebSocketHandler),
#     (r'/result_ws_test', ResultWebSocketRealHandler),
#     (r'/get_http_header', GetHttpHeaderHandler),
#     (r'/get_whois', WhoisHandler),
#     # (r'/get_ip_info', IpLookupHandler),
#     (r'/get_banner', PortBannerHandler),
#     (r'/port/scan/event', PortScanEventHandler),
#     (r'/add_brute_task', AddBruteTaskHandler),
#     (r'/brute_progress', BruteProgressHandler),
#     (r'/get_banner', PortBannerHandler),
#     # (r'/manage', ManagerHandler),
#     (r'/admin', AdminHandler),
#     (r'/admin_user_add', UserAdd),
#     (r'/admin_user_delete', DeleteUserHandler),
#     (r'/admin_user_modify_pwd', ModifyPasswordAdminHandler),
#     (r'/reverse_ip_lookup', ReverseIpLookupHandler),
#     (r'/reverse_ip_result_async', ReverseIpLookupAsyncHandler),
#     (r'/detect_domain', DetectDomainHandler),
#     (r'/search_new', SearchNewHandler),
#     (r'/result_new', ResultNewHandler),
#     (r'/reverse_ip_result_ws', IpReverseWebSocketHandler),
#     (r'/reverse_ip_lookup_new', ReverseIpLookUpNewHandler),
#     (r'/chart', ChartHandler)
# ], **settings)

if __name__ == '__main__':
    try:
        detect_db_health_thread = threading.Thread(target=detect_db_health)
        detect_db_health_thread.setDaemon(True)
        detect_db_health_thread.start()

        http_server = HTTPServer(application, xheaders=True)
        http_server.listen(address=config.http_host, port=config.http_port)
        logging.info('Listening %s:%s' % (config.http_host, config.http_port))
        tornado.ioloop.IOLoop.instance().start()
    except Exception as e:
        logging.error('catch error: %s' % str(e))
        logging.error('exit.')
        sys.exit(-1)
