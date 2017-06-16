#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import sys

import requests
import tornado.web
from concurrent.futures import ThreadPoolExecutor
from tornado.concurrent import run_on_executor
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

from base import BaseHandler
from utils import utils
from utils.banner import get_banner
from utils.config import config
from utils.whatweb import WhatWeb
from service import PortScanEventService


sys.path.append('../')
from api.utils.banner import GetBanner


class GetHttpHeaderHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self, *args, **kwargs):
        target_domain = self.get_argument('domain', None)

        result_dict = {'success': 0}
        if target_domain:
            target_domain = utils.parse_domain_simple(target_domain)
            if utils.is_valid_domain(target_domain):
                result_dict['success'] = 1
                result_dict['domain'] = target_domain
                result_dict['http_header'] = GetBanner(target_domain).execute()
            else:
                logging.debug('获取 header 失败, 输入域名不合法.')
        else:
            logging.debug('获取 header 失败, 没有输入域名.')
        self.write(json.dumps(result_dict))


class PortBannerHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self, *args, **kwargs):
        result_json = {'success': 0}

        target_ip = self.get_argument('ip', None)

        if target_ip and utils.is_valid_ip(target_ip):
            banner_info = get_banner(target_ip)
            if banner_info is not None:
                result_json['success'] = 1
                result_json['data'] = banner_info

            what_web = WhatWeb().discriminate(target_ip)
            if what_web:
                result_json['url'] = what_web['url']
                result_json['cms'] = what_web['cms']

        else:
            logging.debug('用户输入有误, {0}'.format(target_ip))

        self.finish(json.dumps(result_json))

class PortScanEventHandler():
    @tornado.web.authenticated
    def post(self):
        '''
        创建一个扫描时间
        :return:
        '''

        # check ip && domain是否已经查询过了,如果是就不再查询了,且直接将结果推送到前段
        ip = self.get_argument('ip')
        domain = self.get_argument('domain')

        port_scan_service = PortScanEventService()

        res = port_scan_service.get_info_recently(ip,domain)
        if res:
            # websocket直接推送
            pass
        else:
            # create event 创建一个event时间
            port_scan_service.create_event(ip,domain)

        self.finish(json.dumps({'code':1}))


AsyncHTTPClient.configure('tornado.curl_httpclient.CurlAsyncHTTPClient', max_clients=100)


class IpLookupHandler(BaseHandler):

    # @tornado.web.asynchronous
    # @tornado.gen.coroutine
    # def get(self, *args, **kwargs):
    #     result_json = {'success': 0}
    #
    #     target_ip = self.get_argument('ip', '').strip()
    #
    #     # if target_ip and utils.is_valid_ip(target_ip):
    #     #     ip_info = IpAddress(target_ip).query()
    #     #     if result_json is not None:
    #     #         result_json['success'] = 1
    #     #         result_json['data'] = ip_info
    #     # else:
    #     #     logging.debug('用户输入有误, {0}'.format(target_ip))
    #
    #     if target_ip and utils.is_valid_ip(target_ip):
    #         api_url = 'http://int.dpool.sina.com.cn/iplookup/iplookup.php?format=json&ip={}'.format(target_ip)
    #         request = HTTPRequest(url=api_url,
    #                               request_timeout=60)
    #         logging.info('开始调用 zone, ' + target_ip)
    #         async_http_client = AsyncHTTPClient()
    #         response = yield tornado.gen.Task(async_http_client.fetch, request)
    #         logging.info('调用 zone 结束, ' + target_ip)
    #         if response is not None:
    #             response_json = json.loads(response.body)
    #             result_json['success'] = 1
    #             result_json['data'] = response_json
    #         else:
    #             logging.debug('调用 API 失败。 {}'.format(api_url))
    #     else:
    #         logging.debug('用户输入有误, {0}'.format(target_ip))
    #     self.finish(json.dumps(result_json))
    #
    # executor = ThreadPoolExecutor(max_workers=1000)
    #
    # @run_on_executor
    # def get(self, *args, **kwargs):
    #     self.add_header('Cache-Control', 'no-cache')
    #     result_json = {'success': 0}
    #
    #     target_ip = self.get_argument('ip', None)
    #
    #     if target_ip and utils.is_valid_ip(target_ip):
    #         ip_info = IpAddress(target_ip).query()
    #         if result_json is not None:
    #             result_json['success'] = 1
    #             result_json['data'] = ip_info
    #     else:
    #         logging.debug('用户输入有误, {0}'.format(target_ip))
    #
    #     self.write(json.dumps(result_json))
    pass




class DetectDomainHandler(BaseHandler):

    # @tornado.web.asynchronous
    # @tornado.gen.coroutine
    # def get(self, *args, **kwargs):
    #     target = self.get_argument('target')
    #
    #     api_url = 'http://' + config.domain_detect_api_host + '/detect_domain/{}'.format(target)
    #     request = HTTPRequest(url=api_url,
    #                           request_timeout=60)
    #     logging.info('开始调用 detect, ' + target)
    #     async_http_client = AsyncHTTPClient()
    #     response = yield tornado.gen.Task(async_http_client.fetch, request)
    #     logging.info('调用 detect 结束, ' + target)
    #     if response is not None:
    #         result_text = response.body
    #     else:
    #         result_text = '{"state": -1}'
    #     self.finish(result_text)

    executor = ThreadPoolExecutor(max_workers=1000)

    @run_on_executor
    def get(self, *args, **kwargs):
        self.add_header('Cache-Control', 'no-cache')
        target = self.get_argument('target')

        api_url = 'http://' + config.domain_detect_api_host + '/detect_domain/' + target
        logging.info('开始调用 detect, ' + target)
        response = requests.get(api_url)
        logging.info('调用 detect 结束, ' + target)
        if response is not None:
            result_text = response.text
        else:
            result_text = '{"state": -1}'
        self.finish(result_text)
