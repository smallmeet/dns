#!/usr/bin/env python 
# -*- coding: utf-8 -*-
""" create at 13/06/2017 """

__author__ = 'binbin'

import gevent
import logging
from utils.banner import get_banner
from utils.scan_port import ScanPort
from utils.whatweb import WhatWeb
import gevent.monkey
from gevent import Timeout
from service import PortScanEventService
import json
from ws4py.client.tornadoclient import TornadoWebSocketClient
from tornado import ioloop
# 必须要加.不然就阻塞了- -~~
from gevent import monkey
monkey.patch_all()
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from utils.config import config_json

logging.basicConfig(level=logging.DEBUG,
                format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S')

engine = create_engine('mysql://{}:{}@{}/{}?charset={}'.format(
    config_json['mysql_user'],
    config_json['mysql_pwd'],
    config_json['mysql_host'],
    config_json['mysql_db'],
    config_json['mysql_charset']
))
db_session = scoped_session(sessionmaker(bind=engine))
TIME_OUT = 300

port_scan_event_service = PortScanEventService(db_session)


class GeventTimeOutException(Exception):
    pass


def _get_banner(ip):
    '''
    获取80端口的信息
    :param ip:
    :return:
    '''
    logging.info("获取80端口的web信息")
    try:
        with Timeout(TIME_OUT, GeventTimeOutException):
            gevent.sleep(0)
            res = get_banner(ip)
            port_scan_event_service.sync_ip_web_info(ip,json.dumps(res))
    except GeventTimeOutException as e:
        logging.info("_get_banner超时")


def _scan_port(ip):
    '''
    扫描端口信息
    :param ip:
    :return:
    '''
    logging.info("获取其它端口信息")
    try:
        with Timeout(TIME_OUT, GeventTimeOutException):
            gevent.sleep(0)
            res = ScanPort().scan(ip)
            port_scan_event_service.sync_ip_port_info(ip,json.dumps(res))
    except GeventTimeOutException as e:
        logging.info("_scan_port超时")


def _cms(domain):
    '''
    获取端口信息
    :param domain:
    :return:
    '''
    logging.info("获取cms信息")
    try:
        with Timeout(TIME_OUT, GeventTimeOutException):
            gevent.sleep(0)
            res = WhatWeb().discriminate(domain)
            port_scan_event_service.sync_cms_info(domain,json.dumps(res))
    except GeventTimeOutException as e:
        logging.info("_cms超时")


class ScanWorkerClient(TornadoWebSocketClient):
     def opened(self):
         while True:
             res = port_scan_event_service.fetch_wait_events()
             logging.info(res)
             for e in res:
                 ip = e.get_ip()
                 domain = e.domain
                 gevent.joinall([
                    gevent.spawn(_get_banner,ip),
                    gevent.spawn(_cms,domain),
                    gevent.spawn(_scan_port,ip),
                 ])

                 port_scan_event_service.finish_event(e.id,2)
                 self.send(json.dumps({'type':'scan_finish_notify','eventid':e.id}))

             time.sleep(0.25)
         # self.send(json.dumps({'type':'notify_event_finish','eventid':4}))
                 # 推送
         pass

     def received_message(self, m):
         logging.info(m)
         # if len(m) == 175:
         #     self.close(reason='Bye bye')

     def closed(self, code, reason=None):
         ioloop.IOLoop.instance().stop()




if __name__ == "__main__":
    ws = ScanWorkerClient('ws://127.0.0.1:8888/result_ws_test', protocols=['http-only', 'chat'])
    ws.connect()
    ioloop.IOLoop.instance().start()

    logging.info(PortScanEventService().get_info_recently("127.0.0.1",'shaobenbin.com'))


