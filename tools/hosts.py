import os
import time
import json
import logging
import click
import subprocess
from subprocess import TimeoutExpired
from pprint import pprint
from scale import *
from scale.manager import Manager
from scale.logger import Logger
from scale.operation import Operation

logger = Logger(__name__)
manager = Manager(logger)

pflag="prefix"
dflag="domain"
cflag="count"
mflag="mode"
srcflag="source"
dstflag="destination"
tflag="timeout"
vcmd = "hostname"
json_env = 'env'
json_endpoints = 'endpoints'
syslogs_capturedir="syslogs"
syslog = "/var/log/syslog"
cnstCommand = "command"
cnstReturncode = "returncode"
cnstStdout = "stdout"
cnstStderr = "stderr"

def generateHostnames(ctx)->[str]:
    list=[]
    for i in range(ctx.obj[cflag]):
        hostname = ctx.obj[pflag]+str(i+1).zfill(2)+"."+ctx.obj[dflag]
        list.append(hostname)
    return list


def generateReceiveSyslogCmds(hostnames: [str], logdir: str, logger: Logger):
    p = os.path.join(logdir, syslogs_capturedir)
    os.makedirs(p, exist_ok=True)

    operations = []
    for hostname in hostnames:
        hsyslog = os.path.join(p, hostname + "_syslog.log")
        command = ["scp", "-r", "root@"+hostname+":"+syslog, hsyslog]
        operation = Operation(operation=command, logger=logger)
        operations.append(operation)
    return operations

def loadConfig(ctx, configfile: str):
    f = open(file=configfile)
    j = json.loads(f.read())
    ctx.obj[json_endpoints]=j[json_endpoints]
    ctx.obj[json_env]=j[json_env]

@click.group()
@click.option('--loglevel', '-l', type=int, default=0, show_default=True, help="0=debug, 1=info, 2=production, 3=error, 4=critical")
@click.option('--headpseudodelay', envvar="HZN_SCLR_HEAD_PSEUDODELAY", type=float, default=0.2, show_default=True, help="Head node delay if runmode is set to pseudoparallel")
@click.option('--workerpseudodelay', envvar="HZN_SCLR_WORKER_PSEUDODELAY", type=float, default=0.2, show_default=True, help="Worker node delay if runmode is set to pseudoparallel")
@click.option('--mode', '-m', type=int, default=0, show_default=True, help="Change master parallelism: 0=parallel, 1=pseudoparallel, 2=serial")
@click.option('--timeout', '-t', type=int, default=15, show_default=True, help="Sets seconds the Master will wait for a Slave command to return.")
@click.pass_context
def cli(ctx, loglevel, headpseudodelay, workerpseudodelay, mode, timeout):
    logger.setupLogger(loglevel=loglevel)
    ctx.obj = {}
    ctx.obj[mflag]=mode
    ctx.obj[tflag]=timeout
    ctx.obj[hpdflag]=headpseudodelay
    ctx.obj[wpdflag]=workerpseudodelay

@click.command()
@click.option('--prefix', '-p', type=str, required=True, help="Hostname prefix for which an index will be appended")
@click.option('--domain', '-d', type=str, required=True, help="Domain upon which which hostname will be prefixed")
@click.option('--count', '-c', type=int, default=1, show_default=True, help="Number of horizon containers")
@click.pass_context
def validateHosts(ctx, prefix, domain, count):
    """Checks each hostname given the hostname prefix and domain. Runs: ssh hostINDEX.domain hostname"""
    env = {}
    ctx.obj[pflag]=prefix
    ctx.obj[dflag]=domain
    ctx.obj[cflag]=count
    hostnames = generateHostnames(ctx)
    operations = manager.generateSshCommands(env=env, hostnames=hostnames, operation=vcmd, logger=logger)
    manager.run(runmode=ctx.obj[mflag], operations=operations)

@click.command()
@click.option('--configfile', '-f', type=str, required=True, help="File containing configuration json")
@click.pass_context
def validateConfig(ctx, configfile):
    """Checks each each hostname in the json configuation file"""
    env = {}
    loadConfig(ctx, configfile)
    hostnames = ctx.obj[json_endpoints]
    operations = manager.generateSshCommands(env=env, hostnames=hostnames, operation=vcmd, logger=logger)
    manager.run(runmode=ctx.obj[mflag], operations=operations)

@click.command()
@click.option('--configfile', '-f', type=str, required=True, help="File containing configuration json")
@click.option('--logdir', '-o', type=str, required=True, help="Directory to place syslogs")
@click.pass_context
def recieveSyslogs(ctx, configfile, logdir):
    """Recieves source file from the corresponding hosts and writes to destination)"""
    env = {}
    loadConfig(ctx, configfile)
    hostnames = ctx.obj[json_endpoints]
    operations = generateReceiveSyslogCmds(hostnames=hostnames, logdir=logdir, logger=logger)
    manager.run(runmode=ctx.obj[mflag], operations=operations)

@click.command()
@click.option('--source', '-s', type=str, required=True, help="Source file/directory on local host")
@click.option('--destination', '-d', type=str, required=True, help="Destination file/directory on remote host")
@click.option('--configfile', '-f', type=str, required=True, help="File containing configuration json")
@click.pass_context
def scpsend(ctx, source, destination, configfile):
    """Sends source file to the corresponding destination on each config file host)"""
    loadConfig(ctx, configfile)
    hostnames = ctx.obj[json_endpoints]
    operations = manager.generateSendCommands(hostnames=hostnames, source=source, destination=destination, logger=logger)
    manager.run(runmode=ctx.obj[mflag], operations=operations)

@click.command()
@click.option('--source', '-s', type=str, required=True, help="Source file/directory on remote host")
@click.option('--destination', '-d', type=str, required=True, help="Destination directory on local host")
@click.option('--configfile', '-f', type=str, required=True, help="File containing configuration json")
@click.pass_context
def scpreceive(ctx, source, destination, configfile):
    """Receives the source file from each of the hosts defined in configfile.  Source file is placed in a dynamically generated subdirectory of destination directory.)"""
    loadConfig(ctx, configfile)
    hostnames = ctx.obj[json_endpoints]
    operations = manager.generateRecieveCommands(hostnames=hostnames, source=source, destination=destination, logger=logger)
    manager.run(runmode=ctx.obj[mflag], operations=operations)

@click.command()
@click.option('--configfile', '-f', type=str, required=True, help="File containing configuration json")
@click.argument('command', nargs=-1)
@click.pass_context
def pushcommand(ctx, configfile, command):
    """Executes the command passed in on every host defined in the configfile"""
    loadConfig(ctx, configfile)
    hostnames = ctx.obj[json_endpoints]
    env = {}
    operation = ' '.join(command)
    operations = manager.generateSshCommands(env=env, hostnames=hostnames, operation=operation, logger=logger )
    manager.run(runmode=ctx.obj[mflag], operations=operations)

cli.add_command(pushcommand)
cli.add_command(scpsend)
cli.add_command(scpreceive)

cli.add_command(validateHosts)
cli.add_command(validateConfig)
cli.add_command(recieveSyslogs)

if __name__ == '__main__':
    cli()