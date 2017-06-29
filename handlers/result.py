#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import print_function
from __future__ import print_function
import json
import logging
import sys
import threading
import traceback
from Queue import Queue, Empty

import datetime
import requests
import time
import tornado.web
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm.exc import NoResultFound
from tornado import gen, ioloop
from tornado.websocket import WebSocketHandler
from concurrent.futures import ThreadPoolExecutor
from tornado.concurrent import run_on_executor

from handlers.base import BaseHandler, BaseWebSocketHandler
from models import Domain, SubDomainResult, TaskRecords
from utils import misc
from utils.config import config, db, redis_cursor
from utils.history_ip import get_history_ip
from service import PortScanEventService, ReverseIpService
from utils.location_abbr import get_location_abbr
from utils.reverse_ip_lookup import ReverseIpLookUp

sys.path.append('../')
from utils.misc import parse_domain_simple, is_valid_domain, str2bool

pre_system = config.pre_system
mysql_cursor = db
names = locals()

project_name = config.project_name
task_next_id_key = project_name + '__sp'
running_tasks_key = project_name + '__tasks'
task_queue_key = project_name + '__task_queue'
task_detail_key_prefix = project_name + '__task_detail_'


def get_task_state(task_target):
    """返回任务状态:
        -1: 不存在该任务
        0: 该任务正在排队
        1: 已取出, 正在运行
        2: 已完成
    """
    task_state = -1
    try:
        rs = db.query('''
            SELECT
                `state`
            FROM
                `system_task_records`
            WHERE
                `keywords` = %s
            ORDER BY
                `create_time`
            DESC
        ''', task_target)
        if len(rs) > 0:
            task_state = int(rs[0]['state'])
    except Exception as e:
        logging.error('取任务状态失败.')
        logging.error(traceback.format_exc())
        logging.error(str(e))
    return task_state


def get_task_id(keywords):
    task_id = -1
    try:
        rs = db.query('''
            SELECT
                `id`
            FROM
                `system_task_records`
            WHERE
                `keywords` = %s
            ORDER BY
                `create_time`
            DESC
        ''', keywords)
        if len(rs) > 0:
            task_id = int(rs[0]['id'])
    except Exception as e:
        logging.error('取任务状态 id 失败.')
        logging.error(traceback.format_exc())
        logging.error(str(e))
    return task_id


def add_new_task_state(target, task_id):
    try:
        db.insert('''
              INSERT INTO
                  `system_domain` (`domain`, `domain_whois`, `ns_records`, `mx_records`)
              VALUES
                  (%s, "", "", "")
              ON DUPLICATE KEY UPDATE
                  `domain` = VALUES(`domain`)
        ''',target)

        db.insert('''
                INSERT INTO
                    `system_task_records` (`id`, `keywords`, `create_time`, `finish_time`, `state`)
                VALUES
                    (%s, %s, %s, %s, %s)''',
                  task_id,
                  target,
                  misc.now(),
                  misc.original_time(),
                  '0')
    except Exception as e:
        logging.error('添加任务状态失败')
        logging.error(traceback.format_exc())
        logging.error('Caught an error when insert a new task state: %s' % str(e))


def push_task(target_domain, dictionary):
    try:
        current_task_id = redis_cursor.incr(task_next_id_key)
        # 向数据库更新任务状态
        add_new_task_state(target_domain, current_task_id)
        # 将任务 push 到队列
        task_detail_key = '%s%s' % (task_detail_key_prefix, current_task_id)
        redis_cursor.hset(task_detail_key, 'keywords', target_domain)
        redis_cursor.hset(task_detail_key, 'is_brute', int(dictionary))
        redis_cursor.hset(task_detail_key, 'type', 'search_domain')
        redis_cursor.rpush(task_queue_key, current_task_id)
        return True
    except Exception as e:
        logging.error(traceback.format_exc())
        logging.error('Caught an error when insert a new task: %s' % str(e))
    return False


