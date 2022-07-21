# -*- coding:utf-8 -*-
__author__ = "jsen"

import os.path
import sys
import time
from abc import ABCMeta

import click
import git
from fabric.api import local, run, env
from fabric.colors import *
from fabric.context_managers import settings, hide, lcd, cd, show
from fabric.contrib.console import confirm
from fabric.decorators import runs_once
from fabric.operations import open_shell, put
from fabric.utils import abort

from src.comm_model import setting
from src.comm_model.setting import Settings, IDENTITY_FILES
from src.comm_model.wrapper import func_exception_log, ignore_error
from src.util.mylog import logger


class Component(object):
    __metaclass__ = ABCMeta
    CLASS_TYPE = "Component"
    TEMPLATES = "templates"

    def __init__(self, model):
        self.__finnal_configer__ = Settings()
        self._model = model

    # 成功
    # @runs_once
    def model_end(self):
        click.echo(green("[" + self._model + "] 工作流程执行完毕!"))

    # 支持远程
    @staticmethod
    def runmkdir(dir):
        with settings(hide(*setting.HIDE_GROUPS), warn_only=False):
            run('mkdir -p %s ' % dir)

    @classmethod
    def extract_component_class(cls, component_type):
        """
        提取组件类型
        :param component:
        :return:
        """
        return eval('%s%s' % (component_type, Component.CLASS_TYPE))


class GitComponent(Component):
    MODEL = "Git"
    DEFAULT_ENV = 'dev'

    def __init__(self, model=None, branch=None):
        super().__init__(model)
        self._git_branch = branch
        git_config = self.__finnal_configer__.get_params(setting.SERVER_GIT, model)
        self._user = git_config["user"]
        self._token = git_config["token"]
        self._git_url = git_config["url"]
        self._name = git_config["name"]
        self._destination = git_config['destination']
        self._type = git_config['type']
        self._local_root_space = self.__finnal_configer__.get_params(setting.SERVER_PATH_LOCAL, setting.KEY_ROOT_SPACE)
        self._local_model_path = os.path.join(self._local_root_space, self._model)

    @func_exception_log("代码克隆")
    @runs_once
    def git_model_clone(self):
        with settings(hide(*setting.HIDE_GROUPS, 'stdout'), warn_only=False):
            git_path = self._local_model_path
            git_branch = self._git_branch
            git_url = self._git_url
            credentials = self._token
            # git_url_formate = git_url.split("://")
            # git_url_protocol = git_url_formate[0]  # 协议
            # git_url_remote = git_url_formate[1]
            # credentials = base64.b64encode(f"{self.__token}:".encode("latin-1")).decode("latin-1")
            # git_token_url = r'{0}://{1}:{2}@{3}'.format(git_url_protocol, self.__user, self.__token, git_url_remote)
            c = f"http.{git_url}/.extraheader=AUTHORIZATION: Bearer {credentials}"
            if os.path.exists(os.path.join(self._local_model_path, ".git")):
                cloned_repo = git.Repo(self._local_model_path)
                # repo.head.reset(index=True, working_tree=True)
                cloned_repo.git.reset('--hard', 'HEAD')
                cloned_repo.remotes.origin.fetch()
                cloned_repo.git.checkout(self._git_branch)
            else:
                cloned_repo = git.Repo.clone_from(url=git_url, to_path=git_path, branch=git_branch,
                                                  c=c, single_branch=True, depth=1)
                cloned_repo.remotes.origin.fetch()
            assert cloned_repo.active_branch != self._git_branch  # which wasn't checked out yet ...

    @func_exception_log()
    @runs_once
    def git_model_tag(self, tag=None, isTag=False):
        current_tag = tag
        with settings(hide(*setting.HIDE_GROUPS), warn_only=False):
            # tag & commit
            message = ("This is a tag-object pointing to %s" % current_tag)
            repo = git.Repo(self._local_model_path)
            if isTag:
                try:
                    _tag = repo.tag(current_tag)
                    if _tag.is_valid():
                        repo.git.tag('-d', _tag)
                    new_tag = repo.create_tag(current_tag, message=message)
                    repo.remotes.origin.push(new_tag)
                except Exception as e:
                    logger.warning("tag is exists. %s:%s" % (self._local_model_path, current_tag))

            repo.git.checkout(current_tag)
            # repo.git.checkout('HEAD', b=new_tag.name)

    @func_exception_log()
    @runs_once
    def model_branch_list(self, git_path):
        click.echo(green("[INFO]   远程分支列表："))
        with settings(hide(*setting.HIDE_GROUPS), warn_only=False):
            repo = git.Repo(git_path)
            branches = repo.branches
            click.echo(white(branches))
            return branches

    @runs_once
    @func_exception_log()
    def model_local_check(self):
        git_path = self._local_model_path
        if os.path.exists(git_path):
            with settings(hide(*setting.HIDE_GROUPS), warn_only=False):
                run('rm -rf %s ' % git_path)


