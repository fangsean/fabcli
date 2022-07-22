# -*- coding:utf-8 -*-

import sys

import click
from fabric.api import local, env
from fabric.colors import *
from fabric.decorators import task, parallel, roles
from fabric.tasks import execute

from src.comm_model.setting import Settings
from src.component import CICDComponent, RollBackComponent, JarComponent, GitComponent, DockerComponent
from src.component import func_exception_log

env.roledefs['git'] = ['localhost']


@task()
@parallel
@click.help_option('-h', '--help')
def help(**args):
    ''' 帮助 '''


@task()
@parallel
@func_exception_log("test")
def test():
    ''' TEST '''

    local('ls -alrts')


@task()
@parallel
@func_exception_log("check")
def check(namespace):
    ''' 检查校验 '''
    print(namespace)
    configer = Settings()
    print(configer.get_params(namespace))


@roles('git')
@task()
@parallel
@func_exception_log("git")
def git(model, branch):
    ''' 执行代码更新任务 '''

    click.echo("***git 执行代码更新任务***")
    click.echo(green("\tSTART GIT TASK"))
    component = GitComponent(model, branch)
    # execute(component.model_local_check),
    execute(component.git_model_clone),
    # execute(component.git_model_tag),
    execute(component.model_end)
    sys.exit(0)


@task()
@parallel
@func_exception_log("go")
def go(model, deploy, branch):
    ''' 执行发布任务 '''

    click.echo("***go 执行发布任务***")
    click.echo(green("\tSTART GO TASK"))
    component = JarComponent(model, deploy, branch)
    execute(component.git_model_clone),
    execute(component.model_mvn_package),
    execute(component.model_remote_check),
    execute(component.model_jar_push),
    execute(component.model_jar_check),
    execute(component.model_server_kill),
    execute(component.model_jar_upgraded),
    execute(component.model_server_startup),
    execute(component.model_netstat),
    execute(component.model_end)
    sys.exit(0)


@task()
@parallel
@func_exception_log("rollback")
def rollback(model, deploy):
    ''' 执行回退任务 '''

    click.echo(yellow("***backup 执行回退任务***"))
    click.echo(green("\tSTART rollback TASK"))
    component = RollBackComponent(model, deploy)
    execute(component.model_jar_backup_list),
    execute(component.model_input_backup_file),
    execute(component.model_jar_backup),
    execute(component.model_server_kill),
    execute(component.model_server_startup),
    execute(component.model_netstat),
    execute(component.model_end)
    sys.exit(0)


@task()
@parallel
@func_exception_log("kill")
def kill(model, deploy):
    ''' 停止服务进程 '''
    click.echo(yellow("***kill 停止服务进程***"))
    click.echo(green("\tSTART KILL TASK"))
    component = RollBackComponent(model, deploy)
    execute(component.model_server_kill),
    sys.exit(0)


@task()
@parallel
@func_exception_log("restart")
def restart(model, deploy):
    ''' 重启服务进程 '''
    click.echo(yellow("***restart 重启服务进程***"))
    click.echo(green("\tSTART RESTART TASK"))
    component = RollBackComponent(model, deploy)
    execute(component.model_server_kill),
    execute(component.model_server_startup),
    execute(component.model_netstat),
    execute(component.model_end)
    sys.exit(0)


@task()
@parallel
@func_exception_log("k8s CI/CD")
def ci(model, deploy):
    ''' CI '''

    component = DockerComponent(model, deploy)
    # execute(component.git_model_clone),
    execute(component.docker_model_tag),
    execute(component.model_end)
    sys.exit(0)


@task()
@parallel
@func_exception_log("k8s")
def cicd(model, deploy, tag):
    ''' 执行发布任务 '''

    component = CICDComponent(model, deploy, tag)
    execute(component.docker_model_tag),
    execute(component.kub_patch_deployment),
    execute(component.kub_delete_productentry)
    execute(component.model_end)

    sys.exit(0)
