#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys

import tornado.web
import tornado.ioloop
import tornado.autoreload
from tornado.httpserver import HTTPServer

from handlers.interfaces import GetHttpHeaderHandler, PortBannerHandler, DetectDomainHandler,PortScanEventHandler
from handlers.login import LoginHandler, LogoutHandler, ModifyPasswordHandler
from handlers.result import ResultHandler, ResultWebSocketHandler, AddBruteTaskHandler, BruteProgressHandler, \
    ResultAsyncHandler, ResultWebSocketRealHandler, IpReverseWebSocketHandler
from handlers.result import WhoisHandler
from handlers.result_new import ResultNewHandler, ReverseIpLookUpNewHandler
from handlers.reverse_ip_lookup import ReverseIpLookupHandler, ReverseIpLookupAsyncHandler
from handlers.search import SearchHandler, SearchNewHandler
from handlers.usermanager import UserAdd, DeleteUserHandler, ModifyPasswordAdminHandler, AdminHandler
from utils.config import config

reload(sys)
sys.setdefaultencoding('utf-8')

logging.basicConfig(level=logging.DEBUG,
                format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S')


class MainHandler(tornado.web.RequestHandler):

    def get(self):
        logging.debug(self.request.remote_ip)
        self.redirect('/login')


settings = {
    'static_path': 'static',
    'template_path': 'templates',
    'login_url': '/login',
    'xsrf_cookie': True,
    'cookie_secret': '75d68d56257111e78b3e1c1b0d16a734',
    'debug': config.debug
}

application = tornado.web.Application([
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
    (r'/reverse_ip_lookup_new', ReverseIpLookUpNewHandler)
], **settings)

if __name__ == '__main__':
    try:
        http_server = HTTPServer(application, xheaders=True)
        http_server.listen(address=config.http_host, port=config.http_port)
        logging.info('Listening %s:%s' % (config.http_host, config.http_port))
        tornado.ioloop.IOLoop.instance().start()
    except Exception as e:
        logging.error('catch error: %s' % str(e))
        logging.error('exit.')
        sys.exit(-1)
