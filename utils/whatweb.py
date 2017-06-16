#!/usr/bin/env python 
# -*- coding: utf-8 -*-
""" create at 13/06/2017 """

__author__ = 'binbin'
import requests
import lxml.html
import json
import logging

class WhatWeb:

    '''
    获取web的指纹信息
    '''

    def __init__(self):
        '''
        获取web指纹的ip信息
        :return:
        '''
        self.url = "http://whatweb.bugscaner.com/look/"
        self.discriminate_post_url = "http://whatweb.bugscaner.com/what/"
        self.TIME_OUT = 30

    def _fetch_hash(self):
        headers = {
            "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Encoding":"gzip, deflate",
            "Accept-Language":"en-US,en;q=0.5",
            "Cookie":"saeut=CkMPIlk/ilYcKRN7CPGJAg==; a8995_pages=1; a8995_times=1",
            "Host":"whatweb.bugscaner.com",
            "User-Agent":"Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.04"
        }

        r = requests.get(self.url,headers=headers,timeout=self.TIME_OUT)
        if r.status_code == 200:
            body = lxml.html.fromstring(r.text)
            hash_inputs =  body.xpath("//input[@id='hash']/@value")
            return hash_inputs[0]
        return None



    def discriminate(self,domain):
        '''
        识别指纹
        :param domain:
        :return:

            {
                "url": "www.jinwulab.com",
                "error": "no",
                "cms": "wordpress",
                "md5": "1870a829d9bc69abf500eca6f00241fe"
            }

        '''

        headers = {
            "Accept":"application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding":"gzip, deflate",
            "Accept-Language":"en-US,en;q=0.5",
            "Cookie":"saeut=CkMPIlk/ilYcKRN7CPGJAg==; a8995_pages=1; a8995_times=1",
            "Host":"whatweb.bugscaner.com",
            "User-Agent":"Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.04"
        }

        try:
            hash_str = self._fetch_hash()

            if not hash_str:
                return "未识别"

            r = requests.post(self.discriminate_post_url,data={"hash":hash_str,'url':domain},headers=headers,timeout=self.TIME_OUT)
            if r.status_code == 200 and r.text:
                return json.loads(r.text)
            else:
                return "未识别"
        except Exception as e:
            logging.error('what web discriminate error.')
            logging.error(str(e))
            return "识别异常"

if __name__ == "__main__":
    print json.dumps(WhatWeb().discriminate("47.93.87.52"),ensure_ascii=False,indent=4)