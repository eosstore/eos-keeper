#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#

import thread
import threading
import time


import requests

url = 'http://localhost:8888/v1/chain/get_info'
# url = "https://www.baidu.com"

try:
    r = requests.get(url)
except:
    print "request error"
else:
    try:
        res = r.json()
    except:
        print "not json"
    else:
        print res["head_block_num"]
        print res["head_block_producer"]
