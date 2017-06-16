#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
ip地址查询接口
"""
import logging
import traceback

import requests
import utils


# class IpAddress(object):
#
#     def __init__(self, ip):
#         self.ip = ip
#         self.requests_settings = {
#             'timeout': 5
#         }
#
#     def query(self):
#         api_url = 'http://int.dpool.sina.com.cn/iplookup/iplookup.php?format=json&ip={0}'
#         url = api_url.format(self.ip)
#         try:
#             rsp = requests.get(url, **self.requests_settings)
#         except Exception as e:
#             logging.error('获取 ip 信息失败.')
#             logging.error(traceback.format_exc())
#             logging.error(str(e))
#             return None
#         return rsp.json()

requests_settings = {
    'timeout': 5
}


def query(ip):
    if not utils.is_valid_ip(ip):
        return None
    api_url = 'http://int.dpool.sina.com.cn/iplookup/iplookup.php?format=json&ip={0}'
    url = api_url.format(ip)
    try:
        rsp = requests.get(url, **requests_settings)
    except Exception as e:
        logging.error('获取 ip 信息失败.')
        logging.error(traceback.format_exc())
        logging.error(str(e))
        return None
    return rsp.json()


if __name__ == '__main__':
    a = query('202.102.110.204')
    print(a)
    print(a['country'],a['province'],a['city'])
