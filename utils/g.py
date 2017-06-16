#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import threading

reload(sys)
sys.setdefaultencoding('utf-8')


g_lock = threading.Lock()
