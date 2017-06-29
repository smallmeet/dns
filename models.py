#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import Column, SMALLINT
from sqlalchemy import create_engine, INT, VARCHAR, Text, DateTime, ForeignKey,NUMERIC
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.databases import mysql
import ipaddress


from utils.config import config_json

BaseModel = declarative_base()


class User(BaseModel):

    __tablename__ = 'system_admin_user'

    id = Column(INT, primary_key=True, autoincrement=True)
    group_id = Column(SMALLINT, nullable=False)
    username = Column(VARCHAR(128), nullable=False)
    password = Column(VARCHAR(32), nullable=False)
    create_time = Column(DateTime, nullable=False)
    lastlogin_time = Column(DateTime, nullable=False)
    login_ip = Column(VARCHAR(32), default='')
    avatar = Column(VARCHAR(64), default='')
    comment = Column(VARCHAR(255), default='')


class Domain(BaseModel):
    """根域名"""

    __tablename__ = 'system_domain'

    id = Column(INT, primary_key=True)
    domain = Column(VARCHAR(64), nullable=False)
    domain_whois = Column(Text, default='')
    ns_records = Column(Text, default='')
    mx_records = Column(Text, default='')

class SubDomainResult(BaseModel):
    """子域名结果"""

    __tablename__ = 'system_subdomain_result'

    id = Column(INT, primary_key=True)
    domain_id = Column(INT, nullable=False)
    subdomain = Column(VARCHAR(255), nullable=False)
    ip = Column(Text, nullable=False)
    location = Column(Text)
    last_commit_time = Column(DateTime, nullable=False)
    origin = Column(VARCHAR(32), nullable=False)
    state = Column(INT, nullable=True)


class TaskRecords(BaseModel):
    """任务"""

    __tablename__ = 'system_task_records'

    id = Column(INT, primary_key=True)
    keywords = Column(VARCHAR(64), nullable=False)
    state = Column(INT, default=0)
    create_time = Column(DateTime)
    finish_time = Column(DateTime)


class SystemEvents(BaseModel):
    """事件"""

    __tablename__ = 'system_events'

    def __init__(self,ip, **kwargs):
        BaseModel.__init__(self,**kwargs)
        self.ip = self.ip_to_int(ip)
        self.ipv4 = ip

    id = Column(INT, primary_key=True)
    ip = Column(NUMERIC(200), nullable=False)
    ipv4 = Column(VARCHAR(200),default='', nullable=False)
    domain = Column(VARCHAR(64), nullable=False)
    state = Column(INT, default=0)
    type_id = Column(INT, default=0)
    create_time = Column(DateTime)
    finish_time = Column(DateTime)
    is_delete = Column(INT, default=0)

    def get_ip(self):
        if not self.ip:
            return None

        else:
            return str(ipaddress.IPv4Address(self.ip))

    @classmethod
    def ip_to_int(self,ip):
        return int(ipaddress.IPv4Address(unicode(ip)))


class SystemDomains(BaseModel):
    '''
    域名信息
    '''

    __tablename__ = 'system_domains'

    def __init__(self,domain,**kwargs):
        BaseModel.__init__(self,**kwargs)
        self.domain = domain

    id = Column(INT, primary_key=True)
    cms = Column(VARCHAR(500), nullable=False)
    domain = Column(VARCHAR(500), default='',nullable=False)
    head_info = Column(VARCHAR(500), default='', nullable=False)
    create_time = Column(DateTime)
    sync_time = Column(DateTime)

class SystemIps(BaseModel):
    '''
    ip信息
    '''

    __tablename__ = 'system_ips'

    def __init__(self,ip, **kwargs):
        BaseModel.__init__(self,**kwargs)
        self.ipv4 = ip
        self.ip = self.ip_to_int(ip)

    id = Column(INT, primary_key=True)
    ip = Column(NUMERIC(200), nullable=False)
    ipv4 = Column(VARCHAR(200),default='', nullable=False)
    port_info = Column(VARCHAR(5000),default='', nullable=False)
    web_info = Column(VARCHAR(500), default='',nullable=False)
    create_time = Column(DateTime)
    sync_time = Column(DateTime)

    def get_ip(self):
        if not self.ip:
            return None

        else:
            return str(ipaddress.IPv4Address(self.ip))

    @classmethod
    def ip_to_int(self,ip):
        return int(ipaddress.IPv4Address(unicode(ip)))

if __name__ == '__main__':
    engine = create_engine('mysql://{}:{}@{}/{}?charset={}'.format(
        config_json['mysql_user'],
        config_json['mysql_pwd'],
        config_json['mysql_host'],
        config_json['mysql_db'],
        config_json['mysql_charset']
    ))
    DBSession = sessionmaker(bind=engine)
    db_session = DBSession()
    domain = db_session.query(Domain).filter(Domain.domain == 'kq88.com').one()
    print(domain.mx_records)
    db_session.close()
