import time
import click
import os
import json
import subprocess
import tempfile
from scale import *
from scale.logger import Logger
from scale.manager import Manager
from scale.operation import Operation

logger = Logger(__name__)
manager = Manager(logger)

#build the array used for the ssh non-interactive remote execution (per requested behavior)
def generateAnaxScaleCommand(ctx, host: str, command: str)-> Operation:
    env = ctx.obj[json_env]
    workerPseudoDelay = ctx.obj[wpdflag]
    logLevel = ctx.obj[rflag]
    count = ctx.obj[cflag]

    cdpart = "cd "+env[env_scaler_dir]+"; "
    scalerpart = "python3 -m "+env[env_scaler_name]+" "
    logpart = "-l "+str(logLevel)+" "
    countpart = "-c "+str(count)+" "

    s = cdpart+scalerpart+logpart

    if command != queryRunningOp:
           s = s+countpart

    s = s+command

    return manager.generateSshCommand(env=env, host=host, operation=s, workerPseudoDelay=workerPseudoDelay, logger=logger)

def generateAnaxScaleCommands(ctx, command: str)->[Operation]:
    hosts = ctx.obj[json_endpoints]
    operations = []
    for host in hosts:
        operation = generateAnaxScaleCommand(ctx, host, command)
        operations.append(operation)
    return operations

def kickoff(ctx, operation: str):
    runmode = ctx.obj[mmflag]
    operations = generateAnaxScaleCommands(ctx, operation)
    manager.run(runmode=runmode, operations=operations)

@click.group()
@click.option('--locallog', '-l', type=int, default=0, show_default=True, help="0=debug, 1=info, 2=produciton, 3=error, 4=critical")
@click.option('--remotelog', '-r', type=int, default=0, show_default=True, help="0=debug, 1=info, 2=produciton, 3=error, 4=critical")
@click.option('--count', '-c', type=int, default=1, show_default=True, help="Number of horizon containers")
@click.option('--headpseudodelay', envvar="HZN_SCLR_HEAD_PSEUDODELAY", type=float, default=0.2, show_default=True, help="Head node delay if runmode is set to pseudoparallel")
@click.option('--workerpseudodelay', envvar="HZN_SCLR_WORKER_PSEUDODELAY", type=float, default=0.2, show_default=True, help="Worker node delay if runmode is set to pseudoparallel")
@click.option('--configfile', '-f', type=str, required=True, help="File containing configuration json")
@click.pass_context
def cli(ctx, configfile, workerpseudodelay, headpseudodelay, count, remotelog, locallog):
    """The EdgeScaler product is a Master-Slave distributed scale analysis platform.  It controls remote execution using
using the scale.anaxremote python module.  The scale.anaxremote master application performs non-interactive ssh
execution of the scale.anaxscale python module on slave nodes.  The scale.anaxscale slave application executes 0..*
hzn, horizon-container, and docker operations."""

    # Loads JSON Configuration File
    # {
    # "env": {
    #     "HZN_EXCHANGE_URL": "https://stg.edge-fabric.com/v1",
    #     "DOCKER_HUB_ID": "YOURHUBID",
    #     "HZN_ORG_ID": "YOURORGID",
    #     "EXCHANGE_USER": "iamapikey",
    #     "EXCHANGE_PW": "YOURPD",
    #     "HZN_EXCHANGE_USER_AUTH": "iamapikey:YOURPD",
    #     "MYDOMAIN": "YOURDOMAIN",
    #     "HZN_AIC": "/root/anax-in-container/horizon-container (YOUR LOCATION TO AIC)"
    #   },
    #   "endpoints": ["YOURHOSTNAMELIST",]
    # }

    global pseudoDelay
    pseudoDelay = headpseudodelay

    global logger
    logger.setupLogger(loglevel=locallog)

    #check for log level out of accepted range.  Slave logging is only 0 or 1.
    lglvl_remote=1
    if remotelog == 0:
        lglvl_remote = 0

    f = open(file=configfile)
    j = json.loads(f.read())
    ctx.obj = {
        mmflag: mode_parallel, #default master execution mode
        smflag: mode_parallel, #default slave execution mode
        json_endpoints: j[json_endpoints],
        json_env: j[json_env],
        rflag: lglvl_remote,
        cflag: count,
        wpdflag: workerpseudodelay
    }


@click.command()
@click.pass_context
def start(ctx):
    """Starts Anax Containers on all hosts"""
    operation = startOp
    kickoff(ctx, operation)

@click.command()
@click.pass_context
def restart(ctx):
    """Starts Anax Containers on all hosts"""
    operation = restartOp
    kickoff(ctx, operation)