def push_brute_task(target_domain):
    try:
        current_task_id = redis_cursor.incr(task_next_id_key)
        # 向数据库更新任务状态
        add_new_task_state(target_domain, current_task_id)
        # 将任务 push 到队列
        task_detail_key = '%s%s' % (task_detail_key_prefix, current_task_id)
        redis_cursor.hset(task_detail_key, 'keywords', target_domain)
        redis_cursor.hset(task_detail_key, 'only_brute', 1)
        redis_cursor.hset(task_detail_key, 'type', 'search_domain')
        redis_cursor.rpush(task_queue_key, current_task_id)
        return True
    except Exception as e:
        logging.error(traceback.format_exc())
        logging.error('Caught an error when insert a new task: %s' % str(e))
    return False


class ResultHandler(BaseHandler):
    """搜索结果页"""

    @tornado.web.authenticated
    def get(self, *args, **kwargs):
        # 检查用户是否登录
        cookie_username = self.get_secure_cookie(pre_system + 'username')
        if not cookie_username:
            self.redirect('/login')
            return

        try:
            rs = db.query('''
                SELECT
                    `avatar`
                FROM
                    `system_admin_user`
                WHERE
                    `username` = %s
                ''', cookie_username)
            avatar = rs[0]['avatar']
        except Exception:
            avatar = ''

        # 取参数
        target_domain = self.get_argument('content', '')
        https = str2bool(self.get_argument('https', 'false'))
        searchEngine = str2bool(self.get_argument('searchEngine', 'false'))
        domain = str2bool(self.get_argument('domain', 'false'))
        dictionary = str2bool(self.get_argument('dictionary', 'false'))

        # 处理域名
        target_domain = parse_domain_simple(target_domain)
        logging.debug('target domain is: ' + target_domain)
        if not is_valid_domain(target_domain):
            # self.redirect('/home?error=1&msg=1')
            self.render('home.html')
            return

        # 查询任务是否存在
        task_state = get_task_state(target_domain)

        # 如果任务不存在, 则创建任务
        if -1 == task_state:
            logging.debug('任务不存在, 创建任务.')
            push_task(target_domain, dictionary)
            logging.debug('创建任务 over.')
        elif 0 == task_state:
            logging.debug('正在排队')
        elif 1 == task_state:
            logging.debug('正在运行')
        elif 2 == task_state:
            logging.debug('已经结束')
        self.render('result.html', avatar=avatar, username=cookie_username)


def is_bruting(domain):
    running_task_ids = redis_cursor.hkeys(running_tasks_key)
    for task_id in running_task_ids:
        task_detail_key = task_detail_key_prefix + task_id
        if redis_cursor.hget(task_detail_key, 'target') == domain:
            is_brute = redis_cursor.hget(task_detail_key, 'is_brute')
            is_brute = bool(int(is_brute)) if is_brute is not None else False
            only_brute = redis_cursor.hget(task_detail_key, 'only_brute')
            only_brute = bool(int(only_brute)) if only_brute is not None else False
            if is_brute or only_brute:
                return True
    return False


class ResultAsyncHandler(BaseHandler):
    """获取结果的接口"""

    def get(self, *args, **kwargs):
        result_dict = {
            'success': 1
        }

        try:
            target_domain = self.get_argument('domain', '')
            # 上次查询的 id
            since = int(self.get_argument('since', 0))
            limit = int(self.get_argument('limit', 10))
            limit = 30 if limit > 30 else limit
            rs = db.query('SELECT `id` FROM `system_domain` WHERE `domain` = %s', target_domain)
            if len(rs) == 0:
                logging.debug('没有该域名')
                raise Exception('no such domain')
            domain_id = rs[0]['id']
            logging.debug('domain_id: %s' % domain_id)
            sub_domains = db.query('''
                SELECT
                    `subdomain`, `ip`, `last_commit_time`, `origin`, `location`
                FROM
                    `system_subdomain_result`
                WHERE
                    `domain_id` = %s
                ORDER BY
                    `last_commit_time`
                LIMIT
                    %s, %s
            ''', domain_id, since, limit)
            if len(sub_domains) > 0:
                for per_domain in sub_domains:
                    per_domain['last_commit_time'] = per_domain['last_commit_time'].strftime('%y-%m-%d %H:%M:%S')
                    origin = per_domain['origin']
                    if origin == 'api':
                        per_domain['origin'] = '接口'
                    elif origin == 'https':
                        per_domain['origin'] = '证书'
                    elif origin == 'brute':
                        per_domain['origin'] = '爆破'
                    elif origin == 'page':
                        per_domain['origin'] = '页面'
                    else:
                        per_domain['origin'] = '未知'
                logging.debug('domain_id: %s' % str(sub_domains))
                result_dict['sub_domains'] = list(sub_domains)
            else:
                result_dict['sub_domains'] = list()

            # 获取任务状态
            task_state = get_task_state(target_domain)
            result_dict['task_state'] = task_state
            result_dict['is_brute'] = is_bruting(target_domain)
        except Exception as e:
            logging.error(traceback.format_exc())
            logging.error('Caught an error: %s' % str(e))
            result_dict['success'] = 0
        self.write(json.dumps(result_dict))


