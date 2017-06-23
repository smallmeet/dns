#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import hashlib
import os
import random
import re
import socket
import sys
import types
import uuid
from urlparse import urlparse

import requests

import identicon
from config import config

reload(sys)
sys.setdefaultencoding('utf-8')


def is_running(pid):
    """ping the process"""
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def get_ip_list(domain):
    """获取域名对应的 ip 列表"""
    return socket.gethostbyname_ex(domain)[2]


def get_ip(domain):
    """获取域名对应的 ip 列表字符串, 逗号隔开"""
    try:
        ip_list = socket.gethostbyname_ex(domain)[2]
        ip = ', '.join(ip_list)
    except Exception:
        ip = 'null'
    return ip


def get_ip_api(domain):
    """通过接口查询 Ip， 同步。"""
    # response = requests.get('http://192.168.1.169:8310/dig_a/' + domain)
    response = requests.get('http://' + config.domain_detect_api_host + '/dig_a/' + domain)
    response_json = response.json()
    response_data = response_json['data']
    return ', '.join(response_data) if response_data is not None else '无'


REGX_PER_DICT = r'^[a-zA-Z0-9]+$'
REGX_START = r'^\.'
REGX_END = r'\.$'


def is_valid_domain(domain):
    """判断域名是否合法"""
    if re.match(REGX_START, domain) or re.match(REGX_END, domain):
        return False
    dicts = domain.split('.')
    for per_dict in dicts:
        if not re.match(REGX_PER_DICT, per_dict):
            return False
    return True


def parse_domain_simple(domain):
    """简单处理一下域名, 返回域名"""
    domain = domain.strip().replace(' ', '').replace('http://', '').replace('https://', '').split('/')[0]
    rs_re = re.findall('([^a-zA-Z0-9]+)$', domain)
    if rs_re:
        domain = domain.replace(rs_re[0], '')
    return domain


def is_valid_ip(ip):
    # return bool(re.match(r'^(?:(?:2[0-4][0-9]\.)|(?:25[0-5]\.)|(?:1[0-9][0-9]\.)|(?:[1-9][0-9]\.)|(?:[0-9]\.)){3}(?:(?:2[0-5][0-5])|(?:25[0-5])|(?:1[0-9][0-9])|(?:[1-9][0-9])|(?:[0-9]))$', ip))
    return bool(re.match(
        r"^(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|[1-9])\."
        + "(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d)\."
        + "(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d)\."
        + "(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d)$", ip))



def now():
    """获取当前时间"""
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def original_time():
    """"""
    return datetime.datetime.fromtimestamp(0).strftime('%Y-%m-%d %H:%M:%S')


def str2bool(content):
    """将字符串 false true 转换为 Python bool 类型"""
    return True if content and content == 'true' else False


def dumps_handler(src):
    """序列化"""
    if isinstance(src, datetime.datetime):
        return src.strftime('%Y-%m-%d %H:%M:%S')
    return str(src)


def is_threads_done(threads):
    for per_thread in threads:
        if per_thread.is_alive():
            return False
    return True


def md5(string):
    if type(string) is types.StringType:
        m = hashlib.md5()
        m.update(str)
        return m.hexdigest()
    else:
        return ''


seeds = 'qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM0123456789'
seeds_length = len(seeds)


def random_str():
    result = ''
    random_length = random.randint(0, seeds_length - 1)
    for i in xrange(random_length):
        result += seeds[random.randint(0, random_length - 1)]
    return result


def next_uuid():
    return str(uuid.uuid3(uuid.NAMESPACE_DNS, random_str())).replace('-', '')


def img_create(filename):
    filename_url = 'static/img/avatar/{0}.png'.format(filename)
    result=''
    for i in filename:
        result += '{0}'.format(ord(i))
    img_id = int(result)
    img = identicon.render_identicon(img_id, 36)
    img.save(filename_url)
    return True


def _get_netloc(url):
    o = urlparse(url)
    return o.netloc


def remove_repeat_domain(data_list):
    """去除重复结果"""
    result_list = []
    domain_set = set()
    for elem in data_list:
        url = elem['url']
        domain = _get_netloc(url)
        print(domain)
        if domain not in domain_set:
            domain_set.add(domain)
            result_list.append(elem)

    return result_list
