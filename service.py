#!/usr/bin/env python 
# -*- coding: utf-8 -*-
""" create at 14/06/2017 """


__author__ = 'binbin'

import sys
import datetime
import logging
import traceback
import requests

from lxml import etree

from models import Domain, TaskRecords, User, SubDomainResult
from models import SystemDomains
from models import SystemIps
from models import SystemEvents
import json
sys.path.append('../')

from utils import misc
from utils.reverse_ip_lookup import ReverseIpLookUp
from utils.config import config, redis_cursor

project_name = config.project_name
task_next_id_key = project_name + '__sp'
running_tasks_key = project_name + '__tasks'
task_queue_key = project_name + '__task_queue'
task_detail_key_prefix = project_name + '__task_detail_'


class BaseService(object):

    def __init__(self, db):
        super(BaseService, self).__init__()
        self.db = db


class PortScanEventService(BaseService):

    def __init__(self, db):
        """
        这个用来获取端口扫描信息的service类
        :return:
        """
        super(PortScanEventService, self).__init__(db)
        self.MIN_SYNC_TIME_DELAY = datetime.timedelta(hours=6)

    def fetch_wait_events(self):
        res = self.db.query(SystemEvents).filter(SystemEvents.state < 2).all()
        self.db.close()
        if not res:
            return []
        return res

    def _get_min_sync_time(self):
        """
        获取最早能够接受的同步时间,再早的就不需要了,重新爬
        :return:
        """
        return datetime.datetime.now() - self.MIN_SYNC_TIME_DELAY

    def sync_ip_web_info(self,ip,web_info):
        ip_info = self.db.query(SystemIps).filter(SystemIps.ip == SystemIps.ip_to_int(ip)).first()
        if not ip_info:
            ip_info = SystemIps(ip=ip,web_info=web_info,create_time = datetime.datetime.now())
        else:
            ip_info.web_info = web_info

        self.db.add(ip_info)
        self.db.commit()

    def sync_ip_port_info(self,ip,port_info):
        ip_info = self.db.query(SystemIps).filter(SystemIps.ip == SystemIps.ip_to_int(ip)).first()
        if not ip_info:
            ip_info = SystemIps(ip=ip,port_info=port_info,create_time = datetime.datetime.now())
        else:
            ip_info.port_info = port_info

        self.db.add(ip_info)
        self.db.commit()

    def sync_cms_info(self,domain,cms_info):
        domain_info = self.db.query(SystemDomains).filter(SystemDomains.domain == domain).first()
        if not domain_info:
            domain_info = SystemDomains(domain=domain,cms=cms_info,create_time=datetime.datetime.now())
        else:
            domain_info.cms = cms_info

        self.db.add(domain_info)
        self.db.commit()

    def get_info_by_id(self,_eventid):
        system_event = self.db.query(SystemEvents).filter(SystemEvents.id == _eventid).first()
        if not system_event:
            return None

        result = {}

        domain_info = self.db.query(SystemDomains).filter(SystemDomains.domain == system_event.domain).first()

        if domain_info:
            if not domain_info.cms:
                domain_info.cms = ''
            result['domain_info']={'domain':domain_info.domain,'cms':json.loads(domain_info.cms),'sync_time':domain_info.sync_time.strftime("%Y-%m-%d-%H")}


        ip_info = self.db.query(SystemIps).filter(SystemIps.ip == system_event.ip).first()

        if ip_info:
            if not ip_info.web_info:
                ip_info.web_info = ""

            result['ip_info'] = {'ip':{'ip':ip_info.get_ip(),'web_info':json.loads(ip_info.web_info),'port_info':ip_info.port_info}}

        self.db.close()
        return result

    def get_info_recently(self,_ip,_domain):
        """
        获取域名信息和ip信息,注意这里我需要指定最小sync时间
        :param _ip:
        :param _domain:
        :return:
        """
        min_sync_time = self._get_min_sync_time()

        result = {}

        domain_info = self.db.query(SystemDomains).filter(SystemDomains.sync_time > min_sync_time).filter(SystemDomains.domain == _domain).first()
        ip_info = self.db.query(SystemIps).filter(SystemIps.ip == _ip).filter(SystemIps.ip == _ip).first()
        self.db.close()

        if not domain_info or not ip_info:
            return None

        if not domain_info.cms:
            domain_info.cms = ''
            result['domain_info']={'domain':domain_info.domain,'cms':json.loads(domain_info.cms),'sync_time':domain_info.sync_time.strftime("%Y-%m-%d-%H")}

        if not ip_info.web_info:
            ip_info.web_info = ""

            result['ip_info'] = {'ip':{'ip':ip_info.get_ip(),'web_info':json.loads(ip_info.web_info),'port_info':ip_info.port_info}}

        return result

    def finish_event(self,_eventid,state):
        system_event = self.db.query(SystemEvents).filter(SystemEvents.id == _eventid).first()
        if not system_event:
            return

        system_event.state = state
        system_event.finish_time = datetime.datetime.now()
        self.db.add(system_event)

        ip = system_event.get_ip()
        domain = system_event.domain

        domain_info = self.db.query(SystemDomains).filter(SystemDomains.domain == domain).first()
        if domain_info:
            domain_info.sync_time = datetime.datetime.now()
            self.db.add(domain_info)
        ip_info = self.db.query(SystemIps).filter(SystemIps.ip == ip).first()
        if ip_info:
            ip_info.sync_time = datetime.datetime.now()
            self.db.add(ip_info)

        self.db.commit()

        # TODO 通过websocket通知获取信息

    def create_event(self,_ip,_domain):
        """
        创建一个事件
        :return:
        """
        now = datetime.datetime.now()
        system_events = SystemEvents(ip=_ip,domain=_domain,state=0,type_id=3,create_time=now,is_delete=0)
        self.db.add(system_events)
        self.db.commit()


