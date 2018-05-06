#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# ========= eoskeeper是一个用于监控eos程序的守护进程 =========
#
# == 程序原理 ==
# 我们的节点分为四种角色：A角色（BP）、B角色（备用BP，第一道防线）、C角色（备用BP，第二道防线）、普通全节点（后面用F角色表示）
#
# 东京节点(node1): A角色
# 新加坡节点(node2): B角色
# 北京节点(node3): C角色
# 这三个地区除上述关键节点外还有普通全节点。
#
# eoskeeper能够实时监控eos日志，检测9876和8888端口，
# 在三个主机中会分别给eoskeeper守护进程设置为A、B、C三个角色，以下是eoskeeper根据角色做出相应的动作，
# 当A主机的eos出现问题时，eoskeeper会给cloudwath发送告警信息；（并附加一个功能：立即远程对B执行脚本，使B出块，但次功能不作为主要功能，也就是说可以没有）
# 当A被修复时，需再次以A为主节点，让其他节点回到原来的角色。
# 当B主机检测到2轮出块循环都没有eosstore账户时，B主机的eoskeeper会执行脚本，使B出块
# 当B主机的eos出现问题时，eoskeeper会给cloudwath发送告警信息；（并附加一个功能：立即远程对B执行脚本，使C出块，但次功能不作为主要功能，也就是说可以没有）
# 当C主机检测到6轮出块循环都没有eosstore账户时，C主机的eoskeeper会执行脚本，使C出块
#
# 所有主机的eoskeeper都会实时将eos状态上传到cloudwatch，对cloudwatch进行设置，没有接收到eoskeeper的信息或者接收到告警信息都需要通知运维人员。
#
# == 配置相关 ==
# BP节点的eosio需要开启http api，并只允许本机访问。（用于健康检查）
#
# == 管理相关 ==
# 任何一台主机出现故障时，都需要及时修复。修复后，使各个节点恢复自己的角色。
# 正常情况下，需要设置cloudwatch，每隔一定时间，需要向专用的微信群发送三台主机的关键数据，我们和运维人员都在此群中。
#
#
# == 程序流程总括 ==
# 1. 判断是否分叉
# 2. 根据各自的角色进行判断并采取相应的措施。
#   a. 如果是A，则判断是否正常产生块。
#   b. 如果是B，则判断eosstore是否正常出块
#
#
# == 程序详细流程 ==
# *. 加载配置信息
# *. 检查8888端口（每隔固定时间查看调用结果，子进程）
# *. 过滤日志（实时分析日志流，子进程）
# *. 分析队列数据；如有异常，根据角色做出相应动作；将实时信息发送到cloudwatch
#
#
# 关键日志类型，具体案例，请见doc/log_parse.txt
# 类型1.
# fork_database.cpp:78
# "Number of missed blocks: ${num}"
#
# 类型2.
# producer_plugin.cpp:239
# "${p} generated block ${id}... #${n} @ ${t} with ${count} trxs, lib: ${lib}"
#
# 类型3.
# chain_controller.cpp:176
# "push block #${n} from ${pro} ${time}  ${id} lib: ${l} success"
#
# 类型4.
# chain_controller.cpp:726
# "pop block #${n} from ${pro} ${time}  ${id}"
#
#
#
#
# 各种故障判断及需要采取的措施
#
# 1. 判断8888端口是否正常
#   依据
#       a. 是否返回了正常的json内容，如果超过5秒不正常，说明节点异常。
#       b. bp是否不断变化
#       c. head_block_num 是否不断增加
#   措施
#       a. 通知下一道防线变为主角色。（A角色适用<这是可有可无的操作>，其他角色不用）
#       b. 报警通知运维人员。
#
#
# 2. 根据日志，判断是否和主网分叉的（A、B、F角色通用）
#   依据
#       a. 根据日志类型3分析，如果接收不到类型3的信息，或者接收到的类型3的bp个数太少，则说明分叉了。
#           a.1 15秒内没有任何日志。（测试网络发现一般有23-30秒没有日志）
#           a.2 30秒内未收到此类日志。（重点）
#           a.3 1分钟内收到的bp个数小于等于4个。（重点）
#       b. 根据日志类型1分析，如果num数值大于等于48（12*4）个则认为分叉了。
#       c. 后期出现权威网站，可以通过api调用获得最新块高度，和日志块高度对比，差距超出一定量则认为分叉。
#   措施
#       a. 通知下一道防线变为主角色。（A角色适用<这是可有可无的操作>，其他角色不用）
#       b. 报警通知运维人员。
#
#
# 3. 根据日志，在上面第2步判断正常的前提下，各自判断：
#   A角色 判断eosstore是否出块正常
#       依据
#           收集类型2的日志，看上次自己出块时间是否超过了260秒（6*21~=130秒,也就是一轮 130*2轮=260秒）
#       措施
#           同上
#
#   B角色 判断eosstore是否出块正常
#       依据
#           收集类型3的日志，看上次eosstore出块时间是否超过了260秒（2轮）
#       措施
#           自己变为主角色
#
#   C角色 判断eosstore是否出块正常
#       依据
#           收集类型3的日志，看上次eosstore出块时间是否超过了780秒(6轮)
#       措施
#           自己变为主角色
#
#   F角色  判断eosstore是否出块正常
#       依据
#           收集类型3的日志，看上次eosstore出块时间是否超过了秒650秒(5轮)
#       措施
#          报警通知运维人员。
#
#



import time
import threading
import re
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


# def parse():





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
    log_parser.setDaemon(True)
    log_parser.start()

    for i in range(1000):
        time.sleep(0.1)
        print(i)









