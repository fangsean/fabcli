# -*- encoding: utf-8 -*-

import configparser
import json
import os
import sys
from pathlib import Path

import yaml as yaml
from pkg_resources import resource_filename

from src.comm_model.init import Singleton

INIT_FILE = "fabcli.ini"
SERVERS_HOSTS_FILE = "../config/servers.json"
REPOSITORY_FILE = "../config/repository.yaml"
APP_PREFIX = os.getenv('APP_PREFIX', sys.prefix)
IDENTITY_FILES = resource_filename(__name__, "../identity_files")
HIDE_GROUPS = ['stderr']
SHOW_GROUPS = ['running', 'stdout', 'stderr', 'debug']

SERVERS_HOSTS = 'servers_hosts'
REPOSITORY = 'repository'
REPOSITORY_GIT = 'git'
REPOSITORY_PROJECTS = 'projects'
SERVER_GIT = 'server_git'
SERVER_PATH_LOCAL = 'server_path_local'
SERVER_PATH_REMOTE = 'server_path_remote'


# @Singleton
class Settings(Singleton):
    """
        Python变量命名用法（以字符或者下划线开头，可以包括字母、数字、下划线，区别大小写）
        一般变量
        常量
        私有变量
        内置变量
    """

    # config
    instance = None
    __first_init = True

    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super().__new__(cls, *args, **kwargs)
        return cls.instance

    def __init__(self):
        if self.__first_init:
            self.__final__config = configparser.ConfigParser()
            self.__final__config.read(os.path.join(APP_PREFIX, INIT_FILE), encoding='utf-8')
            self.__config_params__ = {
                section: {
                    item[0]: item[1]
                    for item in self.__final__config.items(section)
                }
                for section in self.__final__config.sections()
            }

            with open(resource_filename(__name__, SERVERS_HOSTS_FILE),
                      encoding="utf-8") as fp:
                self.__config_params__[SERVERS_HOSTS] = json.loads(fp.read())

            with open(resource_filename(__name__, REPOSITORY_FILE),
                      encoding="utf-8") as fp:
                self.__config_params__[REPOSITORY] = yaml.load(fp.read(), Loader=yaml.FullLoader)

            git_conf = self.__config_params__[REPOSITORY][REPOSITORY_GIT]
            self.__config_params__[SERVER_GIT] = {
                project['name']: {**git_conf, **project}
                for project in self.__config_params__[REPOSITORY].get(REPOSITORY_PROJECTS, [])
            }

            self.__first_init = False

    def get_configer(self):
        return self.__final__config

    @staticmethod
    def check_k8s_kubefile():
        kube_config = os.path.join(os.environ['HOME'], ".kube", "config")
        my_file = Path(kube_config)
        if not my_file.is_file():
            print("%s not exists, loading please!" % (kube_config))
            exit(1)

    def get_params(self, key, *args, **kwargs):
        if len(args) == 0 and len(kwargs) == 0:
            return self.__config_params__[key]
        else:
            temp = self.__config_params__[key]
            for arg in args:
                temp = temp[arg]
            return temp

    def __split_list__(self, str):
        return str.split(',')

    def __host_ref__(self, dict, lists):
        params = []
        try:
            for list in lists:
                params.append(dict[list])
        except Exception as e:
            pass
        return params
