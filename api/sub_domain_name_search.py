#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import sys
# import threading
# import time
# from argparse import ArgumentParser
# from utils.decorators import PageCatcherDecorator, SearchEngineCatcherDecorator, CrtCatcherDecorator, \
#     SubDomainBruteDecorator, RecursiveCatcherDecorator
# from utils.getdomainsbyssl import GetDomainsBySsl
# from utils.pagecatcher import PageCatcher, RecursivePageCatcher
# from utils.pz import getbing as get_side_site
# from utils.searchenginecatcher import SearchEngineCatcher
# from utils.subDomainsBrute import SubNameBrute
# from utils.globalresult import g_result_dict
#
# reload(sys)
# sys.setdefaultencoding('utf-8')
#
# DEFAULT_LEVEL = 1
# DEFAULT_THREAD_COUNT = 8
# DEFAULT_CATCH_DEPTH = 3
# DEFAULT_CATCHER_PAGE_LIMIT = 100
#
# result_dict = {}
#
#
# # def callback(work_requests, data):
# #     if data and isinstance(data, dict):
# #         result_dict.update(data)
# #         # print '-' * 35 + 'finished.' + '-' * 35
# #         # print data
# #         # print '-' * 79
#
#
# def main():
#     argument_parser = ArgumentParser(description='子域名查询')
#     argument_parser.add_argument('domain', help='目标域名')
#     argument_parser.add_argument('-l', '--level', type=int, default=DEFAULT_LEVEL, help='查询等级')
#     argument_parser.add_argument('-f', '--file', type=str, default='dict/next_sub.txt', help='额外添加的字典')
#     argument_parser.add_argument('-t', '--threads', type=int, default=DEFAULT_THREAD_COUNT, help='爆破线程数')
#     argument_parser.add_argument('-o', '--output', help='输出文件， 默认文件名为{target}.txt')
#     argument_parser.add_argument('--ignore-intranet', action='store_true', help='忽略内网')
#     argument_parser.add_argument('--full-scan', action='store_true', help='完整爆破')
#     argument_parser.add_argument('-d', '--depth', type=int, default=DEFAULT_CATCH_DEPTH, help='爬取的深度')
#     argument_parser.add_argument('--proxy', help='代理')
#     argument_parser.add_argument('--spider-page-limit', type=int, default=DEFAULT_CATCHER_PAGE_LIMIT, help='爬虫爬取的页数')
#     argument_parser.add_argument('-v', '--verbose', action='store_true', help='')
#     args = argument_parser.parse_args()
#
#     setattr(args, 'i', args.ignore_intranet)
#     setattr(args, 'full_scan', args.full_scan)
#
#     # print args
#
#     thread_list = []
#     if args.level >= 1:
#         sub_domain_brute = SubDomainBruteDecorator(SubNameBrute(args.domain, args))
#         thread_list.append(threading.Thread(target=sub_domain_brute.execute))
#         crt_catcher = CrtCatcherDecorator(GetDomainsBySsl(args.domain, verbose=args.verbose))
#         thread_list.append(threading.Thread(target=crt_catcher.execute))
#         pass
#     if args.level >= 2:
#         search_engine_catcher = SearchEngineCatcherDecorator(SearchEngineCatcher(args.domain, args.spider_page_limit))
#         thread_list.append(threading.Thread(target=search_engine_catcher.execute))
#         pass
#     if args.level >= 3:
#         page_catcher = PageCatcherDecorator(PageCatcher(args.domain, args.domain, args.depth))
#         thread_list.append(threading.Thread(target=page_catcher.execute))
#
#     for per_thread in thread_list:
#         per_thread.setDaemon(True)
#         per_thread.start()
#     while threading.activeCount() > 1:
#         # print threading.activeCount()
#         time.sleep(0.1)
#
#     if args.level >= 4:
#         recursive_page_catcher = RecursiveCatcherDecorator(
#             RecursivePageCatcher(args.domain, g_result_dict.keys(), args.depth))
#         result_dict.update(recursive_page_catcher.execute())
#
#     if args.level >= 5:
#         all_ips = set()
#         for str_ips in g_result_dict.values():
#             ips = str_ips.split(', ')
#             for j in ips:
#                 all_ips.add(j)
#
#         side_site = {}
#         for i in all_ips:
#             side_site[i] = get_side_site(i)
#             if side_site[i]:
#                 print '\n%s:' % i
#                 for j in side_site[i]:
#                     print j[0].ljust(30) + j[1]
#
#     if args.output:
#         file_name = args.output
#     else:
#         file_name = args.domain + '.txt'
#     with open(file_name, 'w') as file:
#         for i in g_result_dict.keys():
#             file.write(i.ljust(30) + g_result_dict[i] + '\n')
#             file.flush()
#
#
# if __name__ == '__main__':
#     try:
#         main()
#     except KeyboardInterrupt, e:
#         sys.exit(-1)


import sys
import importlib
import threading
import time
from Queue import Queue
from utils import globalresult, g_config, utils
from sqlite3 import IntegrityError

