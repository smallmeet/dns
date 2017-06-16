#!/usr/bin/env python
# -*- coding: utf-8 -*-

from argparse import Namespace
import json
import sys
import os
import importlib
import threading
import time
import logging
import traceback

import requests

from g import g_lock
from config import db, redis_cursor, config
from utils import get_ip, now, is_threads_done, dumps_handler, get_ip_api
import iplookup

from config import config
from reverse_ip_lookup import ReverseIpLookUp

sys.path.append('.')
sys.path.append('..')

project_name = config.project_name
reverse_ip_key_prefix = project_name + '__result_'


def lazy_load(module_name, prefix_package=None):
    """动态加载模块"""
    module = importlib.import_module(module_name, prefix_package)
    class_name = ''.join([i.capitalize() for i in module_name.replace('.', '').split('_')])
    target_class = getattr(module, class_name)
    return target_class


def domain_and_ip(domain_list):
    """返回域名和 ip 对应的字典"""
    if isinstance(domain_list, list):
        result_dict = {
            'data': {}
        }
        for per_domain in domain_list:
            result_dict['data'][per_domain] = {
                'ip': get_ip_api(per_domain)
            }
    else:
        result_dict = {
            'data': domain_list
        }
        for per_domain in result_dict['data']:
            result_dict['data'][per_domain] = {
                'ip': get_ip_api(per_domain)
            }

    return result_dict


def set_origin(result, func):
    class_name = func.im_class.__name__

    if class_name == 'Baidu' \
            or class_name == 'Alexa' \
            or class_name == 'ILinks' \
            or class_name == 'Bing' \
            or class_name == 'Netcraft' \
            or class_name == 'Sitedossier' \
            or class_name == 'Threatminer' \
            or class_name == 'Bugbank' \
            or class_name == 'Ip138' \
            or class_name == 'Threatcrowd' \
            or class_name == 'HackTarget' \
            or class_name == 'Juanluo':
        origin = 'api'
    elif class_name == 'SubDomainsBrute':
        origin = 'brute'
    elif class_name == 'Crt' \
            or class_name == 'GetSsl':
        origin = 'https'
    elif class_name == 'PageCatcher':
        origin = 'page'
    else:
        origin = 'unknown'

    result['origin'] = origin
    return result


def get_locations(result):
    for per_domain in result['data']:
        per_domain_data = result['data'][per_domain]

        ip_str = per_domain_data['ip']
        ip_list = ip_str.split(', ')

        locations = []
        for ip in ip_list:
            location_json = iplookup.query(ip)
            if location_json:
                if location_json.get('country') or location_json.get('province') or location_json.get('city'):
                    if location_json.get('country') == '中国' and location_json.get('province') and location_json.get('city'):
                        locations.append(location_json['province'] + " " + location_json['city'])
                    else:
                        locations.append(location_json['country'] + " " + location_json['province'] + " " + location_json['city'])
        per_domain_data['location'] = ', '.join(locations)
    return result


