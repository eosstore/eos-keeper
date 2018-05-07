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
#       b. bp是否不断变化，如果1分钟内收到的bp个数/种类小于等于4个。
#       c. head_block_num 是否不断增加
#   措施
#       a. 通知下一道防线变为主角色。（A角色适用<这是可有可无的操作>，其他角色不用）
#       b. 报警通知运维人员。
#
#
# 2. 根据日志，判断是否和主网分叉的（A、B、F角色通用）
#   依据
#       a. 15秒内没有任何日志。（测试网络发现一般有23-30秒没有日志）
#       b. 根据日志类型3分析，如果接收不到类型3的信息，或者接收到的类型3的bp个数太少，则说明分叉了。
#           b.1 30秒内未收到此类日志。（重点）
#           b.2 1分钟内收到的bp个数/种类小于等于4个。（重点）
#       c. 根据日志类型1分析，如果num数值大于等于48（12*4）个则认为分叉了。
#       d. 后期出现权威网站，可以通过api调用获得最新块高度，和日志块高度对比，差距超出一定量则认为分叉。
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

#       ================================================= CODE =================================================

import time
import threading
import re
import ConfigParser
from sh import tail
import docker
import requests


class List:
    def __init__(self, max_length):
        self.__list = []
        self.__maxLength = max_length
        self.__lock = threading.Lock()

    def append(self, data):
        self.__lock.acquire()
        if self.__list.__len__() >= self.__maxLength:
            self.__list.pop(0)
        self.__list.append(data)
        self.__lock.release()

    def read(self, length):
        self.__lock.acquire()
        res = self.__list[(self.__list.__len__() - length):]
        self.__lock.release()
        return res

    def length(self):
        return self.__list.__len__()


# -- 从配置文件加载参数 --
class NewConfigParser(ConfigParser.RawConfigParser):
    def get(self, section, option):
        val = ConfigParser.RawConfigParser.get(self, section, option)
        return val.strip('"').strip("'")


config = NewConfigParser()
config.read('config.ini')

role = config.get("global", "role")
producer_name = config.get("global", "producer_name")
http_port = config.get("global", "http_port")
is_docker = config.get("global", "is_docker")
log_file = config.get("global", "log_file")
c_name = config.get("global", "c_name")


# -- 全局变量 --

# 有哪些list呢
# http端口相关，以下3项都是每秒记录一次数据。
l_http_json_ok = List(100)      # 记录http端口是否返回数据，及是否是json格式；正确则记录1，错误则记录为2
l_http_bps = List(200)          # 记录bp是否正常变化
l_http_hbn = List(100)          # 记录head_block_num 是否不断增加

# 日志相关
now = time.time()
t_last_log = now              # 最后一条日志的时间
t_last_log_style2 = now       # 最后一条类型2日志的时间，用户A角色判断是否正常出块
t_last_log_style3 = now       # 最后一条类型3日志的时间
l_log_push_bps = List(300)              # 记录bp更换是否正常
l_log_missed_block_num = List(20)       # 记录类型1日志的信息
l_log_missed_block_num_t = List(20)     # 记录每个l_log_missed_block_num记录的时间

re_s1 = r'.*] Number of missed blocks: (\d+)'
re_s2 = r'.*producer_plugin.cpp.*] (.*) generated block .* (#\d+) @.* with (\d+) trxs.*'
re_s3 = r'.*chain_controller.cpp.*] push block (#\d+) from (.+) 20\d\d-.*'

url = 'http://localhost:' + http_port + '/v1/chain/get_info'


# -- 故障处理 --
def err_handler(msg):
    print "ERROR HANDLE! :" + msg