class ResultWebSocketHandler(BaseWebSocketHandler):
    """获取结果的接口"""

    executor = ThreadPoolExecutor(max_workers=1000)

    def check_origin(self, origin):
        logging.info('check_origin: {}'.format(origin))
        return True

    @run_on_executor
    def on_message(self, message):
        print(message)
        request_json = json.loads(message)

        if 'type' in request_json.keys():
            if request_json['type'] == 'notify_event_finish':
                eventid = request_json['eventid']
                self.emit_scan_info(eventid)
                print("eventid : %d is finish" % (eventid))
        else:
            if request_json.get('domain') != 'kq88.com':
                return


            self.example_get_domain_detail()
            self.example_get_ip_history()

            response_json = self.example_get_sub_domains()
            self.write_message(response_json)

            self.example_get_domain_state(response_json)
            self.example_get_scan_info()

    def emit_scan_info(self,eventid):
        res = PortScanEventService(self.db).get_info_by_id(eventid)
        if not res:
            return

        res['type'] = 'scan_info'

        self.write_message(res)

        pass

    def example_get_scan_info(self):
        self.write_message({'type':'scan_info',"domain_info": {"domain": "hy2.kq88.com", "cms": {"url": "hy2.kq88.com", "md5": "1870a829d9bc69abf500eca6f00241fe", "cms": "wordpress", "error": "no"}, "sync_time": "2017-06-14-17"}, "ip_info": {"ip": {"ip": "42.121.57.135", "web_info": {"product": "Apache httpd", "name": "http", "extrainfo": "(CentOS) PHP/5.6.29", "reason": "syn-ack", "cpe": "cpe:/a:apache:http_server:2.4.6", "state": "open", "version": "2.4.6", "conf": "10"}, "port_info": "{\"source\": \"hackertarget\", \"dataset\": \"PORT     STATE    SERVICE       VERSION\\n80/tcp   open     http          Apache httpd 2.4.6 ((CentOS) PHP/5.6.29)\"}"}}, "type": "scan_info"})


    def example_get_domain_detail(self):
        self.write_message({
            'type': 'domain_detail',
            'domain': 'kq88.com',
            'ns_records': [
                {
                    'name': 'f1g1ns2.dnspod.net',
                    'ip': '180.163.19.15'
                },
                {
                    'name': 'f1g1ns2.dnspod.net',
                    'ip': '61.129.8.159'
                }
            ],
            'mx_records': [
                {
                    'name': 'mxdomain.qq.com',
                    'ip': '183.57.48.35'
                }
            ],
            'whois': {"updated_date": ["2017-04-06 00:00:00", "2016-01-19 18:15:16"], "status": ["ok https://icann.org/epp#ok", "ok http://www.icann.org/epp#OK"], "name": "yaojian zhou", "dnssec": "unsigned", "city": "xing hua shi", "expiration_date": ["2023-06-12 00:00:00", "2023-06-12 08:16:17"], "zipcode": "225700", "domain_name": ["KQ88.COM", "kq88.com"], "country": "CN", "whois_server": "grs-whois.hichina.com", "state": "jiang su", "registrar": "HICHINA ZHICHENG TECHNOLOGY LTD.", "referral_url": "http://www.net.cn", "address": "xinghua shi chang'an juweihui banqiao jingyuan wenhuajie dongce 2# 02", "name_servers": ["F1G1NS1.DNSPOD.NET", "F1G1NS2.DNSPOD.NET", "f1g1ns1.dnspod.net", "f1g1ns2.dnspod.net"], "org": "jiangsu aichi Network Technology Co., Ltd.", "creation_date": ["2000-06-12 00:00:00", "2000-06-12 08:16:17"], "emails": ["kq88@163.com", "DomainAbuse@service.aliyun.com"]}
        })
        pass

    def example_get_ip_history(self):
        self.write_message({
            'type': 'ip_history',
            'domain': 'kq88.com',
            "history":[
                {
                    "ip": "58.222.21.70",
                    "start_date": "2017-04-12",
                    "end_date": "2017-06-09"
                }
            ]
        })

    def example_get_sub_domains(self):
        return {"domain":"kq88.com","task_state":2,"type":"sub_domain","success":1,"sub_domains":[{"last_commit_time":"17-06-07 17:50:59","ip":"无","sub_domain":"book.kq88.com","location":"","origin":"接口"},{"last_commit_time":"17-06-07 17:50:59","ip":"无","sub_domain":"vv.kq88.com","location":"","origin":"证书"},{"last_commit_time":"17-06-07 17:50:59","ip":"42.121.57.135","sub_domain":"hy2.kq88.com","location":"CN","origin":"接口"},{"last_commit_time":"17-06-07 17:50:59","ip":"无","sub_domain":"by.kq88.com","location":"","origin":"接口"},{"last_commit_time":"17-06-07 17:50:59","ip":"无","sub_domain":"site.kq88.com","location":"","origin":"接口"},{"last_commit_time":"17-06-07 17:50:59","ip":"183.61.38.175, 14.17.42.24, 183.61.51.74, 14.18.245.237","sub_domain":"mail.kq88.com","location":"CN","origin":"接口"},{"last_commit_time":"17-06-07 17:50:59","ip":"无","sub_domain":"bbs.kq88.com","location":"","origin":"接口"},{"last_commit_time":"17-06-07 17:50:59","ip":"无","sub_domain":"010.kq88.com","location":"","origin":"接口"},{"last_commit_time":"17-06-07 17:50:59","ip":"无","sub_domain":"0510.kq88.com","location":"","origin":"接口"},{"last_commit_time":"17-06-07 17:50:59","ip":"无","sub_domain":"chat.kq88.com","location":"","origin":"接口"},{"last_commit_time":"17-06-07 17:50:59","ip":"无","sub_domain":"member.kq88.com","location":"","origin":"接口"},{"last_commit_time":"17-06-07 17:50:59","ip":"无","sub_domain":"bbss.kq88.com","location":"","origin":"接口"},{"last_commit_time":"17-06-07 17:50:59","ip":"无","sub_domain":"www1.kq88.com","location":"","origin":"接口"},{"last_commit_time":"17-06-07 17:50:59","ip":"无","sub_domain":"xhws.kq88.com","location":"","origin":"接口"},{"last_commit_time":"17-06-07 17:50:59","ip":"无","sub_domain":"jg.kq88.com","location":"","origin":"接口"},{"last_commit_time":"17-06-07 17:50:59","ip":"无","sub_domain":"job.kq88.com","location":"","origin":"接口"},{"last_commit_time":"17-06-07 17:50:59","ip":"无","sub_domain":"survey.kq88.com","location":"","origin":"接口"},{"last_commit_time":"17-06-07 17:50:59","ip":"无","sub_domain":"class.kq88.com","location":"","origin":"接口"},{"last_commit_time":"17-06-07 17:50:59","ip":"无","sub_domain":"down.kq88.com","location":"","origin":"接口"},{"last_commit_time":"17-06-07 17:50:59","ip":"无","sub_domain":"gd.kq88.com","location":"","origin":"接口"},{"last_commit_time":"17-06-07 17:50:59","ip":"无","sub_domain":"h.kq88.com","location":"","origin":"接口"},{"last_commit_time":"17-06-07 17:50:59","ip":"无","sub_domain":"d.kq88.com","location":"","origin":"接口"},{"last_commit_time":"17-06-07 17:50:59","ip":"无","sub_domain":"search.kq88.com","location":"","origin":"接口"},{"last_commit_time":"17-06-07 17:50:59","ip":"无","sub_domain":"www1c20.kq88.com","location":"","origin":"接口"},{"last_commit_time":"17-06-07 17:50:59","ip":"123.125.112.110","sub_domain":"m.zs.kq88.com","location":"CN","origin":"接口"},{"last_commit_time":"17-06-07 17:50:59","ip":"无","sub_domain":"z.kq88.com","location":"","origin":"接口"},{"last_commit_time":"17-06-07 17:50:59","ip":"无","sub_domain":"wx.kq88.com","location":"","origin":"接口"},{"last_commit_time":"17-06-07 17:50:59","ip":"无","sub_domain":"vita.kq88.com","location":"","origin":"接口"},{"last_commit_time":"17-06-07 17:50:59","ip":"无","sub_domain":"m.px.kq88.com","location":"","origin":"接口"},{"last_commit_time":"17-06-07 17:50:59","ip":"无","sub_domain":"tesco.kq88.com","location":"","origin":"接口"}]}

    def example_get_domain_state(self, response_json):
        for per_sub_domain_json in response_json['sub_domains']:
            per_sub_domain = per_sub_domain_json['sub_domain']
            api_url = 'http://' + config.domain_detect_api_host + '/detect_domain/' + per_sub_domain
            resp = requests.get(api_url)
            result_json = {
                'success': 1,
                'domain': per_sub_domain,
                'type': 'domain_state'
            }
            result_json.update(resp.json())
            self.write_message(result_json)


