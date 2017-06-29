#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import requests
import misc
from config import config


class ReverseIpLookUp(object):
    """调用反查 Ip 接口"""

    def __init__(self, target_ip, **kwargs):
        self.target_ip = target_ip
        self.on_progress = kwargs['on_progress'] if kwargs.get('on_progress') else None

    def run(self):
        result_json = {}
        url = 'http://' + config.reverse_ip_api_host + '/reverse_ip/{}'
        # url = 'http://127.0.0.1:8889/reverse_ip/{}'

        # C 段
        if '*' == self.target_ip[-1:]:
            for i in range(1,255):
                ip = self.target_ip[:-1] + str(i)
                per_result_data = requests.get(url.format(ip)).json()
                logging.info(ip + " " + str(per_result_data))
                self.on_progress({
                    'ip': ip,
                    'data': per_result_data['data']
                })
                result_json[ip] = per_result_data['data']

        # 单个 Ip
        else:
            try:
                result_list = requests.get(url.format(self.target_ip)).json()['data']
                result_json[self.target_ip] = result_list
                if self.on_progress:
                    self.on_progress({
                        'ip': self.target_ip,
                        'data': result_list
                    })
            except Exception as e:
                result_json[self.target_ip] = []
                pass
        return result_json


if __name__ == '__main__':
    runner = ReverseIpLookUp('220.191.214.46')
    print runner.run()
