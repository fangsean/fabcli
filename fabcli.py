import sys

import click
from fabric.api import local
from fabric.colors import *
from fabric.context_managers import settings, hide
from fabric.decorators import task
from pkg_resources import resource_filename

from src.comm_model.setting import Settings, HIDE_GROUPS

__version__ = '0.1'
pass_config = click.make_pass_decorator(Settings, ensure=True)
exec_local = f"-f {resource_filename(__name__, 'fabfile.py')}"

@click.group()
def main():
    pass


@main.command()
@pass_config
@task
def test(config):
    ''' 测试 '''

    click.echo(yellow("***test 测试***"))
    with settings(hide(*HIDE_GROUPS), warn_only=True):
        local('fab test')

    click.echo(green("\tEND TASK"))


@main.command()
@click.option('--namespace', '-n', help="命名空间", type=str, required=True)
@task
def check(namespace):
    ''' 检查校验 '''

    click.echo(yellow("***检查校验***"))
    with settings(hide(*HIDE_GROUPS), warn_only=True):
        local(f'fab {exec_local} check:namespace=%s' % (namespace))

    click.echo(green("\tEND TASK"))


@main.command()
@click.option('--model', '-m', default=None, help='项目服务名.', type=str, required=False)
@click.option('--branch', '-b', default=None, help="分支名称", type=str, required=False)
@pass_config
@task
def git(config, model, branch):
    ''' 执行代码更新任务 '''

    click.echo("***git 执行代码更新任务***")
    models = list(config.get_params("servers").keys())
    if model == None or branch == None or model not in models:
        warning_info(config)

    try:
        local(f'fab {exec_local} git:model=%s,branch=%s' % (model, branch))
    except Exception as e:
        click.echo(red(f"\tERROR TASK {e}"))
    click.echo(green("\tEND TASK"))


@main.command()
@click.option('--model', '-m', default=None, help='项目服务名.', type=str, required=False)
@click.option('--deploy', '-e', default=None, help="版本环境", type=str, required=False)
@pass_config
@task
def rollback(config, model, deploy):
    ''' 执行回退任务 '''

    click.echo(yellow("***backup 执行回退任务***"))
    models = list(config.get_params("servers").keys())
    envs = list(config.get_params("deploy").keys())

    if model == None or deploy == None or model not in models or deploy not in envs:
        warning_info(config)

    try:
        local(f'fab {exec_local} rollback:model=%s,deploy=%s' % (model, deploy))
    except Exception as e:
        click.echo(red("\tERROR TASK"))

    click.echo(green("\tEND TASK"))


@main.command()
@click.option('--model', '-m', default=None, help='项目服务名.', type=str, required=False)
@click.option('--deploy', '-e', default=None, help="版本环境", type=str, required=False)
@click.option('--branch', '-b', default=None, help="分支名称", type=str, required=False)
@pass_config
@task
def go(config, model, deploy, branch):
    ''' 非容器部署 '''

    click.echo(yellow("***go 执行单一模式发布任务***"))
    models = list(config.get_params("servers").keys())
    envs = list(config.get_params("deploy").keys())

    if model == None or deploy == None or branch == None \
            or model not in models or deploy not in envs:
        warning_info(config)

    try:
        local(f'fab {exec_local} go:model=%s,deploy=%s,branch=%s' % (model, deploy, branch))
    except Exception as e:
        click.echo(red("\tERROR TASK"))
    click.echo(green("\tEND TASK"))


@main.command()
@click.option('--model', '-m', default=None, help='项目服务名.', type=str, required=False)
@click.option('--deploy', '-e', default=None, help="版本环境", type=str, required=False)
@pass_config
@task
def kill(config, model, deploy):
    ''' 停止服务进程 '''

    click.echo(yellow("***kill 停止服务进程***"))
    models = list(config.get_params("servers").keys())
    envs = list(config.get_params("deploy").keys())

    if model == None or deploy == None or model not in models or deploy not in envs:
        warning_info(config)

    try:
        local(f'fab {exec_local} kill:model=%s,deploy=%s' % (model, deploy))
    except Exception as e:
        click.echo(red("\tERROR TASK"))

    click.echo(green("\tEND TASK"))


@main.command()
@click.option('--model', '-m', default=None, help='项目服务名.', type=str, required=False)
@click.option('--deploy', '-e', default=None, help="版本环境", type=str, required=False)
@pass_config
@task
def restart(config, model, deploy):
    ''' 重启服务进程 '''

    click.echo(yellow("***restart 重启服务进程***"))
    models = list(config.get_params("servers").keys())
    envs = list(config.get_params("deploy").keys())

    if model == None or deploy == None or model not in models or deploy not in envs:
        warning_info(config)

    try:
        local(f'fab {exec_local} restart:model=%s,deploy=%s' % (model, deploy))
    except Exception as e:
        click.echo(red("\tERROR TASK"))

    click.echo(green("\tEND TASK"))


@main.command()
@click.option('--model', '-m', default=None, help='项目服务名.', type=str, required=False)
@click.option('--deploy', '-e', default=None, help="版本环境", type=str, required=False)
@pass_config
@task
def ci(config, model, deploy):
    ''' 初始化准备 '''

    click.echo(yellow("***START CI TASK***"))
    models = list(config.get_params("servers").keys())
    envs = list(config.get_params("deploy").keys())
    if model == None or deploy == None or model not in models or deploy not in envs:
        warning_info(config)

    with settings(hide(*HIDE_GROUPS), warn_only=True):
        local(f'fab {exec_local} ci:model=%s,deploy=%s' % (model, deploy))

    click.echo(green("\tEND TASK"))


@main.command()
@click.option('--model', '-m', default=None, help='项目服务名', type=str, required=False)
@click.option('--deploy', '-e', default=None, help="版本环境,命名空间", type=str, required=False)
@click.option('--tag', '-t', default=None, help="版本", type=str, required=True)
@pass_config
@task
def deploy(config, model, deploy, tag):
    ''' 容器部署 '''

    click.echo(yellow("***START DEPLOY TASK***"))
    Settings.check_k8s_kubefile()
    models = list(config.get_params("servers").keys())
    envs = list(config.get_params("deploy").keys())
    if model == None or deploy == None or model not in models or deploy not in envs:
        warning_info(config)

    with settings(hide(*HIDE_GROUPS), warn_only=True):
        local(f'fab {exec_local} cicd:model=%s,deploy=%s,tag=%s' % (model, deploy, tag))

    click.echo(green("\tEND TASK"))


def warning_info(config):
    click.echo(red("\tPlease enter the [model] parameter ："))
    click.echo(magenta(list(config.get_params("servers").keys())))
    click.echo(red("\tPlease enter the [deploy] parameter :"))
    click.echo(magenta(list(config.get_params("deploy").keys())))
    sys.exit(red("\tBreak"))


if __name__ == '__main__':
    check(['--namespace', 'Account'])
    # deploy(['-n', 'kube-system'])
    # jar(['-m', 'entry', '-e', "dev"])
    ci(['-m', 'billing-portal-general', '-e', "devlocal"])
    # git(['-m', 'fabcli', '-b', 'main'])
