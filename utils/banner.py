#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
nmap banner信息获取

"""

import json
import logging
import traceback

import nmap


# def get_banner(domain, port=80):
#     port = port
#     cmd = 'nmap -p {0} -sV --script=banner {1}'
#     out = os.popen(cmd.format(port, domain))
#     result = str()
#     list1 = out.read().splitlines()
#     for i in range(len(list1)):
#         if i > 4:
#             if list1[i].strip() != '':
#                 result += list1[i]
#                 result += '\n'
#             else:
#                 break
#     return result


def get_banner(ip, port='80'):
    try:
        nm = nmap.PortScanner()
        scan_result = nm.scan(ip, port)
        logging.debug(scan_result)
        return nm[ip]['tcp'][80]
    except Exception as e:
        logging.error('Caught an error when scan port, ip: {0}, port: {1}'.format(ip, port))
        logging.error(traceback.format_exc())
        logging.error(str(e))
    return None


if __name__ == '__main__':
    print json.dumps(get_banner('220.191.214.46'), indent=2)