class ResultWebSocketRealHandler(BaseWebSocketHandler):
    """获取结果的接口"""

    executor = ThreadPoolExecutor(max_workers=1000)

    connections = set()

    def __init__(self, application, request, **kwargs):
        super(ResultWebSocketRealHandler, self).__init__(application, request, **kwargs)
        self.closed = False
        self.domain_state_queue = Queue()

        self.domain_state_still_work = False
        self.domain_state_should_stop = False
        self.domain_state_thread = threading.Thread(target=self.get_domain_state_looper)
        self.domain_state_thread.setDaemon(True)
        self.domain_state_thread.start()

    def open(self):
        self.connections.add(self)
        # self.write_message("Conn!")

    def check_origin(self, origin):
        logging.info('check_origin: {}'.format(origin))
        return True

    @run_on_executor
    def on_message(self, message):
        if self.closed:
            return

        print(".......... 收到信息 begin ..........\n")
        print(message)
        print(".......... 收到信息 end ..........\n\n\n\n\n\n\n")

        logging.info('id: {}'.format(id(self)))
        request_json = json.loads(message)

        if 'type' in request_json.keys():
            if request_json['type'] == 'scan':
                ''' 这是一个端口扫描请求 '''

                print("这是一个端口扫描请求")
                self.create_scan_event(request_json)
            elif request_json['type'] == 'scan_finish_notify':
                ''' 这是一个端口扫描完毕的通知请求 '''

                print("这是一个端口扫描完毕的通知请求")
                eventid = request_json['eventid']
                res = PortScanEventService(self.db).get_info_by_id(eventid)
                self.emit_scan_info(res)
            return

        if request_json.get('domain'):
            target_domain = request_json.get('domain')
            logging.info(target_domain)
            self.get_ip_history(target_domain)
            self.get_domain_detail(target_domain)
            self.get_sub_domains(target_domain)
            # if response_json:
            #     self.write_message(response_json)
            #     self.get_domain_state(response_json)
        while not self.domain_state_queue.empty() or self.domain_state_still_work:
            time.sleep(0.1)
        self.domain_state_should_stop = True
        self.write_message({'type': 'task_over'})
        # self.closed = True
        # self.close()

    def on_close(self):
        self.closed = True
        self.domain_state_should_stop = True
        logging.info('on close')
        self.connections.remove(self)
        self.db.close()

    def create_scan_event(self,request_json):
        ip = request_json['ip']
        domain = request_json['domain']
        port_scan_event_service = PortScanEventService(self.db)
        res = port_scan_event_service.get_info_recently(ip,domain)
        if res:
            self.emit_scan_info(res)
        else:
            port_scan_event_service.create_event(ip,domain)

    def emit_scan_info(self,res):
        if not res:
            return
        res['type'] = 'scan_info'
        [con.write_message(res) for con in self.connections]

    def get_domain_detail(self, target_domain):
        """获取域名详情,NS 和 MX 记录."""
        response_json = {
            'type': 'domain_detail',
            'domain': target_domain
        }
        try:
            response = requests.get('http://' + config.domain_detect_api_host + '/dig_a/' + target_domain)
            ips = response.json()['data']
            logging.warning(ips)
            response_json['other_site'] = [ReverseIpLookUp(i).run() for i in ips]
            while True:
                # db_session = DBSession()
                target_domain_entity = self.db.query(Domain).filter(Domain.domain == target_domain).first()
                self.db.close()
                if target_domain_entity is not None:
                    if not response_json.get('ns_records') and target_domain_entity.ns_records:
                        response_json['ns_records'] = json.loads(target_domain_entity.ns_records)
                    if not response_json.get('mx_records') and target_domain_entity.mx_records:
                        response_json['mx_records'] = json.loads(target_domain_entity.mx_records)
                    if not response_json.get('whois') and target_domain_entity.domain_whois:
                        response_json['whois'] = json.loads(target_domain_entity.domain_whois)
                    if 'ns_records' in response_json and 'mx_records' in response_json and 'whois' in response_json:
                        break
                time.sleep(1)
            logging.info(response_json)
            self.write_message(response_json)
        except Exception as e:
            logging.error(traceback.format_exc())
            logging.error(e)
            self.write_message(response_json)

    def get_ip_history(self, target_domain):
        """获取历史解析记录."""
        self.write_message({
            'type': 'ip_history',
            'domain': target_domain,
            'history': get_history_ip(target_domain)['data']
        })

    @gen.coroutine
    def get_sub_domains(self, target_domain):
        """获取子域名."""
        # db_session = None
        try:
            # db_session = DBSession()
            target_domain_entity = self.db.query(Domain).filter(Domain.domain == target_domain).one()

            target_domain_id = target_domain_entity.id
            offset = 0
            limit = 30
            max_count = 500
            is_finished = False
            while not is_finished and not self.closed and offset < max_count:
                # db_session = DBSession()
                task_record_entity = self.db.query(TaskRecords).filter(TaskRecords.keywords == target_domain).one()
                task_state = task_record_entity.state

                target_sub_domains = self.db.query(SubDomainResult).filter(SubDomainResult.domain_id == target_domain_id).offset(offset).limit(limit).all()
                self.db.close()
                logging.info('domain_id: {}, offset: {}, limit: {}, type: {}'.format(target_domain_id, offset, limit, target_sub_domains))
                # return
                response_json = {
                    'type': 'sub_domain',
                    'domain': target_domain,
                    'sub_domains': []
                }
                for per_sub_domain in target_sub_domains:
                    response_json['sub_domains'].append({
                        'sub_domain': per_sub_domain.subdomain,
                        'ip': per_sub_domain.ip,
                        'location': ','.join([get_location_abbr(i) for i in per_sub_domain.location.split(',')]),
                        'origin': per_sub_domain.origin,
                        'last_commit_time': per_sub_domain.last_commit_time.strftime('%Y-%m-%d %H:%M:%S')
                    })

                real_query_count = len(response_json['sub_domains'])

                if task_state == 2:
                    if real_query_count != 0:
                        self.write_message(response_json)
                        self.get_domain_state(response_json)
                    if real_query_count != limit:
                        break
                else:
                    if real_query_count != 0:
                        self.write_message(response_json)
                        self.get_domain_state(response_json)
                offset += real_query_count

                yield gen.Task(
                    ioloop.IOLoop.current().add_timeout,
                    deadline=datetime.timedelta(seconds=0.5))
        except Exception as e:
            logging.error(traceback.format_exc())
            logging.error(e)
            yield None
        finally:
            # if db_session is not None:
            #     db_session.close()
            pass

    def get_domain_state(self, response_json):
        """将域名提交到自身的队列, 准备探测状态."""
        for per_sub_domain_json in response_json['sub_domains']:
            per_sub_domain = per_sub_domain_json['sub_domain']
            # api_url = 'http://' + config.domain_detect_api_host + '/detect_domain/' + per_sub_domain
            # resp = requests.get(api_url)
            # result_json = {
            #     'success': 1,
            #     'domain': per_sub_domain,
            #     'type': 'domain_state'
            # }
            # result_json.update(resp.json())
            # self.write_message(result_json)
            self.domain_state_queue.put(per_sub_domain)

    def get_domain_state_looper(self):
        """异步线程, 用于探测域名状态."""
        session = self.db
        while not self.domain_state_should_stop:
            try:
                domain = self.domain_state_queue.get(timeout=0.1)
                logging.info(domain)
                if domain:
                    sub_domain_entity = session.query(SubDomainResult).filter(SubDomainResult.subdomain == domain).first()

                    response_json = {
                        'type': 'domain_state',
                        'domain': domain,
                        'success': 1
                    }
                    if sub_domain_entity:
                        if sub_domain_entity.state:
                            response_json['state'] = int(sub_domain_entity.state)
                        else:
                            self.domain_state_still_work = True
                            api_url = 'http://' + config.domain_detect_api_host + '/detect_domain/' + domain
                            resp_json = requests.get(api_url).json()
                            response_json.update(resp_json)
                            session.query(SubDomainResult).filter(SubDomainResult.id == sub_domain_entity.id).update({
                                'state': resp_json['state']
                            })
                            session.commit()
                        logging.info(response_json)
                        self.write_message(response_json)
                    session.commit()
            except Empty:
                pass
            except Exception as e:
                logging.error(traceback.format_exc())
                logging.error(e)
            self.domain_state_still_work = False


