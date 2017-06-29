#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json
import logging

import torndb
import redis
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


class Namespace(object):
    """Simple object for storing attributes.

    Implements equality by attribute names and values, and provides a simple
    string representation.
    """

    def __init__(self, **kwargs):
        for name in kwargs:
            setattr(self, name, kwargs[name])

    __hash__ = None

    def __eq__(self, other):
        if not isinstance(other, Namespace):
            return NotImplemented
        return vars(self) == vars(other)

    def __ne__(self, other):
        if not isinstance(other, Namespace):
            return NotImplemented
        return not (self == other)

    def __contains__(self, key):
        return key in self.__dict__

env = os.getenv("sub_domain_env")
if env not in('devel','local','binbin','prod'):
    env = 'local'

try:
    fp = file('%s/config/%s_config.json'%(os.getcwd().replace("utils/","").replace("utils",""),env))
    config_data = fp.read()
    fp.close()

    config_json = json.loads(config_data)
    config = Namespace(**config_json)

    mysql_settings = {
        'host': config_json['mysql_host'],
        'user': config_json['mysql_user'],
        'password': config_json['mysql_pwd'],
        'database': config_json['mysql_db'],
        'charset': config_json['mysql_charset']
    }
    db = torndb.Connection(time_zone='+8:00',**mysql_settings)

    redis_settings = {
        'host': config_json['redis_host'],
        'port': config_json['redis_port']
    }
    redis_pool = redis.ConnectionPool(**redis_settings)
    redis_cursor = redis.Redis(connection_pool=redis_pool)
    if not redis_cursor.ping():
        raise Exception('redis connect failed')

    project_name = config_json['project_name']
    pre_system = config_json['pre_system']
    http_server_port = config_json['http_port']
    DEBUG = config_json['debug']

    # 为 Worker 和 TaskLoader 创建
    engine = create_engine('mysql://{}:{}@{}/{}?charset={}'.format(
        config_json['mysql_user'],
        config_json['mysql_pwd'],
        config_json['mysql_host'],
        config_json['mysql_db'],
        config_json['mysql_charset']
    ))
    db_session = scoped_session(sessionmaker(bind=engine))
except Exception as e:
    logging.error('load config error: %s' % str(e))
    sys.exit(-1)
