import time
import click
import os
import json
import logging
import subprocess
from subprocess import TimeoutExpired
from pprint import pprint

logger = logging.getLogger(__name__)
json_env = 'env'
json_endpoints = 'endpoints'
env_scaler_dir = "HZN_SCALER_DIR"
env_scaler_name = "HZN_SCALER_NAME"
rflag = "remotelog"
cflag = "count"
sflag = "serial"
serialDelay=.2

startOp = "start"
stopOp = "stop"
registerOp = "register"
registerPattern="IBM/pattern-ibm.helloworld"
unregisterOp = "unregister"
runningOp = "running"
agreementsOp = "agreements"
nodesOp = "node list"


@click.group()
@click.option('--locallog', '-l', type=int, default=0, show_default=True, help="0=debug, 1=info, 2=produciton, 3=error, 4=critical")
@click.option('--remotelog', '-r', type=int, default=0, show_default=True, help="0=debug, 1=info, 2=produciton, 3=error, 4=critical")
@click.option('--count', '-c', type=int, default=1, show_default=True, help="Number of horizon containers")
@click.option('--configfile', '-f', type=str, required=True, help="File containing configuration json")
@click.pass_context
def cli(ctx, configfile, count, remotelog, locallog):
    """Used to control the lifecycle of 1 or more Anax Docker Containers"""
    # create logger
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

    # add ch to logger
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
        sflag: False, #default the master-slave relatioship to parallel execution
        json_endpoints: j[json_endpoints],
        json_env: j[json_env],
        rflag: lglvl_remote,
        cflag: count
    }

def isSerial(ctx)->bool:
    return ctx.obj[sflag]

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

    if operation != runningOp:
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

    logger.info("Remote Operation...\n" + commands[0][2]+"\n")
    processes = {}
    #Kickoff all asynchronous processes
    for command in commands:
        logger.debug("Calling remote operation on: " + command[0]+" "+command[1])
        sshinfo = command[1] #this is the user@hostname portion of the ssh command
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        processes.update({sshinfo: p})

        #if the user has set the serial flag we should wait for the current host to complete execution
        #before continuing to the next host.

        if isSerial(ctx):
            cval = ctx.obj[cflag]
            dval = serialDelay
            sval = dval*cval*2
            logger.debug(str(["Delay: "+str(dval), "Count: "+str(cval), "Sleeping: "+str(sval)]))
            time.sleep(sval)

            #logger.debug("Waiting for process to complete before continuing...")
            #p.wait()




    logger.debug("")
    logger.info("All Processes Scheduled...  Waiting for completion... Do not interupt..")

    #Wait for all background processes
    for command in commands:
        sshinfo = command[1] #this is the user@hostname portion of the ssh command
        process = processes[sshinfo]
        logger.debug("Waiting for "+sshinfo+" with process "+str(process.pid))

        #aquire remote command's output
        outs = str()
        errs = str()
        try:
            errs, outs = process.communicate()
        except TimeoutExpired:
            process.kill()
            errs, outs = process.communicate()

        #print output according to local log level
        if(logger.getEffectiveLevel() >= logging.WARNING):
            logger.warning(str(outs).rstrip()+str(errs))
        else:
            logger.info("Connect: "+sshinfo+"\nSTDOUT: "+str(outs)+"STDERR: "+str(errs))

    # inform user of completion
    logger.info("All Processes Completed.")


def kickoff(ctx, operation: str):
    commands = generateAnaxScaleCommands(ctx, operation)
    remoteRun(ctx, commands)

@click.command()
@click.pass_context
def start(ctx):
    """Starts Anax Containers on all hosts (see count flag for >1 container)"""
    operation = startOp
    kickoff(ctx, operation)

@click.command()
@click.option('--serial', '-s', is_flag=True, help="Change default parallel execution to serial.")
@click.pass_context
def register(ctx, serial):
    """Registers the Anax Containers on all hosts with hello world (see count flag)"""
    ctx.obj[sflag]=serial

    operation = registerOp
    if serial:
        operation=operation+" --"+sflag

    operation = operation+" "+registerPattern

    kickoff(ctx, operation)

@click.command()
@click.option('--serial', '-s', is_flag=True, help="Change default parallel execution to serial.")
@click.pass_context
def unregister(ctx, serial):
    """Unregisters the Anax Containers on all hosts with hello world (see count flag)"""
    ctx.obj[sflag] = serial

    operation = unregisterOp
    if serial:
        operation = operation + " --" + sflag

    kickoff(ctx, operation)

@click.command()
@click.pass_context
def stop(ctx):
    """Stops Anax Containers on all hosts (see count flag for >1 container)"""
    operation = stopOp
    kickoff(ctx, operation)

@click.command()
@click.pass_context
def agreements(ctx):
    """Stops Anax Containers on all hosts (see count flag for >1 container)"""
    operation = agreementsOp
    kickoff(ctx, operation)

@click.command()
@click.option('--list', '-l', is_flag=True, help="List anax containers on each host")
@click.option('--count', '-c', is_flag=True, help="List anax container count on each host")
@click.pass_context
def running(ctx, list, count):
    """Lists the names of running anax containers"""
    operation = runningOp
    if list:
        operation = operation+" --list"
    else:
        operation = operation+" --count"

    kickoff(ctx, operation)

cli.add_command(start)
cli.add_command(register)
cli.add_command(unregister)
cli.add_command(stop)
cli.add_command(agreements)
cli.add_command(running)

if __name__ == '__main__':
    cli()