class SearchTask(object):
    """子域名搜索任务"""

    def __init__(self, keywords, **kwargs):
        self.target = keywords
        logging.info(self.target)
        self.is_brute = True if kwargs.get('is_burte') else False
        self.kwargs = kwargs
        logging.info(kwargs)
        # rs = db.query('SELECT `id` FROM `system_domain` WHERE `domain` = %s', self.target)
        # self.domain_id = rs[0]['id']
        self.worker_threads = []

    @staticmethod
    def task_runner(func, callback):
        """运行任务
        {
            "origin": 来源,
            "data": {
                "DOMAIN": {
                    'ip': [ IPS ],
                    'location': [ LOCATIONS ]
                }
                ...
            }
        }
        """
        try:
            result = func()
            result = domain_and_ip(result)
            result = set_origin(result, func)
            result = get_locations(result)
            callback(func, result)
        except Exception as e:
            logging.error('Caught an error in %' + threading.current_thread().getName())
            logging.error(traceback.format_exc())
            logging.error(str(e))

    def save_result(self, func, result):
        """保存结果"""
        g_lock.acquire()

        sql = '''
            INSERT INTO
                `system_subdomain_result` (`domain_id`, `subdomain`, `ip`, `last_commit_time`, `origin`, `location`)
            SELECT
                `system_domain`.`id`, %s, %s, %s, %s, %s
            FROM
                `system_domain`
            WHERE
                `system_domain`.`domain` = %s
            ON DUPLICATE KEY UPDATE
                `ip` = VALUES(`ip`),
                `last_commit_time` = VALUES(`last_commit_time`)
        '''
        time_now = now()
        logging.info('start saving.')
        logging.info(func.im_class.__name__)
        logging.info(result)
        try:
            for per_domain in result['data'].keys():
                per_domain_data = result['data'][per_domain]
                db.insert(sql,
                          per_domain,
                          per_domain_data['ip'],
                          time_now,
                          result['origin'],
                          per_domain_data['location'],
                          self.target)
            logging.info('saving over.')
        except Exception as e:
            logging.error(traceback.format_exc())
            logging.error('caught an error when saving result:\n%s (%s)`' % (str(e), func))
        finally:
            g_lock.release()

    def load_brute_module(self):
        """加载爆破模块"""
        sub_domains_brute = lazy_load('.sub_domains_brute', 'api.utils')
        brute_settings = {
            'file': 'api/dict/custom.txt',
            'full_scan': False,
            'i': False,
            'threads': 20,
            'output': None,
            'task_id': self.kwargs['task_id']
        }
        return sub_domains_brute(self.target, Namespace(**brute_settings))

    def run(self):
        # 是否是单独爆破任务
        if 'only_brute' in self.kwargs and self.kwargs['only_brute']:
            logging.debug('开始爆破')
            enable_brute = True
            if enable_brute:
                sub_domains_brute_instance = self.load_brute_module()
                brute_result = sub_domains_brute_instance.execute()
                brute_result = domain_and_ip(brute_result)
                brute_result = set_origin(brute_result, sub_domains_brute_instance.execute)
                self.save_result(sub_domains_brute_instance.execute, brute_result)
            else:
                time.sleep(10)
                # self.save_result(self.save_result, {'aaaa.com': '1.1.1.1'})
            return

        # Whois 信息
        whois_task = WhoisTask(self.target)
        t = threading.Thread(target=whois_task.run())
        t.setDaemon(True)
        self.worker_threads.append(t)
        t.start()

        # 域名详情, NS 和 MX 记录.
        domain_detail_task = DomainDetailTask(self.target)
        t = threading.Thread(target=domain_detail_task.run)
        t.setDaemon(True)
        self.worker_threads.append(t)
        t.start()

        # 先检测域传送, 如果有域传送漏洞, 那么直接导出, 无需再找.
        dns_zone_transfer = lazy_load('.dns_zone_transfer', 'api.utils')
        dns_zone_transfer_result = dns_zone_transfer(self.target).execute()
        if len(dns_zone_transfer_result.keys()):
            logging.debug('发现域传送漏洞.')
            self.save_result(self.run, dns_zone_transfer_result)
            return

        # 加载各种模块
        modules_class = []
        for module_name in config.modules.keys():
            if config.modules[module_name]:
                target_class = lazy_load('.' + module_name, 'api.utils')
                modules_class.append(target_class)
                if config.debug:
                    print(target_class)

        # 运行
        for per_class in modules_class:
            t = threading.Thread(target=self.task_runner, args=(per_class(self.target).execute, self.save_result))
            self.worker_threads.append(t)
            t.setDaemon(True)
            t.start()

        # 爆破
        if self.is_brute == '1':
            logging.debug('开始爆破')
            sub_domains_brute_instance = self.load_brute_module()
            t = threading.Thread(target=sub_domains_brute_instance.execute)
            self.worker_threads.append(t)
            t.setDaemon(True)
            t.start()
        while not is_threads_done(self.worker_threads):
            time.sleep(0.1)


class WhoisTask(object):
    """Whois 信息搜索任务"""

    def __init__(self, target, **kwargs):
        self.target = target
        self.kwargs = kwargs

    @staticmethod
    def task_runner(func, callback):
        whois_result = func()
        callback(whois_result)

    def callback(self, result):
        g_lock.acquire()
        logging.debug('whois results: ' + str(result))
        sql = '''
            UPDATE
                `system_domain`
            SET
                `domain_whois` = %s
            WHERE
                `domain` = %s;
        '''
        try:
            db.execute(sql, json.dumps(result, default=dumps_handler), self.target)
        except Exception as e:
            logging.error('saving whois data error.')
            logging.error(traceback.format_exc())
            logging.error(str(e))
        g_lock.release()

    def run(self):
        module_whois = lazy_load('.get_whois', 'api.utils')
        self.task_runner(module_whois(self.target).execute, self.callback)


