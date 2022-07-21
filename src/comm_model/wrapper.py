# -*- coding:utf-8 -*-
__author__ = "jsen"

import functools
import sys

from fabric.colors import *

from src.util.mylog import logger


def func_exception_log(model=None, detail=""):
    def log(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            try:
                logger.info(blue("%s.%s    :%s" % (model, func.__name__, detail)))
                func_ = func(*args, **kw)
                logger.info(blue("%s.%s OK :%s" % (model, func.__name__, detail)))
                return func_
            except Exception as e:
                logger.error(red("%s.%s ERROR :%s" % (model, func.__name__, str(e))))
                sys.exit(1)

        return wrapper

    return log


# 忽略
def ignore_error():
    def execute(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            try:
                return func(*args, **kw)
            except Exception as e:
                logger.error(red("%s ERROR :%s" % (func.__name__, str(e))))

        return wrapper

    return execute