reload(sys)
sys.setdefaultencoding('utf-8')

DEBUG = 0
config_json = g_config.config_json
db = g_config.db
db_cursor = g_config.db_cursor
task_queue = Queue()
global_lock = threading.Lock()
domain_id = -1


def lazy_load(module_name, prefix_package=''):
    module = importlib.import_module(prefix_package + '.' + module_name)
    class_name = ''.join([i.capitalize() for i in module_name.split('_')])
    target_class = getattr(module, class_name)
    return target_class


def out_put(domain, ip):
    if isinstance(ip, list):
        ip = ', '.join(ip)
    sys.stdout.write(domain.ljust(30) + ip + '\n')
    sys.stdout.flush()


def save_root_domain(root_domain):
    try:
        db_cursor.execute('INSERT INTO `root_domain` VALUES (NULL, ?)', (root_domain, ))
        db.commit()
    except IntegrityError as e:
        pass
    db_cursor.execute('SELECT `id` FROM `root_domain` WHERE `domain` = ?', (root_domain, ))
    return db_cursor.fetchone()[0]


def save_result(result):
    global_lock.acquire()

    sql_params = []
    if isinstance(result, list):
        for i in result:
            sql_params.append([domain_id, i, ''])
    elif isinstance(result, dict):
        for i in result.keys():
            if isinstance(result[i], list):
                ip_str = ', '.join(result[i])
            else:
                ip_str = result[i]
            sql_params.append([domain_id, i, ip_str])
            out_put(i, result[i])
    if DEBUG:
        print 'save_result: ' + str(sql_params)
    for i in sql_params:
        try:
            db_cursor.execute('''
                INSERT INTO `result_domain` values (
                    NULL, ?, ?, ?
                )
            ''', i)
            db.commit()
        except IntegrityError as e:
            if DEBUG:
                print 'save result: ' + str(e)
            pass

    global_lock.release()


def callback(task, result):
    if DEBUG:
        print 'callback: ', task, result
    # if isinstance(result, list):
    #     globalresult.add_list(result)
    # elif isinstance(result, dict):
    #     globalresult.update_result_dict(result)
    save_result(result)


def task_runner(task, callback=None):
    try:
        result = task()
        callback(task, result)
    except Exception as e:
        if DEBUG:
            print 'task_runner: ' + str(e)
        pass


def task_loader():
    while True:
        try:
            task = task_queue.get(timeout=0.1)
            new_thread = threading.Thread(target=task_runner, args=(task, callback))
            new_thread.setDaemon(True)
            new_thread.start()
        except Exception as e:
            pass


def ip_parser():
    while True:
        global_lock.acquire()
        db_cursor.execute('SELECT `id`, `domain` FROM `result_domain` WHERE `root_domain_id` = ? and `ip` = ""', (domain_id,))
        result_rows = db_cursor.fetchall()
        global_lock.release()

        if DEBUG:
            print 'ip_parser: ' + str(result_rows)
        if result_rows:
            sql_params = []
            for row in result_rows:
                id = row[0]
                domain = row[1]
                ip = utils.get_ip(domain)
                sql_params.append([ip, id])
                out_put(domain, ip)

            global_lock.acquire()
            db_cursor.executemany('UPDATE `result_domain` SET `ip` = ? WHERE `id` = ?', sql_params)
            db.commit()
            global_lock.release()
        time.sleep(0.1)


if __name__ == '__main__':
    # load modules
    module_config = config_json['modules']
    modules_class = []
    for module_name in module_config.keys():
        if module_config[module_name]:
            target_class = lazy_load(module_name, 'utils')
            modules_class.append(target_class)
            if DEBUG:
                print target_class

    target = sys.argv[1] if len(sys.argv) > 1 else 'cugb.edu.cn'
    domain_id = save_root_domain(target)
    if DEBUG:
        print 'domain_id: ' + str(domain_id)
    # sys.exit(0)

    # load history data
    db_cursor.execute('SELECT `domain`, `ip` FROM `result_domain` WHERE `root_domain_id` = ?', (domain_id,))
    history_data = db_cursor.fetchall()
    if history_data:
        for per_history_data in history_data:
            out_put(per_history_data[0], per_history_data[1])

    # run DNS Zone Transfer
    if config_json['dns_zone_transfer']:
        dns_zone_transfer = lazy_load('dns_zone_transfer', 'utils')
        print dns_zone_transfer(target).execute()

    # run per module
    for per_class in modules_class:
        task_queue.put(per_class(target).execute)
    task_loader_thread = threading.Thread(target=task_loader)
    task_loader_thread.setDaemon(True)
    task_loader_thread.start()
    ip_parser_thread = threading.Thread(target=ip_parser)
    ip_parser_thread.setDaemon(True)
    ip_parser_thread.start()

    # wait all task done
    try:
        time.sleep(1)
        while threading.active_count() > 3:
            # print threading.active_count()
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass

    db.close()
