#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import traceback

import tornado.web

from handlers.base import BaseHandler
from models import DBSession, User, TaskRecords, Domain
from service import TaskRecordService, UserService, RootDomainService
from utils.config import config, pre_system, redis_cursor
from utils import utils

project_name = config.project_name
task_next_id_key = project_name + '__sp'
running_tasks_key = project_name + '__tasks'
task_queue_key = project_name + '__task_queue'
task_detail_key_prefix = project_name + '__task_detail_'


class ResultNewHandler(BaseHandler):
    """搜索结果页"""

    def __init__(self, application, request, **kwargs):
        super(ResultNewHandler, self).__init__(application, request, **kwargs)
        self.user_service = UserService()
        self.domain_service = RootDomainService()
        self.task_record_service = TaskRecordService()

    @tornado.web.authenticated
    def get(self, *args, **kwargs):
        current_username = self.get_secure_cookie(pre_system + 'username')

        current_user_entity = self.user_service.get_user(current_username)
        avatar = current_user_entity.avatar


        # 取参数
        target_domain = self.get_argument('content', '')
        dictionary = utils.str2bool(self.get_argument('dictionary', 'false'))


        # 处理域名
        target_domain = utils.parse_domain_simple(target_domain)
        logging.debug('target domain is: ' + target_domain)
        if not utils.is_valid_domain(target_domain):
            self.redirect('/search_new')
            return

        self.domain_service.create_domain(target_domain)
        # 查询任务是否存在
        task_state = self.task_record_service.get_task_state(target_domain)

        # 如果任务不存在, 则创建任务
        if -1 == task_state:
            logging.debug('任务不存在, 创建任务.')
            task_params = {
                'keywords': target_domain,
                'type': 'search_domain',
                'is_brute': int(dictionary)
            }
            TaskRecordService().create_task(task_params)
            logging.debug('创建任务 over.')
        elif 0 == task_state:
            logging.debug('正在排队')
        elif 1 == task_state:
            logging.debug('正在运行')
        elif 2 == task_state:
            logging.debug('已经结束')
        self.render('result_new.html', avatar=avatar, username=current_username, target_domain=target_domain)


class ReverseIpLookUpNewHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self, *args, **kwargs):
        ip = self.get_argument('ip', '')
        self.render('ip.html', ip=ip)
