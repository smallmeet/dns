#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
工作进程，单独开启
从队列中取 id, 然后在 redis 中取任务内容进行扫描
"""

import sys
import os
import threading
import time
import logging
import traceback

from taskloader import load_task

import misc
from config import config, redis_cursor, db

reload(sys)
sys.setdefaultencoding('utf-8')

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')

project_name = config.project_name
running_tasks_key = project_name + '__tasks'
task_queue_key = project_name + '__task_queue'
task_detail_key_prefix = project_name + '__task_detail_'


def get_all_values(task_hash_key):
    task_all_keys = redis_cursor.keys(task_hash_key)


def update_task_state(task_id, target_state):
    # 更新任务状态
    db.insert('''
            UPDATE
                `system_task_records`
            SET
                `state` = %s
            WHERE
                `id` = %s''',
              target_state,
              task_id)


def time_it(func):
    """测量方法运行时间"""
    def wrapper(*args, **kwargs):
        start = time.time()
        func(*args, **kwargs)
        end = time.time()
        logging.info('function `{}` used {} seconds'.format(func.func_name, end - start))

    return wrapper


@time_it
def execute_task(task_id):
    """执行任务"""
    # 取任务信息
    task_hash_key = '%s%s' % (task_detail_key_prefix, task_id)
    current_task_settings = redis_cursor.hgetall(task_hash_key)
    task_type = current_task_settings['type']
    current_task_settings['task_id'] = task_id
    logging.debug('current_task_settings: {0}'.format(current_task_settings))

    update_task_state(task_id, 1)

    # 开始扫描
    tasks = []

    task_runner = load_task(task_type)(**current_task_settings)
    task_runner_thread = threading.Thread(target=task_runner.run)
    tasks.append(task_runner_thread)
    task_runner_thread.setDaemon(True)
    task_runner_thread.start()

    while not misc.is_threads_done(tasks):
        logging.debug('111')
        time.sleep(0.1)

    db.update('''
        UPDATE
            `system_task_records`
        SET
            `finish_time` = %s,
            `state` = %s
        WHERE
            `id` = %s''',
              misc.now(),
              2,
              task_id)


def take_over_task(task_id):
    """接管任务"""
    try:
        # 添加到任务区
        redis_cursor.hset(running_tasks_key, task_id, os.getpid())
        # 执行任务
        execute_task(task_id)
        # 任务完成, 从任务区移除
        redis_cursor.hdel(running_tasks_key, task_id)
        redis_cursor.delete(task_detail_key_prefix + task_id)
        return True
    except (Exception, KeyboardInterrupt) as e:
        # 如果任务执行时出现异常, 则重新入队
        if task_id != -1:
            redis_cursor.lpush(task_queue_key, task_id)
            redis_cursor.hdel(running_tasks_key, task_id)
        logging.error('%s' % traceback.format_exc())
        logging.error('work process caught exception: %s' % str(e))
    return False


def run():
    # 轮循任务区
    executing_task_ids = redis_cursor.hkeys(running_tasks_key)
    config.debug and logging.info('开始轮循任务区.')
    for per_task_id in executing_task_ids:
        task_runner_pid = int(redis_cursor.hget(running_tasks_key, per_task_id))
        if not misc.is_running(task_runner_pid):
            # 如果任务对应的进程挂了, 则接管任务
            config.debug and logging.info('任务 %s 对应进程挂了, 接管该任务.' % per_task_id)
            take_over_task(per_task_id)
    while True:
        # 从队列中取任务
        current_task_id = redis_cursor.lpop(task_queue_key)
        if not current_task_id or current_task_id == 'None':
            config.debug and logging.info('没有任务, 等待 3 秒.')
            time.sleep(3)
            continue

        config.debug and logging.info('开始执行任务 %s.' % current_task_id)
        flag_finished = take_over_task(current_task_id)
        if flag_finished:
            config.debug and logging.info('任务 %s 执行完毕.' % current_task_id)
        else:
            config.debug and logging.info('任务 %s 执行失败.' % current_task_id)
        time.sleep(3)


if __name__ == '__main__':
    run()