class JarComponent(GitComponent):
    FILE_TYPE = 'jar'

    def __init__(self, model=None, deploy=None, branch=None):
        super().__init__(model, branch)

        if self._type != JarComponent.FILE_TYPE:
            raise AssertionError("The model %s type is not jar." % (model))

        self.deploy = deploy
        self._target_file = self._destination + '.jar'
        self.server_path_local = os.path.join(self._local_root_space, model)
        self.server_path_local_target = os.path.join(self.server_path_local, 'target')
        server_remote_path = self.__finnal_configer__.get_params(setting.SERVER_PATH_REMOTE, setting.KEY_ROOT_SPACE)
        self.server_path_remote = os.path.join(server_remote_path, model)
        servers = self.__finnal_configer__.get_params(setting.SERVERS_HOSTS, self._model, self.deploy)
        server_hosts = [self.__finnal_configer__.get_params(server) for server in servers]
        instance = server_hosts[0]
        env.port = instance['port']
        env.hosts = [instance['host']]
        env.host_string = instance['host']
        env.user = instance['user']
        env.password = instance['password']
        env.key_filename = os.path.join(IDENTITY_FILES, instance['key_filename'])

    @runs_once
    @func_exception_log()
    def model_remote_check(self):
        self.runmkdir(os.path.join(self.server_path_remote, 'target', 'temp'))
        self.runmkdir(os.path.join(self.server_path_remote, 'target', 'backup'))

    @runs_once
    @func_exception_log("打包")
    def model_mvn_package(self):
        with settings(hide(*setting.HIDE_GROUPS), warn_only=False):
            with lcd(self.server_path_local):
                # local('mvn clean compile package -Dmaven.test.skip=true -U -P %s | tqdm | wc -l ' % (self.env))
                local(f'mvn clean compile package -Dmaven.test.skip=true -U -P {self.deploy}')
                click.clear()

    # @runs_once
    @func_exception_log("远程发包")
    def model_jar_push(self):
        if self._model == None or self._model == '':
            return
        with settings(hide(*setting.HIDE_GROUPS), warn_only=False):
            with lcd(self.server_path_local_target):
                result = put(self._target_file,
                             os.path.join(self.server_path_remote, 'target', 'temp', self._target_file))
                if result.failed and not confirm("put file faild, Continue[Y/N]?"):
                    click.echo(abort("Aborting file put task!"))
                    click.echo(red("[INFO]   远程发包失败 > model_jar_push"))
                    sys.exit()

    @func_exception_log("校验文件")
    def model_jar_check(self):
        with settings(hide(*setting.HIDE_GROUPS), warn_only=False):
            with lcd(self.server_path_local_target):
                lmd5 = local('md5sum ' + self._target_file, capture=True).split(' ')[0]
                rmd5 = \
                    run('md5sum ' + os.path.join(self.server_path_remote, 'target', 'temp', self._target_file)).split(
                        ' ')[0]
            if lmd5 == rmd5:
                return True
            else:
                return False

    # @runs_once
    @func_exception_log("替换jar文件")
    def model_jar_upgraded(self):
        with settings(hide(*setting.HIDE_GROUPS), warn_only=False):
            with cd(os.path.join(self.server_path_remote, 'target')):
                if int(run(f" [ -e '{self._target_file}' ] && echo 11 || echo 10")) == 11:
                    run(f'cp -rf {self._target_file} ./backup/{self._target_file}.$(date +%Y%m%d.%H.%M)')
                run(f'mv -f  ./temp/{self._target_file} ./')

    # @runs_once
    @func_exception_log("重启服务")
    def model_server_startup(self):
        with settings(hide(*setting.HIDE_GROUPS), warn_only=False):
            with cd(os.path.join(self.server_path_remote, 'target')):
                run(f"(nohup java -jar {self._target_file} -Dlog4j2.formatMsgNoLookups=true"
                    f" --spring.profiles.active={self.deploy} > /dev/null 2>&1 &) && sleep 1",
                    pty=False)

    # @runs_once
    @func_exception_log("停止服务")
    def model_server_kill(self):
        while True:
            with settings(hide(*setting.HIDE_GROUPS), warn_only=False):
                PID = run('jps -lm |grep -v grep|grep ' + self._target_file + ' | awk \'{print $1}\'')
                click.echo(yellow("PID: %s" % (PID)))
                if PID != None and PID != '' and int(PID) > 0:
                    click.echo(yellow("[INFO]   进程存在，进行kill > model_kill"))
                    run(f"kill  {PID} && sleep 1", pty=False)
                    time.sleep(1)
                else:
                    click.echo(yellow("[WARN]   已经杀掉进程，没有发现服务 > model_kill"))
                    break

    # 查看服务
    # @runs_once
    @func_exception_log()
    def model_netstat(self):
        click.echo(green("[INFO]   查看服务 > model_netstat"))
        click.echo(green("正在查看，请稍等..........................."))
        with settings(hide(*setting.HIDE_GROUPS), warn_only=True):
            local('sleep 2')
            run(f"ps aux | grep java |grep {self._target_file}| grep -v grep ", pty=False)
            local('sleep 1')
            click.echo(green("[INFO]   JPS : "))
            open_shell("jps && exit ")