@click.command()
@click.option('--mmode', '-m', envvar="HZN_SCLR_MASTER_MODE", type=int, default=0, show_default=True, help="Change master parallelism: 0=parallel, 1=pseudoparallel, 2=serial")
@click.option('--smode', '-s', envvar="HZN_SCLR_SLAVE_MODE", type=int, default=0, show_default=True, help="Change slave parallelisms: 0=parallel, 1=pseudoparallel, 2=serial")
@click.argument('pattern')
@click.pass_context
def register(ctx, mmode, smode, pattern):
    """Registers Anax Containers on all hosts with given pattern"""
    ctx.obj[mmflag]=mmode
    ctx.obj[smflag] = smode
    operation = registerOp+" --"+smflag+" "+str(smode)+" "+pattern
    kickoff(ctx, operation)


@click.command()
@click.option('--mmode', '-m', envvar="HZN_SCLR_MASTER_MODE", type=int, default=0, show_default=True, help="Change parallelism: 0=parallel, 1=pseudoparallel, 2=serial")
@click.option('--smode', '-s', envvar="HZN_SCLR_SLAVE_MODE", type=int, default=0, show_default=True, help="Change slave parallelisms: 0=parallel, 1=pseudoparallel, 2=serial")
@click.pass_context
def unregister(ctx, mmode, smode):
    """Unregisters the Anax Containers on all hosts"""
    ctx.obj[mmflag] = mmode
    ctx.obj[smflag] = smode
    operation = unregisterOp + " --" + smflag + " " + str(smode)
    kickoff(ctx, operation)

@click.command()
@click.option('--mmode', '-m', envvar="HZN_SCLR_MASTER_MODE", type=int, default=0, show_default=True, help="Change parallelism: 0=parallel, 1=pseudoparallel, 2=serial")
@click.option('--smode', '-s', envvar="HZN_SCLR_SLAVE_MODE", type=int, default=0, show_default=True, help="Change slave parallelisms: 0=parallel, 1=pseudoparallel, 2=serial")
@click.option('--eventlogflags', '-e', default="va", show_default=True, help="Flag values for hzn eventlog list")
@click.pass_context
def eventlog(ctx, mmode, smode, eventlogflags):
    """Collect eventlogs for all containers on all hosts"""
    ctx.obj[mmflag] = mmode
    ctx.obj[smflag] = smode
    operation = eventlogOp + " --" + smflag + " " + str(smode) + " --" + efflag + " " + eventlogflags
    kickoff(ctx, operation)

@click.command()
@click.pass_context
def stop(ctx):
    """Stops Anax Containers on all hosts"""
    operation = stopOp
    kickoff(ctx, operation)

@click.command()
@click.pass_context
def agreements(ctx):
    """Collects agreement information for all containers on all hosts"""
    operation = agreementsOp
    kickoff(ctx, operation)

@click.command()
@click.option('--list', '-l', is_flag=True, help="List anax containers on each host")
@click.option('--count', '-c', is_flag=True, help="List anax container count on each host")
@click.pass_context
def queryrunning(ctx, list, count):
    """Lists the anax containers deployed on each hosts"""
    operation = queryRunningOp
    if list:
        operation = operation+" --list"
    else:
        operation = operation+" --count"

    kickoff(ctx, operation)

@click.command()
@click.pass_context
def validaterunning(ctx):
    """Validates if docker containers are in the running state"""
    operation = validateRunningOp
    kickoff(ctx, operation)

@click.command()
@click.pass_context
def prune(ctx):
    """Ensures there is a clean environment across all hosts for scale testing"""
    operation = pruneOp
    kickoff(ctx, operation)

@click.command()
@click.option('--source', '-s', type=str, required=True, help="Source file/directory to be transfered")
@click.option('--destination', '-d', type=str, required=True, help="Destination file/directory to recieve transfer")
@click.pass_context
def dockercp(ctx, source, destination):
    """Executes Docker's cp command across every host in the configuration file for every container specified with -c"""
    operation = dockercpOp+" --source "+source+" --destination "+destination
    kickoff(ctx, operation)

@click.command()
@click.argument('cmd')
@click.pass_context
def dockerexec(ctx, cmd):
    """Executes Docker's exec command across every host in the configuration file for every container specified with -c"""
    kickoff(ctx, dockerexecOp+" "+cmd)

@click.command()
@click.option('--logdir', '-o', type=str, required=True, help="Logging directory")
@click.pass_context
def agentlogs(ctx, logdir):
    """Executes Docker's exec command across every host in the configuration file for every container specified with -c"""
    operation = agentlogsOp + " --logdir " + logdir
    kickoff(ctx, operation)

@click.command()
@click.pass_context
def containerconfigupdate(ctx):
    """Executes Docker's exec command across every host in the configuration file for every container specified with -c"""
    kickoff(ctx, containerconfigupdateOp)

cli.add_command(start)
cli.add_command(restart)
cli.add_command(stop)

cli.add_command(register)
cli.add_command(unregister)

cli.add_command(agreements)
cli.add_command(eventlog)
cli.add_command(agentlogs)

cli.add_command(queryrunning)
cli.add_command(validaterunning)
cli.add_command(prune)

cli.add_command(dockercp)
cli.add_command(dockerexec)
cli.add_command(containerconfigupdate)

if __name__ == '__main__':
    cli()