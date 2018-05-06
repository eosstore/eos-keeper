#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# 程序原理：
# 我们提供一主两备，共三个节点，分别用A、B、C表示，eoskeeper是一个用于监控eos程序的守护进程，
# eoskeeper能够实时监控eos日志，检测9876和8888端口，
# 在三个主机中会分别给守护进程设置A、B、C三个角色，以是eoskeeper根据角色做出相应的动作，
# 当A主机的eos出现问题时，eoskeeper会给cloudwath发送告警信息；（并附加一个功能：立即远程对B执行脚本，使B出块，但次功能不作为主要功能，也就是说可以没有）
# 当B主机检测到2轮出块循环都没有eosstore账户时，B主机的eoskeeper会执行脚本，使B出块
# 当B主机的eos出现问题时，eoskeeper会给cloudwath发送告警信息；（并附加一个功能：立即远程对B执行脚本，使C出块，但次功能不作为主要功能，也就是说可以没有）
# 当C主机检测到6轮出块循环都没有eosstore账户时，C主机的eoskeeper会执行脚本，使C出块
#
# 所有主机的eoskeeper都会实时将eos状态上传到cloudwatch，对cloudwatch进行设置，没有接收到eoskeeper的信息或者接收到告警信息都需要通知
# 运维人员。


# 管理相关：
# 正常情况下，需要设置cloudwatch，每隔一定时间，需要向专用的微信群发送三台主机的关键数据，我们和运维人员都在此群中。

# 程序流程：
#
# *. 加载配置信息
# *. 过滤日志（实时分析日志流，子进程）
# *. 检查8888端口（每隔固定时间查看调用结果，子进程）
# *. 检查9876端口（每隔固定时间查看调用结果，子进程）
# *. 分析队列数据；如有异常，根据角色做出相应动作；将实时信息发送到cloudwatch
#
#


import time
import threading
import ConfigParser
from sh import tail
import docker


class NewConfigParser(ConfigParser.RawConfigParser):
    def get(self, section, option):
        val = ConfigParser.RawConfigParser.get(self, section, option)
        return val.strip('"').strip("'")


config = NewConfigParser()
config.read('config.ini')

is_docker = config.get("global", "is_docker")
log_file = config.get("global", "log_file")
c_name = config.get("global", "c_name")



class LogParser(threading.Thread):
    def run(self):
        if is_docker == "true":
            client = docker.from_env()
            nodeos = client.containers.get("nodeos")

            for line in nodeos.logs(stream=True, tail=1):
                print line
        else:
            for line in tail("-n", 1, "-f", log_file, _iter=True):
                print(line)


if __name__ == '__main__':
    log_parser = LogParser()
    log_parser.run()

    for i in range(1000):
        time.sleep(1)
        print(i)









