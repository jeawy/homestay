#!/usr/bin/env python
# -*- coding:utf-8 -*- 
##########################################################
# (C) 2000-2012 NSFOCUS Corporation. All rights Reserved #
##########################################################
'''
Created on 2012-8-6

@author: maochong

background logger utils
'''
import os
 
import logging
import logging.config
import traceback
import time
import datetime
import pdb

LOG_HOME = os.path.dirname(os.path.abspath(__file__))
LOG_HOME = os.path.join(os.path.dirname(LOG_HOME), "logs") 

FOMMATER = '[%(asctime)s](%(levelname)s) {pid:%(process)d, tid:%(thread)d, %(filename)s}, %(module)s.%(funcName)s %(lineno)d: %(message)s'

def getLogger(singleOrmodule, logfile, pscr = False, interval = 180):
    '''
    :singleOrmodule False单日志，True模块日志
    :logfile 日志输出文件，只输入文件名到默认路径，或直接输入系统的其他绝对路径
    :pscr 是否将日志输出到控制台
    '''
    logpath = ""
    if not os.path.exists(LOG_HOME):
        os.mkdir(LOG_HOME)

    # 输入指定的其他目录存放日志时，若绝对路径不存在，抛出IOError异常
    # if logfile.find("/") != -1:
    #     onlydir = os.path.dirname(logfile)
    #     if not os.path.isdir(onlydir):
    #         raise IOError("The %s path doesn't exist!" % onlydir)
    # else:
    #     logfile = os.path.join(LOG_HOME, logfile)

    # 如果传入的相对路径或绝对路径不存在的时候递归创建所需文件夹
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    ext = os.path.splitext(logfile)[1]
    if ext != ".log" :
        logpath = ('%s.log' % logfile)
        logfile = logpath + "." + today
    else: 
        logfile = logfile + ".log." + today 

    logfile = os.path.join(LOG_HOME, logfile) if not os.path.isabs(logfile) else logfile

    onlydir = os.path.dirname(logfile)
    if not os.path.isdir(onlydir):
        os.makedirs(onlydir)

    """
    # 判断扩展名是否为log，若不存在需要添加log后缀

    ext = os.path.splitext(logfile)[1]
    if ext != ".log" :
        logpath = ('%s.log' % logfile)
    else:
        logpath = logfile
    """
    logpath = logfile
    #python内部438权限对应Linux内部666权限
    if not os.path.exists(logpath):
        try:
            os.mknod(logpath)
            os.chmod(logpath, 438)
        except:
            pass
    else:
        try:
            os.chmod(logpath, 438)
        except:
            pass

    if not singleOrmodule:
        return SingleLogger(logpath, pscr)
    else:
        ml = ModuleLogger("")
        ml.init(logpath, pscr, interval)
        return ml


class ModuleLogger(logging.Logger):
    """
    守护进程的logger配置
    """
    last_time = None

    def init(self, logpath, pscr, interval):
        self.logpath = logpath
        self.pscr = pscr
        self.debug_ctl = 'DEBUG'

        self.interval = interval
        self.handlers = []
        self.config()

    def config(self):
        global FOMMATER
        # 生成root logger

        if self.debug_ctl.upper() == "DEBUG":
            level = logging.DEBUG
        elif self.debug_ctl.upper() == "INFO":
            level = logging.INFO

        self.setLevel(level)
        # 清理上次设置生效的handler
        if self.handlers:
            for handler in self.handlers:
                self.removeHandler(handler)


        #设置格式
        formatter = logging.Formatter(FOMMATER)

        # 生成RotatingFileHandler，设置文件大小为10M,编码为utf-8，最大文件个数为30个，如果日志文件超过30，则会覆盖最早的日志  
        fh = logging.handlers.RotatingFileHandler(self.logpath, mode = 'a', maxBytes = 1024*1024*10, backupCount = 30, encoding = "utf-8")
        fh.setLevel(level)
        fh.setFormatter(formatter)
        self.addHandler(fh)

        if self.pscr:
            #生成StreamHandler
            ch = logging.StreamHandler()
            ch.setLevel(level)
            ch.setFormatter(formatter)
            self.addHandler(ch)

    def debug(self, msg, *args, **kwargs):
        if msg is not None:
            now = time.localtime(time.time())

            if self.last_time is not None:
                # 计算logger.debug上次调用的时间差
                delta_time = time.mktime(now) - time.mktime(self.last_time)

                # 判断是否超过设置的时间间隔
                if delta_time > self.interval:
                    # 本次超过时间间隔后，查看配置文件的DEBUG_CTL的值
                    debug_attr = 'DEBUG'

                    # 与目前设定的DEBUG_CTL相比
                    if debug_attr.upper() != self.debug_ctl.upper():
                        # 发生变化重新生效logger配置
                        self.debug_ctl = debug_attr
                        self.config()

                    # 超过debug的interval时间后更新last_time为当前时间
                    self.last_time = now
            else:
                # 第一次初始化last_time的时间为当前时间
                self.last_time = now

            self._log(logging.DEBUG, msg, args, **kwargs)

