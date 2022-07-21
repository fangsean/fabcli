import logging
import os
import sys
import time

from fabric.colors import *

from src.comm_model.setting import Settings

configer = Settings()
__log_root__ = configer.get_params("logs", 'root_path')


def Logger(name=None):
    log_root = __log_root__
    if log_root == None or log_root == '':
        log_root = os.path.join(os.getcwd(), os.sep, ".logs")
    if os.path.isdir(log_root) == False:
        os.makedirs(log_root)

    # LOG_FILE是日志文件名
    file = "log." + time.strftime('%Y-%m-%d-%H', time.localtime(time.time()))
    log_file = os.path.join(log_root, file)

    # 生成一个日志对象
    logger = logging.getLogger(name)

    # 按文件大小分隔日志，分隔多少份
    # file_handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=40 * 1024 * 1024, backupCount=40)
    # 根据时间对日志分隔，S-second（按秒对日志进行分割），M-Minutes（按分钟对日志进行分割），H-Hours（按小时对日志进行分割），D-Days（按天对日志进行分割）
    # file_handler = logging.handlers.TimedRotatingFileHandler(LOG_FILE, when='M', interval=1, backupCount=40)
    file_handler = logging.FileHandler(log_file)
    # 生成一个规范日志的输出格式
    formater = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S")
    # 将格式器设置到处理器上
    file_handler.setFormatter(formater)
    # stream_handler_err = logging.StreamHandler(sys.stderr)
    stream_handler_stdout = logging.StreamHandler(sys.stdout)
    # 将处理器加到日志对象上
    logger.addHandler(file_handler)
    # logger.addHandler(stream_handler_err)
    logger.addHandler(stream_handler_stdout)
    # 设置日志信息输出的级别
    logger.setLevel(logging.NOTSET)
    return logger


logger = Logger()