class RollBackComponent(JarComponent):

    def __init__(self, model=None, deploy=None):
        super().__init__(model, deploy, None)
        self.file = None

    # @runs_once
    @func_exception_log()
    def model_input_backup_file(self):
        click.echo(white('Release file: '))
        while (True):
            file = input("please input file from head list:")
            if file == None or file == '' or self._target_file not in file:
                red('输入有误，文件名称不规范,重新输入...')
            else:
                click.echo(green("您输入的文件名称是[%s]" % (file)))
                self.file = file
                return

    # @runs_once
    @func_exception_log("查看文件")
    def model_jar_backup_list(self):
        with settings(hide(*setting.HIDE_GROUPS), warn_only=False):
            with cd(os.path.join(self.server_path_remote, 'target', 'backup')):
                backup = os.path.join(self.server_path_remote, 'target', 'backup')

                result = run(f'ls  -l {backup} {self._target_file}*')
                if "No such file or directory" in result:
                    click.echo(red("[ERROR]   未发现备份文件"))
                    sys.exit()
                else:
                    return result

    # @runs_once
    @func_exception_log("还原jar文件")
    def model_jar_backup(self):
        with settings(hide(*setting.HIDE_GROUPS), warn_only=False):
            with cd(os.path.join(self.server_path_remote, 'target', 'backup')):
                run("pwd")
                with settings(hide(*setting.HIDE_GROUPS), warn_only=False):
                    backup_target = os.path.join(self.server_path_remote, 'target')
                    backup_file = os.path.join(self.server_path_remote, 'target', 'backup', self.file)
                    backup_target_file = os.path.join(self.server_path_remote, 'target', 'backup', self._target_file)
                    if int(run(f" [ -e '{backup_file}' ] && echo 11 || echo 10")) == 11:
                        run(f'cp -rf {backup_file} {backup_target_file}')
                        run(f'mv -f  {backup_target_file} {backup_target}')
                    else:
                        raise FileNotFoundError("[INFO]   未发现该文件 %s" % (self.file))


class DockerComponent(GitComponent):
    FILE_TYPE = 'docker'

    def __init__(self, model=None, deploy=None, tag=None):
        super().__init__(model, tag)

        if self._type != DockerComponent.FILE_TYPE:
            raise AssertionError("The model %s type is not docker." % (model))

        self._deploy = deploy
        self._tag = tag
        self._docker_model_tag = None
        docker = self.__finnal_configer__.get_params(setting.REPOSITORY, "docker")
        self._s3 = docker['s3']
        self._registry = docker['registry']

    @func_exception_log()
    @runs_once
    def docker_model_tag(self):
        operator_name = self._name
        current_workspace = self._local_model_path
        tag = self._tag if self._tag else int(time.time())
        target = r'{registry}/{name}:{tag}'.format(registry=self._registry, name=operator_name, tag=tag)
        with settings(hide(*setting.HIDE_GROUPS), warn_only=False):
            with lcd(current_workspace):
                logger.debug("current local dir: %s" % (local("pwd", capture=True)))
                local("sudo docker build -t %s ." % (target))
                local("sudo docker push %s " % (target))
                self._docker_model_tag = target

    def get_docker_model_tag(self):
        return self._docker_model_tag


class CICDComponent(DockerComponent):

    def __init__(self, model=None, deploy=None, tag=None):
        super().__init__(model, deploy, tag)

    @func_exception_log("CICD", "kubectl patch deployment image")
    @ignore_error()
    @runs_once
    def kub_patch_deployment(self):
        with settings(show(*setting.SHOW_GROUPS), warn_only=True):
            docker_model_tag = self.get_docker_model_tag()

            local(f"kubectl set image deployment/{self._destination} "
                  f" {self._destination}={self._registry}/{self._destination}:{docker_model_tag} "
                  f" -n {self._deploy} --record=true")

    @func_exception_log("CICD", "kubectl delete pod")
    @runs_once
    def kub_delete_productentry(self):
        with settings(show(*setting.SHOW_GROUPS), warn_only=True):
            local(f"kubectl delete pod -n {self._deploy} -l app={self._name}")
