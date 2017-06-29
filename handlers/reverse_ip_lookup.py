#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging
import traceback

import datetime

from handlers.base import BaseHandler
from utils import misc
from utils.config import db, config, redis_cursor

pre_system = config.pre_system

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
                `system_task_records`.`keywords` = %s
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


def add_new_task_state(task_id, target_ip):
    try:
        logging.info('task id: {}'.format(task_id))
        db.insert('''
                INSERT INTO
                    `system_task_records` (`id`, `keywords`, `create_time`, `finish_time`, `state`)
                VALUES
                    (%s, %s, %s, %s, %s)''',
                  task_id,
                  target_ip,
                  misc.now(),
                  misc.original_time(),
                  '0')
    except Exception as e:
        logging.error('添加任务状态失败')
        logging.error(traceback.format_exc())
        logging.error('Caught an error when insert a new task state: %s' % str(e))


def push_task(target_ip, **kwargs):
    try:
        current_task_id = redis_cursor.incr(task_next_id_key)
        # 向数据库更新任务状态
        add_new_task_state(current_task_id, target_ip)
        # 将任务 push 到队列
        task_detail_key = '%s%s' % (task_detail_key_prefix, current_task_id)
        redis_cursor.hset(task_detail_key, 'keywords', target_ip)
        redis_cursor.hset(task_detail_key, 'type', 'reverse_ip_lookup')
        redis_cursor.rpush(task_queue_key, current_task_id)
        return True
    except Exception as e:
        logging.error(traceback.format_exc())
        logging.error('Caught an error when insert a new task: %s' % str(e))
    return False


def get_task_id(keywords):
    try:
        rs = db.query("SELECT `id` FROM `system_task_records` WHERE `keywords` = %s ORDER BY `create_time` DESC LIMIT 1", keywords)
        return rs[0]['id']
    except Exception as e:
        logging.error(e)
    return -1


def try_restart_task(keywords):
    rs = db.query("SELECT `id`, `state`, `finish_time` FROM `system_task_records` WHERE `keywords` = %s ORDER BY `create_time` DESC LIMIT 1", keywords)
    logging.info(rs)
    if len(rs):
        target_task_info = rs[0]
        logging.info('type: {}, {}'.format(type(target_task_info['finish_time']), target_task_info['finish_time']))
        if datetime.datetime.now() - target_task_info['finish_time'] > datetime.timedelta(minutes=5):
            logging.error('超过阈值，重启任务')
            push_task(keywords)



class ReverseIpLookupHandler(BaseHandler):
    """Ip 反查接口"""

    def get(self, *args, **kwargs):
        target_ip = self.get_argument('target')

        task_state = get_task_state(target_ip)

        # 如果任务不存在, 则创建任务
        if -1 == task_state:
            logging.debug('任务不存在, 创建任务.')
            push_task(target_ip)
            logging.debug('创建任务 over.')
        elif 0 == task_state:
            logging.debug('正在排队')
        elif 1 == task_state:
            logging.debug('正在运行')
        elif 2 == task_state:
            logging.debug('已经结束')
            try_restart_task(target_ip)

        reverse_ip_data_list = []
        try:
            param_start = target_ip if '*' != target_ip[-1:] else target_ip[:-1] + '1'
            param_end = target_ip if '*' != target_ip[-1:] else target_ip[:-1] + '254'
            logging.info('param_start: ' + param_start)
            logging.info('param_end: ' + param_end)
            rs = db.query('''
                SELECT
                    `d`.`domain`, inet_ntoa(`i`.`ip`) as 'ip', `di`.`url`, `di`.`title`, `di`.`create_time`, `di`.`update_time`
                FROM 
                    `system_domains` `d`, `system_domain_and_ip` `di`, `system_ips` `i`
                WHERE
                    `d`.id = `di`.`domain_id`
                    AND `i`.`id` = `di`.`ip_id`
                    AND `i`.`ip` >= inet_aton(%s)
                    AND `i`.`ip` <= inet_aton(%s)
                ORDER BY
                    `i`.`ip`
            ''', param_start, param_end)
            reverse_ip_data = {}
            # for i in rs:
            #     logging.info(i['ip'])
            #     if not reverse_ip_data.get(i['ip']):
            #         reverse_ip_data[i['ip']] = []
            #     reverse_ip_data[i['ip']].append({
            #         'create_time': i['create_time'],
            #         'update_time': i['update_time'],
            #         'url': i['url'],
            #         'title': i['title'],
            #         'domain': i['domain']
            #     })
            # for i in reverse_ip_data.keys():
            #     reverse_ip_data_list.append({
            #         'ip': i,
            #         'data': reverse_ip_data[i]
            #     })
            for i in rs:
                flag_has = False
                for j in reverse_ip_data_list:
                    if j['ip'] == i['ip']:
                        flag_has = True
                        j['data'].append({
                            'create_time': i['create_time'],
                            'update_time': i['update_time'],
                            'url': i['url'],
                            'title': i['title'],
                            'domain': i['domain']
                        })
                if not flag_has:
                    reverse_ip_data_list.append({
                        'ip': i['ip'],
                        'data': [{
                            'create_time': i['create_time'],
                            'update_time': i['update_time'],
                            'url': i['url'],
                            'title': i['title'],
                            'domain': i['domain']
                        }]
                    })
            logging.info(reverse_ip_data_list)
        except Exception as e:
            logging.error(traceback.format_exc())
            logging.error(e)

        self.render('result_reverse_ip.html', reverse_ip_data=reverse_ip_data_list)


class ReverseIpLookupAsyncHandler(BaseHandler):
    """Ip 反查结果"""

    def get(self, *args, **kwargs):
        target = self.get_argument('target')
        last = int(self.get_argument('last', '0'))

        task_id = get_task_id(target)
        task_state = get_task_state(target)
        logging.info(task_id)
        logging.info(task_state)
        if task_id != -1 and task_state > 0:
            current_result_text = redis_cursor.hget(project_name + '__result_' + str(task_id), 'result')
            if current_result_text is not None:
                current_result = json.loads(current_result_text)
                self.write({
                    'data': current_result[last:],
                    'task_state': task_state
                })
                return
        self.write({
            'task_state': task_state
        })