# -- 日志分析 --
def log_parse(line):
    global t_last_log, t_last_log_style2, t_last_log_style3, l_log_missed_block_num, l_log_missed_block_num_t
    t_last_log = time.time()

    # 当有bp不工作时，会匹配此项。
    res1 = re.match(re_s1, line)
    if res1:
        # 提取丢失的块数，插入列表
        l_log_missed_block_num.append(res1.group(1))
        l_log_missed_block_num_t.append(time.time())
        return

    # 只有A角色出块时会匹配此项内容。
    res2 = re.match(re_s2, line)
    if res2:
        # 如果不是eosstore出块则采取措施
        if res2.group(1) != producer_name:
            err_handler()
            return
        # 更新出块时间
        t_last_log_style2 = time.time()
        return

    # 当从其他节点同步块的时候会匹配此项。
    res3 = re.match(re_s3, line)
    if res3:
        # 更新从其他节点接收块时间
        t_last_log_style3 = time.time()

        # 提取对应bp，并插入列表
        bp = res3.group(2)
        l_log_push_bps.append(bp)
        return


class LogParser(threading.Thread):
    def run(self):
        if is_docker == "true":
            client = docker.from_env()
            nodeos = client.containers.get("nodeos")
            for line in nodeos.logs(stream=True, tail=1):
                log_parse(line)
        else:
            for line in tail("-n", 1, "-f", log_file, _iter=True):
                log_parse(line)


# -- http 端口分析 --
def http_parse():
    try:
        r = requests.get(url)
    except:
        l_http_json_ok.append(2)
    else:
        try:
            res = r.json()
        except:
            l_http_json_ok.append(2)
        else:
            l_http_json_ok.append(1)
            l_http_hbn.append(res["head_block_num"])
            l_http_bps.append(res["head_block_producer"])


class HttpParser(threading.Thread):
    def run(self):
        while True:
            http_parse()
            time.sleep(1)


# -- 分析从http端口和日志收集的信息 --
def parse():
    # 分析http端口是否正常
    if l_http_json_ok.length() > 5:
        if l_http_json_ok.read(5) == [2] * 5:
            err_handler("http端口异常！")
            return

    # 分析http返回的bps是否正常
    if l_http_bps.length() > 60:
        bps = set()
        for bp in l_http_bps.read(60):
            bps.add(bp)
        if bps.__len__() < 5:
            err_handler("http端口: 1分钟内捕获的BP个数太少！")
            return

    # 分析http返回的hbn是否正常
    if l_http_hbn.length() > 10:
        res = l_http_hbn.read(10)
        if res[0] == res[9]:
            err_handler("http端口: 10秒内head_block_num未增加！")
            return

    # 分析log，上一条日志的时间
    if time.time() - t_last_log > 20:
        err_handler("log: 超过20秒未收到任何日志")
        return

    # 分析log，类型3，查看接收块的情况
    if time.time() - t_last_log_style3 > 30:
        err_handler("log: 超过30秒未收到push block信息")
        return

    # 分析log，类型3，查看从其他bp接收块的情况
    if l_log_push_bps.length() > 60:
        bps = set()
        for bp in l_log_push_bps.read(60):
            bps.add(bp)
        if bps.__len__() < 5:
            err_handler("log: 1分钟内捕获的BP个数太少！")
            return

    # 分析log，类型1，查看丢失块是否正常。
    if l_log_missed_block_num.length() > 4:
        res = l_log_missed_block_num.read(4)
        res_t = l_log_missed_block_num_t.read(4)
        if time.time() - res_t[0] < 300 and res >= [24]:
            err_handler("log: 多次missed_block_num连续超过24个！")
            return

    # 如果是A角色，
    if role == "A":
        pass
        return

    if role == "B":
        pass











def get_info():
    msg = {}
    msg["http_head_block_producer"] = l_http_bps.read(1)
    msg["http_head_block_num"] = l_http_hbn.read(1)
    msg["log_push_bp"] = l_log_push_bps.read(1)
    return msg


if __name__ == '__main__':
    log_parser = LogParser()
    log_parser.setDaemon(True)
    log_parser.start()

    http_parser = HttpParser()
    http_parser.setDaemon(True)
    http_parser.start()

    while True:
        parse()
        print get_info()
        time.sleep(1)



