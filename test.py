#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import re


# 1.
# fork_database.cpp:78
# "Number of missed blocks: ${num}"
#
# 2.
# producer_plugin.cpp:239
# "${p} generated block ${id}... #${n} @ ${t} with ${count} trxs, lib: ${lib}"
#
# 3.
# chain_controller.cpp:176
# "push block #${n} from ${pro} ${time}  ${id} lib: ${l} success"
#
#
# 4.
# chain_controller.cpp:726
# "pop block #${n} from ${pro} ${time}  ${id}"


re1 = r'.*] Number of missed blocks: (\d+)'
re2 = r'.*producer_plugin.cpp.*] (.*) generated block .* (#\d+) @.* with (\d+) trxs.*'
re3 = r'.*chain_controller.cpp.*] push block (#\d+) from (.+) 20\d\d-.*'







str1=r"2130501ms thread-0   fork_database.cpp:78          _push_block          ] Number of missed blocks: 108"
str2=r"2131500ms thread-0   producer_plugin.cpp:239       block_production_loo ] eostore generated block 9d14aa04... #640476 @ 2018-05-04T05:35:31.500 with 0 trxs, lib: 632783"
str3=r"2145053ms thread-0   chain_controller.cpp:176      push_block           ] push block #640491 from eoseco 2018-05-04T05:35:45.000  0009c5eb0f781ac5ba48960e0da9d20acfe3621837b05bc8af0ef3807c5eb253 lib: 632783 success"



res1 = re.match(re1, str1)

res2 = re.match(re2, str2)

res3 = re.match(re3, str3)

# print res1.group(1)
#
# print res2.group()
# print res2.group(1)
# print res2.group(2)
# print res2.group(3)


print res3.group(1)
print res3.group(2)