def SingleLogger(logpath, pscr):
    ''' 非守护进程的logger配置 '''
    global FOMMATER
    hdlr_Stream = None
    hdlr_Rotating = None
    level = None
    debug_ctl = 'DEBUG'

    if debug_ctl.upper() == "DEBUG":
        level = logging.DEBUG
    elif debug_ctl.upper() == "INFO":
        level = logging.INFO

    l_format = logging.Formatter(FOMMATER)

    # 初始化、获得日志实例对象
    rootLogger = logging.getLogger("")
    rootLogger.setLevel(level)

    # 清理上次设置生效的handler
    if rootLogger.handlers:
        for handler in rootLogger.handlers:
            rootLogger.removeHandler(handler)

    rootLogger.handlers = []

    #生成RotatingFileHandler，设置文件大小为10M，编码为utf-8，最大文件个数为30个，如果日志文件超过30，则会覆盖最早的日志
    hdlr_Rotating = logging.handlers.RotatingFileHandler(logpath, mode = 'a', maxBytes = 1024*1024*10, backupCount = 30, encoding = 'utf-8')
    hdlr_Rotating.setFormatter(l_format)
    hdlr_Rotating.setLevel(level)
    rootLogger.addHandler(hdlr_Rotating)

    if pscr:
        # 输出日志到控制台
        hdlr_Stream = logging.StreamHandler(sys.stdout)
        hdlr_Stream.setFormatter(l_format)
        hdlr_Stream.setLevel(level)
        rootLogger.addHandler(hdlr_Stream)

    return rootLogger

if __name__ == '__main__':
    """ Usage: from logutils import getLogger """

    # 设置方式1——非守护进程：指定不存在的路径，捕获IOError异常，控制台不可显
    try:
        logger = getLogger(False, "/opt/nsfocus/espc/log/vulnerabilityApp/1.log", False)
    except IOError as e:
        # 捕获到路径不存在的IO异常
        print ("logger1 IOError: ", e)

    # 设置方式2——非守护进程：日志文件名，控制台不可显
    logger = getLogger(False, "/opt/nsfocus/espc/log/vulnerabilityApp/2.log", False)
    try:
        logger.info("dir right")
        logger.info("logger2 info exception")
        logger.info()
    except Exception as e:
        logger.debug('This is a debug info')
        logger.exception(e)
        logger.error('This is a error info')

    # 设置方式3——非守护进程：日志文件名，控制台可显
    # __name__指日志文件名使用模块名命名
    logger = getLogger(False, "/opt/nsfocus/espc/log/vulnerabilityApp/3.log", True)

    try:
        logger.info("logger3 info exception")
        logger.info("test")
    except Exception as e:
        logger.debug('This is a debug info')
        logger.info('traceback exception e')
        logger.exception(e)
        logger.error('This is a error info')

    # 设置方式4——守护进程：日志文件名，控制台可显，间隔时间
    # 不停止守护进程，修改wsms_conf.py中的debug.level，可生效更改的配置。
    interval = 30
    seconds = 6
    logger = getLogger(True, __name__, True, interval)
    zh_temp = '这是调试信息'

    while 1:
        logger.info("Debug %s sleep %d s interval %d s" , logger.debug_ctl, seconds, interval)
        logger.debug("This is a debug info: %s", zh_temp.encode('utf-8'))
        time.sleep(seconds)

    flag, xml_content = write_to_xml(single_target, \
                                 len(targets), \
                                 single_site_info, \
                                 sessionID, \
                                 url_hash + '.xml')