class IpReverseWebSocketHandler(BaseWebSocketHandler):

    executor = ThreadPoolExecutor(max_workers=1000)

    def __init__(self, application, request, **kwargs):
        super(IpReverseWebSocketHandler, self).__init__(application, request, **kwargs)
        self.reverse_ip_service = ReverseIpService(self.db)

    def check_origin(self, origin):
        return True

    @run_on_executor
    def on_message(self, message):
        request_json = json.loads(message)
        if 'ip' in request_json:
            target_ip = request_json['ip']
            self.write_message(self.reverse_ip_service.reverse_ip(target_ip))


class WhoisHandler(BaseHandler):
    """查询 Whois 信息借接口"""

    def get(self, *args, **kwargs):
        target_domain = self.get_argument('domain', None)

        result_json = {'success': 0}
        if target_domain:
            target_domain = misc.parse_domain_simple(target_domain)
            if misc.is_valid_domain(target_domain):
                sql = '''
                    SELECT
                        `domain_whois`
                    FROM
                        `system_domain`
                    WHERE
                        `domain` = %s
                '''
                try:
                    rs = db.query(sql, target_domain)
                    rr = rs[0]['domain_whois']
                    result_json['whois'] = json.loads(rr) if rr else {}
                    result_json['domain'] = target_domain
                    result_json['success'] = 1
                except Exception as e:
                    logging.error('从数据库查询 whois 信息失败.')
                    logging.error(traceback.format_exc())
                    logging.error(str(e))
            else:
                logging.debug('获取 whois 失败, 输入域名不合法.')
        else:
            logging.debug('查询 whois 失败, 没有输入域名.')
        self.write(json.dumps(result_json))


