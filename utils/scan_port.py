#!/usr/bin/env python 
# -*- coding: utf-8 -*-
""" create at 13/06/2017 """

__author__ = 'binbin'

from scanless.scanners.hackertarget import scan as hackertarget_scan
from scanless.scanners.yougetsignal import scan as yougetsignal_scan
from scanless.scanners.viewdns import scan as viewdns_scan
import logging
class ScanPort:

    def __init__(self):
        '''
        通过第三方接口获取端口开启信息
        :return:

        可选第三方接口有:

            "hackertarget",
            "yougetsignal",
            "viewdns",
            "ipfingerprints",
            "pingeu",
            "spiderip",
            "portcheckers",
            "t1shopper"

        '''

        pass


    def _scan(self,ip_or_domain):
        try:
            res = hackertarget_scan(ip_or_domain)
            return {"dataset":res,'source':'hackertarget'}
        except Exception as e:
            logging.error("hackertarget fetch error!")
            logging.error(str(e))
            pass

        try:
            res = yougetsignal_scan(ip_or_domain)
            return {"dataset":res,'source':'yougetsignal'}
        except Exception as e:
            logging.error("yougetsignal fetch error!")
            logging.error(str(e))
            pass

        try:
            res = viewdns_scan(ip_or_domain)
            return {"dataset":res,'source':'viewdns'}
        except Exception as e:
            logging.error("viewdns fetch error!")
            logging.error(str(e))
            pass


        return None

    def scan(self,ip_or_domain):
        res = self._scan(ip_or_domain)

        if not res:
            return None

        # 过滤无效端口
        lines = res['dataset'].split("\n")
        result = []
        for line in lines:
            if 'open' in line or 'PORT' in line:
                result.append(line)


        return {"dataset":"\n".join(result),"source":res['source']}


if __name__ == "__main__":
     print ScanPort().scan("cxhr.com")['dataset']