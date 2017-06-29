#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import traceback

from service import UserService
from utils.misc import next_uuid, img_create
import tornado.web
import json
import sys
import datetime
import os
from handlers.base import BaseHandler

sys.path.append('../')
from utils.config import config, db, redis_cursor
from utils.misc import parse_domain_simple, is_valid_domain, now, get_ip_list, str2bool

pre_system = config.pre_system
mysql_cursor = db
names = locals()

project_name = config.project_name
task_next_id_key = project_name + '__sp'
running_tasks_key = project_name + '__tasks'
task_queue_key = project_name + '__task_queue'
task_detail_key_prefix = project_name + '__task_detail_'


class SearchHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self, *args, **kwargs):
        history = list()
        cookie_username = self.get_secure_cookie(pre_system + 'username')

        group_id = db.query('SELECT `group_id` FROM `system_admin_user` WHERE `username` = %s', cookie_username)[0]['group_id']
        if group_id == 0:
            self.redirect('/admin')
            return

        if cookie_username:
            # sql = 'select avatar from system_admin_user WHERE username=%s'
            # ret = db.query(sql, cookie_username)[0]['avatar']
            # if ret != '':
            #     filename = ret
            # else:
            #     filename = next_uuid()
            # filename_url = 'static/img/avatar/{0}.png'.format(filename)
            # if not os.path.exists(filename_url):
            #     if img_create(filename):
            #         sql = '''
            #                 UPDATE `subdomain`.`system_admin_user` SET `avatar`=%s WHERE username=%s;
            #
            #                 '''
            #         ret = db.execute(sql, filename, cookie_username)
            #         if ret:
            #             pass
            #     else:
            #         filename = 'icon'
            # TODO: 重新建一张历史表
            # sql = '''select domain from system_task_records
            #          where user_id=
            #          (select id
            #          from system_admin_user
            #          where username=%s)
            #          order by query_time
            #          limit 10
            #          ;
            #        '''
            # ret = db.query(sql, cookie_username)
            # if ret:
            #     for i in ret:
            #         history.append(i['domain'])

            # try:
            #     # 多表链接查询,查询用户搜索过的域名id 以及子域名数量
            #     sql = '''
            #                        select domain_id,count(subdomain) as cot
            #                        from system_subdomain_result as r where domain_id in
            #                         (select id from system_domain where domain in
            #                         (select domain from system_task_records
            #                         where user_id =
            #                         (select id from system_admin_user where username=%s)))
            #                         group by r.domain_id;
            #                       '''
            #     ret = mysql_cursor.query(sql, cookie_username)
            # except:
            #     pass
            # if ret:
            #     num = len(ret)  # 结果条数
            #     domain_list1 = list()
            #     for i in range(num):
            #         domain_id = ret[i]['domain_id']
            #         subdomain_count = ret[i]['cot']
            #         domain_list1.append(domain_id)
            #         names['x%s' % i] = dict()
            #         names['x%s' % i]['domain_id'] = domain_id
            #         names['x%s' % i]['count'] = subdomain_count
            #
            #     t = tuple(domain_list1)
            #     sql = '''
            #                 select r.domain,create_time
            #                 from system_task_records r,system_domain d
            #                 where r.domain=d.domain and d.id
            #                 in %s;
            #                 '''
            #     try:
            #         ret2 = mysql_cursor.query(sql, t)
            #         for i in range(num):
            #             names['x%s' % i]['domain'] = ret2[i]['domain']
            #             names['x%s' % i]['create_time'] = datetime.datetime.strftime(ret2[i]['create_time'],
            #                                                                          '%Y-%m-%d %H:%M:%S')
            #             history.append(names['x%s' % i])
            #     except:
            #         pass
            self.render('home.html', history=history, username=cookie_username)
            # self.render('login.html')

        else:
            self.render('login.html')

    def post(self, *args, **kwargs):
        pass


class SearchNewHandler(BaseHandler):

    def __init__(self, application, request, **kwargs):
        super(SearchNewHandler, self).__init__(application, request, **kwargs)
        self.user_service = UserService(self.db)

    @tornado.web.authenticated
    def get(self, *args, **kwargs):
        current_username = self.get_secure_cookie(pre_system + 'username')

        current_username_entity = self.user_service.get_user(current_username)
        group_id = current_username_entity.group_id
        avatar = current_username_entity.avatar
        # if group_id == 0:
        #     self.redirect('/admin')
        #     return

        if not avatar:
            avatar = next_uuid()
        filename_url = 'static/img/avatar/{0}.png'.format(avatar)
        if not os.path.exists(filename_url):
            if img_create(avatar):
                current_username_entity.avatar = avatar
                self.user_service.save(current_username_entity)
            else:
                logging.warning('创建头像失败')
                avatar = 'icon'
        self.render('home_new.html', avatar=avatar, username=current_username)