class AddBruteTaskHandler(tornado.web.RequestHandler):
    """添加爆破任务接口"""

    def post(self, *args, **kwargs):
        target_domain = self.get_argument('domain', None)

        result_json = {'success': 0}
        if target_domain:
            target_domain = misc.parse_domain_simple(target_domain)
            if misc.is_valid_domain(target_domain):
                task_state = get_task_state(target_domain)
                logging.debug('任务状态: {0}'.format(task_state))
                if task_state == 2:
                    result_json['success'] = int(push_brute_task(target_domain))
        self.write(json.dumps(result_json))


class BruteProgressHandler(BaseHandler):

    def get(self, *args, **kwargs):
        result_json = {'success': 0}

        target_domain = self.get_argument('domain')

        try:
            task_id = get_task_id(target_domain)
            task_process_key = '{}__brute_detail_{}'.format(project_name, str(task_id))
            result_json['total'] = int(redis_cursor.hget(task_process_key, 'total'))
            result_json['checked'] = int(redis_cursor.hget(task_process_key, 'checked'))
            result_json['found'] = int(redis_cursor.hget(task_process_key, 'found'))
            result_json['success'] = 1
        except Exception as e:
            logging.error(traceback.format_exc())
            logging.error(e)

        self.write(json.dumps(result_json))
