#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals

import logging
import traceback
import time

from lxml import etree
import requests


URL_PATTERN = 'http://site.ip138.com/{}/'
REQUESTS_SETTINGS = {
    'headers': {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.86 Safari/537.36',
        'Referer': 'http://site.ip138.com'
    },
    'timeout': (5, 5),
}


def get_html(url):
    for i in range(3):
        try:
            response = requests.get(url, **REQUESTS_SETTINGS)
            if response.status_code == 200:
                response.encoding = 'utf-8'
                return response.text
        except Exception as e:
            logging.error(traceback.format_exc())
            logging.error(e)
        if i < 2:
            time.sleep(1)
    return None


def get_history_ip(target_domain):
    """查询历史解析记录"""
    result_json = {
        'data': []
    }
    try:
        html = get_html(URL_PATTERN.format(target_domain))
        if html is not None:
            document_root = etree.HTML(html)
            rows = document_root.xpath('//div[@class="content"]//div[@class="panel"]/p')
            for i in rows:
                ip = i.xpath('./a/text()')[0]
                start_date, end_date = i.xpath('./span/text()')[0].split('-----')
                result_json['data'].append({
                    'ip': ip,
                    'start_date': start_date,
                    'end_date': end_date
                })
    except Exception as e:
        logging.error(traceback)
        logging.error(e)
    return result_json


if __name__ == '__main__':
    print(get_history_ip('jwgl.nuststi.edu.cn'))