class DomainDetailTask(object):
    """NS, MX 记录查询任务"""

    def __init__(self, target, **kwargs):
        self.target = target
        self.kwargs = kwargs

    @staticmethod
    def task_runner(func, callback):
        whois_result = func()
        callback(whois_result)

    def save(self, ns_records, mx_records):
        g_lock.acquire()
        # logging.debug('whois results: ' + str(result))
        ns_data = json.dumps(ns_records['data']) #if ns_records['data'] else ''
        mx_data = json.dumps(mx_records['data']) #if mx_records['data'] else ''
        logging.info('domain_detail ns: {}'.format(ns_records))
        logging.info('domain_detail mx: {}'.format(mx_records))
        sql = '''
            UPDATE
                `system_domain`
            SET
                `ns_records` = %s, `mx_records` = %s
            WHERE
                `domain` = %s;
        '''
        try:
            db.execute(sql, ns_data, mx_data, self.target)
        except Exception as e:
            logging.error('saving ns mx data error.')
            logging.error(traceback.format_exc())
            logging.error(str(e))
        g_lock.release()

    def run(self):
        api_url = 'http://' + config.domain_detect_api_host + '/dig_ns/' + self.target
        ns_records = requests.get(api_url).json()
        api_url = 'http://' + config.domain_detect_api_host + '/dig_mx/' + self.target
        mx_records = requests.get(api_url).json()
        self.save(ns_records, mx_records)


class ReverseIpLookUpTask(object):
    """Ip 反查任务"""

    def __init__(self, keywords, **kwargs):
        self.target_ip = keywords
        self.task_id = kwargs['task_id']
        self.kwargs = kwargs

    @staticmethod
    def task_runner(func, callback):
        result_json = func()
        callback(result_json)

    def save_to_cache(self, result_json):
        key = reverse_ip_key_prefix + str(self.task_id)
        all_results = redis_cursor.hget(key, 'result')
        all_results_json = json.loads(all_results) if all_results else []
        all_results_json.append(result_json)
        redis_cursor.hset(key, 'result', json.dumps(all_results_json))
        redis_cursor.expire(key, 300)

    def callback(self, result_json):
        # TODO: 结果存数据库和缓存
        print('callback')
        print(result_json)

        for per_ip in result_json.keys():
            per_data = result_json[per_ip]

            logging.info(per_ip)
            db.insert('''INSERT IGNORE INTO `system_ips` VALUES (NULL, inet_aton(%s))''', per_ip)
            for per_result in per_data:
                domain = per_result['domain']
                url = per_result['url']
                title = per_result['title']

                db.insert('''INSERT IGNORE INTO `system_domains` VALUES (NULL, %s)''', domain)
                db.insert('''
                    INSERT INTO
                        `system_domain_and_ip` (`ip_id`, `domain_id`, `url`, `title`, `create_time`, `update_time`)
                    SELECT 
                        `i`.`id`, `d`.`id`, %s, %s, %s, %s
                    FROM 
                        `system_ips` `i`, `system_domains` `d`
                    WHERE
                        `i`.`ip` = inet_aton(%s)
                        AND `d`.`domain` = %s
                    ON DUPLICATE KEY UPDATE
                        `url` = VALUES(`url`),
                        `title` = VALUES(`title`),
                        `update_time` = VALUES(`update_time`)
                    ''',
                    url, title, now(), now(), per_ip, domain)

    def run(self):
        module_reverse_ip_lookup = ReverseIpLookUp
        self.task_runner(module_reverse_ip_lookup(self.target_ip, on_progress=self.save_to_cache).run, self.callback)


def load_task(task_name):
    if task_name == 'search_domain':
        return SearchTask
    elif task_name == 'reverse_ip_lookup':
        return ReverseIpLookUpTask
    return None


def test():
    # print os.getcwd()
    # task = SearchTask('cugb.edu.cn')
    # task.run()

    task_runner = load_task('reverse_ip_lookup')('220.191.214.46')
    task_runner.run()


if __name__ == '__main__':
    test()