class RootDomainService(BaseService):
    """根域名 Service"""

    def create_domain(self, domain):
        domain_query_runner = self.db.query(Domain).filter(Domain.domain == domain)
        if domain_query_runner.count() == 0:
            domain_entity = Domain(domain=domain)
            self.db.add(domain_entity)
            self.db.commit()


class UserService(BaseService):
    """用户 Service"""

    def get_user(self, username):
        target_user_entity = self.db.query(User).filter(User.username == username).one_or_none()
        self.db.close()
        return target_user_entity

    def save(self, user_entity):
        if isinstance(user_entity, UserService):
            self.db.add(user_entity)
            self.db.commit()


class TaskRecordService(BaseService):
    """任务 Service"""

    def create_task(self, task_params):
        """创建任务, 并推入队列"""
        new_task_entity = TaskRecords(keywords=task_params['keywords'], create_time=misc.now(),
                                      finish_time=misc.original_time())
        self.db.add(new_task_entity)
        self.db.commit()

        new_task_entity = self.db.query(TaskRecords)\
            .filter(TaskRecords.keywords == task_params['keywords'])\
            .order_by(TaskRecords.id.desc())\
            .limit(1)\
            .one()
        new_task_id = new_task_entity.id

        self.push_task(new_task_id, task_params)
        self.db.close()

    def push_task(self, new_task_id, task_params):
        """将任务 push 到队列"""
        try:
            current_task_id = new_task_id

            task_detail_key = '%s%s' % (task_detail_key_prefix, current_task_id)
            for key in task_params:
                redis_cursor.hset(task_detail_key, key, task_params[key])
            redis_cursor.rpush(task_queue_key, current_task_id)
            return True
        except Exception as e:
            logging.error(traceback.format_exc())
            logging.error('push 任务失败: %s' % str(e))
        return False

    def get_task_state(self, keywords):
        target_task_entity = self.db.query(TaskRecords).filter(TaskRecords.keywords == keywords)\
            .limit(1).one_or_none()
        self.db.close()

        if target_task_entity is None:
            return -1
        return target_task_entity.state


class ReverseIpService(BaseService):

    @staticmethod
    def try_decode(content):
        try:
            return unicode(content, 'gb2312')
        except UnicodeDecodeError:
            pass
        try:
            return unicode(content, 'gbk')
        except UnicodeDecodeError:
            pass
        try:
            return unicode(content, 'gb18030')
        except UnicodeDecodeError:
            pass
        return ''

    def reverse_ip(self, ip):
        reverse_ip_data = ReverseIpLookUp(ip).run()

        sub_domain_results = self.db.query(SubDomainResult).filter(SubDomainResult.ip.like('%{}%'.format(ip))).all()

        for i in sub_domain_results:
            for j in reverse_ip_data[ip]:
                if j['domain'] == i.subdomain:
                    continue
            try:
                url = 'http://{}'.format(i.subdomain)
                resp = requests.get(url)
                content_bytes = resp.content
                if resp.encoding.lower() != 'utf-8':
                    html = self.try_decode(content_bytes)
                else:
                    html = resp.text
                root = etree.HTML(html)
                titles = root.xpath('.//title/text()')
                title = titles[0] if titles else ''
                print(title)
                reverse_ip_data[ip].append({
                    'url': url,
                    'domain': i.subdomain,
                    'title': title
                })
            except Exception as e:
                pass
        self.db.close()
        # utils.remove_repeat_domain(reverse_ip_data[ip])
        return reverse_ip_data


if __name__ == "__main__":
    # PortScanEventService().create_event("47.93.87.52",'www.jinwulab.com')
    import json
    #PortScanEventService().sync_ip_port_info("47.93.87.52",json.dumps({"dd":"dd"}))
    # PortScanEventService().sync_cms_info("www.jinwulab.com",json.dumps({"dd":"dd"}))
    # PortScanEventService().finish_event(4,2)

    # RootDomainService().create_domain('asd.com')

    # TaskRecordService().create_task({
    #     'keywords': 'asdasd.com',
    #     'is_brute': 0
    # })

    # print(TaskRecordService().get_task_state('asdasd.com'))
    print(json.dumps(ReverseIpService().reverse_ip('221.228.213.94'), indent=2))
