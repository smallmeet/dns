#!/usr/bin/env python 
# -*- coding: utf-8 -*-
""" create at 14/06/2017 """
import logging
import traceback

from utils import utils

__author__ = 'binbin'

import datetime
from models import db_session, DBSession, Domain, TaskRecords, User
from models import SystemDomains
from models import SystemIps
from models import SystemEvents
import json

from utils.config import config, redis_cursor

project_name = config.project_name
task_next_id_key = project_name + '__sp'
running_tasks_key = project_name + '__tasks'
task_queue_key = project_name + '__task_queue'
task_detail_key_prefix = project_name + '__task_detail_'


class PortScanEventService():

    def __init__(self):
        '''
        这个用来获取端口扫描信息的service类
        :return:
        '''

        self.MIN_SYNC_TIME_DELAY = datetime.timedelta(hours=6)

    def fetch_wait_events(self):
        session = DBSession()
        res = session.query(SystemEvents).filter(SystemEvents.state < 2).all()
        session.close()
        if not res:
            return []
        return res

    def _get_min_sync_time(self):
        '''
        获取最早能够接受的同步时间,再早的就不需要了,重新爬
        :return:
        '''
        return datetime.datetime.now() - self.MIN_SYNC_TIME_DELAY

    def sync_ip_web_info(self,ip,web_info):
        ip_info = db_session.query(SystemIps).filter(SystemIps.ip == SystemIps.ip_to_int(ip)).first()
        if not ip_info:
            ip_info = SystemIps(ip=ip,web_info=web_info,create_time = datetime.datetime.now())
        else:
            ip_info.web_info = web_info

        db_session.add(ip_info)
        db_session.commit()

    def sync_ip_port_info(self,ip,port_info):
        ip_info = db_session.query(SystemIps).filter(SystemIps.ip == SystemIps.ip_to_int(ip)).first()
        if not ip_info:
            ip_info = SystemIps(ip=ip,port_info=port_info,create_time = datetime.datetime.now())
        else:
            ip_info.port_info = port_info

        db_session.add(ip_info)
        db_session.commit()

    def sync_cms_info(self,domain,cms_info):
        domain_info = db_session.query(SystemDomains).filter(SystemDomains.domain == domain).first()
        if not domain_info:
            domain_info = SystemDomains(domain=domain,cms=cms_info,create_time=datetime.datetime.now())
        else:
            domain_info.cms = cms_info

        db_session.add(domain_info)
        db_session.commit()

    def get_info_by_id(self,_eventid):
        system_event = db_session.query(SystemEvents).filter(SystemEvents.id == _eventid).first()
        if not system_event:
            return None

        result = {}

        domain_info = db_session.query(SystemDomains).filter(SystemDomains.domain == system_event.domain).first()

        if domain_info:
            if not domain_info.cms:
                domain_info.cms = ''
            result['domain_info']={'domain':domain_info.domain,'cms':json.loads(domain_info.cms),'sync_time':domain_info.sync_time.strftime("%Y-%m-%d-%H")}


        ip_info = db_session.query(SystemIps).filter(SystemIps.ip == system_event.ip).first()

        if ip_info:
            if not ip_info.web_info:
                ip_info.web_info = ""

            result['ip_info'] = {'ip':{'ip':ip_info.get_ip(),'web_info':json.loads(ip_info.web_info),'port_info':ip_info.port_info}}

        return result

    def get_info_recently(self,_ip,_domain):
        '''
        获取域名信息和ip信息,注意这里我需要指定最小sync时间
        :param _ip:
        :param _domain:
        :return:
        '''
        min_sync_time = self._get_min_sync_time()

        result = {}

        domain_info = db_session.query(SystemDomains).filter(SystemDomains.sync_time > min_sync_time).filter(SystemDomains.domain == _domain).first()
        ip_info = db_session.query(SystemIps).filter(SystemIps.ip == _ip).filter(SystemIps.ip == _ip).first()

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
        system_event = db_session.query(SystemEvents).filter(SystemEvents.id == _eventid).first()
        if not system_event:
            return

        system_event.state = state
        system_event.finish_time = datetime.datetime.now()
        db_session.add(system_event)

        ip = system_event.get_ip()
        domain = system_event.domain

        domain_info = db_session.query(SystemDomains).filter(SystemDomains.domain == domain).first()
        if domain_info:
            domain_info.sync_time = datetime.datetime.now()
            db_session.add(domain_info)
        ip_info = db_session.query(SystemIps).filter(SystemIps.ip == ip).first()
        if ip_info:
            ip_info.sync_time = datetime.datetime.now()
            db_session.add(ip_info)

        db_session.commit()

        # TODO 通过websocket通知获取信息

    def create_event(self,_ip,_domain):
        '''
        创建一个事件
        :return:
        '''
        now = datetime.datetime.now()
        system_events = SystemEvents(ip=_ip,domain=_domain,state=0,type_id=3,create_time=now,is_delete=0)
        db_session.add(system_events)
        db_session.commit()


class RootDomainService(object):
    """根域名 Service"""

    def create_domain(self, domain):
        session = DBSession()
        domain_query_runner = session.query(Domain).filter(Domain.domain == domain)
        if domain_query_runner.count() == 0:
            domain_entity = Domain(domain=domain)
            session.add(domain_entity)
            session.commit()
        session.close()


class UserService(object):
    """用户 Service"""

    def get_user(self, username):
        session = DBSession()
        target_user_entity = session.query(User).filter(User.username == username).one_or_none()
        session.close()
        return target_user_entity

    def save(self, user_entity):
        if isinstance(user_entity, UserService):
            session = DBSession()
            session.add(user_entity)
            session.commit()
            session.close()

class TaskRecordService(object):
    """任务 Service"""

    def create_task(self, task_params):
        """创建任务, 并推入队列"""
        session = DBSession()

        new_task_entity = TaskRecords(keywords=task_params['keywords'], create_time=utils.now(),
                                      finish_time=utils.original_time())
        session.add(new_task_entity)
        session.commit()
        session.close()

        session = DBSession()
        new_task_entity = session.query(TaskRecords)\
            .filter(TaskRecords.keywords == task_params['keywords'])\
            .order_by(TaskRecords.id.desc())\
            .limit(1)\
            .one()
        new_task_id = new_task_entity.id

        self.push_task(new_task_id, task_params)

        session.close()

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
        session = DBSession()
        target_task_entity = session.query(TaskRecords).filter(TaskRecords.keywords == keywords)\
            .limit(1).one_or_none()
        session.close()

        if target_task_entity is None:
            return -1
        return target_task_entity.state


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

    print(TaskRecordService().get_task_state('asdasd.com'))
