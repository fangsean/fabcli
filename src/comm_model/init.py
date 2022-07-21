# -*- encoding: utf-8 -*-


class Singleton(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if Singleton._instance is None:
            Singleton._instance = object.__new__(cls, *args, **kwargs)
        return Singleton._instance
