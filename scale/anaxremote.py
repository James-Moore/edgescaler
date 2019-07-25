import time
import datetime
import click
import os
import json
import logging
import subprocess
from subprocess import TimeoutExpired

logger = logging.getLogger(__name__)
json_env = 'env'
json_endpoints = 'endpoints'
env_scaler_dir = "HZN_SCALER_DIR"
env_scaler_name = "HZN_SCALER_NAME"
rflag = "remotelog"
cflag = "count"

mmflag = "mmode"
smflag = "smode"
mode_parallel = 0
mode_pseudoserial = 1
mode_serial = 2
pseudoDelay=.2

startOp = "start"
stopOp = "stop"
restartOp = "restart"
registerOp = "register"
unregisterOp = "unregister"
eventlogOp = "eventlog"
queryRunningOp = "queryrunning"
validateRunningOp = "validaterunning"
agreementsOp = "agreements"
nodesOp = "node list"
pruneOp = "prune"
dockercpOp = "dockercp"
dockerexecOp = "dockerexec"
forcekillallOp ="forcekillall"
containerconfigupdateOp = "containerconfigupdate"



def timestamp()->str:
    return "["+str(datetime.datetime.now()).split('.')[0]+"]\t"

def debug(out: str):
    logger.debug(timestamp()+out)

def info(out: str):
    logger.info(timestamp()+out)

def warning(out: str):
    logger.warning(timestamp()+out)

def error(out: str):
    logger.error(timestamp()+out)

def isSerial(mode: int)->bool:
    return mode == mode_serial

def isPseudoSerial(mode: int)->bool:
    return mode == mode_pseudoserial

def isParallel(mode: int)->bool:
    return mode == mode_parallel

def generateSshLogin(host: str)->[str]:
    sshcmd = "ssh"
    sshconnect = "root@"+host
    return [sshcmd, sshconnect]

def generateSshCommand(host: str, operation: str, env: {})->[str]:
    assemble = ""
    for key in env:
        assemble = assemble +"export "+key+"="+env[key]+"; "
    assemble = assemble + operation
    login = generateSshLogin(host)
    return login + [assemble]

#build the array used for the ssh non-interactive remote execution (per requested behavior)
def generateAnaxScaleCommand(ctx, host: str, operation: str)->[]:
    env = ctx.obj[json_env]
    logLevel = ctx.obj[rflag]
    count = ctx.obj[cflag]

    cdpart = "cd "+env[env_scaler_dir]+" && "
    scalerpart = "python3 -m "+env[env_scaler_name]+" "
    logpart = "-l "+str(logLevel)+" "
    countpart = "-c "+str(count)+" "

    operations = cdpart+scalerpart+logpart

    if operation != queryRunningOp:
           operations = operations+countpart

    operations = operations + operation

    return generateSshCommand(host, operations, env)

def generateAnaxScaleCommands(ctx, operation: str)->[]:
    hosts = ctx.obj[json_endpoints]
    commands = []
    for host in hosts:
        command = generateAnaxScaleCommand(ctx, host, operation)
        commands.append(command)
    return commands

def exportEnv(env: {}):
    for key in env:
        os.environ[key] = env[key]

#run the remote command asynchronously so all hosts perform their local parallel operations in parallel
#meaning... parallelism is hostcount*processcount
def remoteRun(ctx, commands: []):
    exportEnv(ctx.obj[json_env]) #export environment from json environment description
    runmode = ctx.obj[mmflag]
    info("Run Mode: "+str(runmode)+" Remote Operation...\n" + commands[0][2]+"\n")
    processes = {}
    #Kickoff all asynchronous processes
    for command in commands:
        debug("Calling remote operation on: " + command[0]+" "+command[1])
        sshinfo = command[1] #this is the user@hostname portion of the ssh command
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        processes.update({sshinfo: p})

        #User defined mode of operation
        if isPseudoSerial(runmode):
            cval = ctx.obj[cflag]
            dval = pseudoDelay
            sval = dval*cval*2
            debug(str(["Delay: "+str(dval), "Count: "+str(cval), "Sleeping: "+str(sval)]))
            time.sleep(sval)
        elif isSerial(runmode):
            debug("Waiting for process to complete before continuing...")
            p.wait()

    logger.debug("")
    info("All Processes Scheduled...  Waiting for completion... Do not interupt..")

    #Wait for all background processes
    for command in commands:
        sshinfo = command[1] #this is the user@hostname portion of the ssh command
        process = processes[sshinfo]
        debug("Waiting for "+sshinfo+" with process "+str(process.pid))

        #aquire remote command's output
        outs = str()
        errs = str()
        try:
            errs, outs = process.communicate()
        except TimeoutExpired:
            process.kill()
            errs, outs = process.communicate()

        warning(str(outs).rstrip()+str(errs))

    # inform user of completion
    info("All Processes Completed.")

def kickoff(ctx, operation: str):
    commands = generateAnaxScaleCommands(ctx, operation)
    remoteRun(ctx, commands)


@click.group()
@click.option('--locallog', '-l', type=int, default=0, show_default=True, help="0=debug, 1=info, 2=produciton, 3=error, 4=critical")
@click.option('--remotelog', '-r', type=int, default=0, show_default=True, help="0=debug, 1=info, 2=produciton, 3=error, 4=critical")
@click.option('--count', '-c', type=int, default=1, show_default=True, help="Number of horizon containers")
@click.option('--configfile', '-f', type=str, required=True, help="File containing configuration json")
@click.pass_context
def cli(ctx, configfile, count, remotelog, locallog):
    """The EdgeScaler product is a Master-Slave distributed scale analysis platform.  It controls remote execution using
using the scale.anaxremote python module.  The scale.anaxremote master application performs non-interactive ssh
execution of the scale.anaxscale python module on slave nodes.  The scale.anaxscale slave application executes 0..*
hzn, horizon-container, and docker operations."""
    # create logging
    global logger
    lglvl_local = logging.INFO
    if locallog == 0:
        lglvl_local = logging.DEBUG
    elif locallog == 1:
        lglvl_local = logging.INFO
    elif locallog >= 2:
        lglvl_local = logging.WARNING

    #Only log levels used are 0-2 so comment out the rest
    #elif locallog == 3:
    #    lglvl_local = logging.ERROR
    #elif locallog == 4:
    #    lglvl_local = logging.CRITICAL

    logger.setLevel(lglvl_local)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(lglvl_local)

    # create formatter
    # formatter = logging.Formatter('%(message)s')

    # add formatter to ch
    # ch.setFormatter(formatter)

    # add ch to logging
    logger.addHandler(ch)

    #Loads JSON Configuration File
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
        cflag: count
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
@click.pass_context
def eventlog(ctx, mmode, smode):
    """Collect eventlogs for all containers on all hosts"""
    ctx.obj[mmflag] = mmode
    ctx.obj[smflag] = smode
    operation = eventlogOp + " --" + smflag + " " + str(smode)
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

cli.add_command(queryrunning)
cli.add_command(validaterunning)
cli.add_command(prune)

cli.add_command(dockercp)
cli.add_command(dockerexec)
cli.add_command(containerconfigupdate)

if __name__ == '__main__':
    cli()