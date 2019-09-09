import subprocess
from subprocess import TimeoutExpired
import shutil
import click
import docker
import os
import time
import socket
from uuid import uuid4
import json
import datetime
import logging
from scale import *
from scale.logger import Logger
from scale.manager import Manager
from scale.operation import Operation
from scale.horizonhelper import HorizonHelper
from scale.commandhelper import CommandHelper
from scale.dockerhelper import DockerHelepr



hhelper = HorizonHelper()
chelper = CommandHelper()
dhelper = DockerHelepr()

hostname = socket.gethostname()
logger = Logger(__name__)
manager = Manager(logger)

def isAnaxRunning(index: int)->bool:
    return hznprefix+str(index) in dhelper.getRunningAnaxContainerNames()

#executes a single hzn command
def executeSingleHzn(cmd: str, argList: [str], index: int)->str:
    HORIZON_URL = hhelper.generateHorizonURL(index)
    os.environ["HORIZON_URL"] = HORIZON_URL

    #verify that the command exists
    if not shutil.which(cmd):
        logger.debug("The required command " + hzncmd + " has not been found.", newline=True)
        raise Exception()

    #verify that the indexed anax container is running
    if not isAnaxRunning(index):
        logger.debug("Anax container " + hznprefix+str(index) + " is not running.", newline=True)
        raise Exception()

    callList = [cmd] + argList
    logger.debug("Call: " + HORIZON_URL, newline=True)
    logger.debug("Call: " + str(callList), newline=True)
    out = subprocess.check_output(callList)

    return out



@click.group()
@click.option('--workerpseudodelay', envvar="HZN_SCLR_WORKER_PSEUDODELAY", type=float, default=0.2, show_default=True, help="Worker node delay if runmode is set to pseudoparallel")
@click.option('--log', '-l', type=int, default=1, show_default=True, help="0=debug, 1=info, 2=warning, 3=error, 4=critical")
@click.option('--count', '-c', type=int, default=1, show_default=True, help="Number of horizon containers")
@click.option('--anax', '-a', envvar="HZN_AIC", required=True, help="the location of ANAX_IN_CONTAINER's horizon-container script. Export HZN_AIC instead of cli flag")
@click.option('--organization', '-o', envvar="HZN_ORG_ID", required=True, help="Must set HZN_ORG_ID or pass flag")
@click.pass_context
def cli(ctx, organization, anax, count, log, workerpseudodelay):
    """Used to control the Anax Docker Containers on this host.  All commands consume the count flag unless specified.
    To see which commands consume the count flag issue --help on the individual command.  The count flag replicates a
     given operation across containers 1..COUNT."""

    global pseudoDelay
    pseudoDelay = workerpseudodelay

    # create logging
    global logger
    logger.setupLogger(loglevel=log)

    ctx.obj = {
        cflag: count,
        aflag: anax,
        oflag: organization,
        smflag: mode_parallel  # default slave execution mode
    }


@click.command()
@click.option('--smode', '-s', envvar="HZN_SCLR_SLAVE_MODE", type=int, default=0, show_default=True, help="Change slave parallelisms: 0=parallel, 1=pseudoparallel, 2=serial")
@click.argument('pattern')
@click.pass_context
def register(ctx, smode, pattern):
    """Registers the Anax Containers with hello world on this host"""
    ctx.obj[smflag] = smode
    count = ctx.obj[cflag]
    org = ctx.obj[oflag]
    containers = dhelper.getRunningContainerList(count)

    #Debugging Start
    logger.debug("REGISTER: Running Agent Containers...", newline=True)
    for container in containers:
        logger.debug(hhelper.generateNodeAuth(hostname=hostname, containerIndex=container), newline=True)
    #Debugging End

    hznattrLists = hhelper.generateRegAttrLists(org=org, pattern=pattern, hostname=hostname, containers=containers)

    # Debugging Start
    logger.debug("REGISTER: Attribute Lists to execute...", newline=True)
    for hznattr in hznattrLists:
        logger.debug(hznattr, newline=True)
    # Debugging End

    logger.debug("REGISTER: Execute HZN on Attribute lists STARTED", newline=True)
    operations = hhelper.generateHorizonOperations(hznattrLists, containers, logger)
    manager.run(runmode=smode, operations=operations)
    logger.debug("REGISTER: Execute HZN on Attribute lists COMPLETED", newline=True)


@click.command()
@click.option('--smode', '-s', envvar="HZN_SCLR_SLAVE_MODE", type=int, default=0, show_default=True, help="Change slave parallelisms: 0=parallel, 1=pseudoparallel, 2=serial")
@click.pass_context
def unregister(ctx, smode):
    """Unregisters the Anax Containers on this host"""
    ctx.obj[smflag] = smode
    count = ctx.obj[cflag]
    containers = dhelper.getRunningContainerList(count)
    hznattrLists = hhelper.generateUnregAttrLists(containers)
    operations = hhelper.generateHorizonOperations(hznattrLists, containers, logger)
    manager.run(runmode=smode, operations=operations)

@click.command()
@click.option('--smode', '-s', envvar="HZN_SCLR_SLAVE_MODE", type=int, default=0, show_default=True, help="Change slave parallelisms: 0=parallel, 1=pseudoparallel, 2=serial")
@click.option('--eventlogflags', '-e', type=str, default="va", show_default=True, help="Flag values for hzn eventlog list")
@click.pass_context
def eventlog(ctx, smode, eventlogflags):
    """Collects the eventlogs for each container on this host"""
    ctx.obj[smflag] = smode
    count = ctx.obj[cflag]
    containers = dhelper.getRunningContainerList(count)
    hznattrLists = hhelper.generateEventlogAttrLists(containers, eventlogflags)
    operations = hhelper.generateHorizonOperations(hznattrLists, containers, logger)
    manager.run(runmode=smode, operations=operations)

@click.command()
@click.option('--logdir', '-o', type=str, required=True, help="Logging Directory")
@click.pass_context
def agentlogs(ctx, logdir):
    """Acquires all agent container logs on this host"""
    logger.info("Capturing agent logs on " + hostname, timestamp=False)
    client = docker.from_env()
    p = os.path.join(logdir, syslogs_capturedir)
    os.makedirs(p, exist_ok=True)
    p = os.path.join(p, hostname)
    os.makedirs(p, exist_ok=True)

    #for container in client.containers.list(filters={"name": "horizon"}):
    for container in client.containers.list(all=True, filters={"name": "horizon"}):
        containerName = container.attrs['Name']

        #remove the '/' character from the default docker api behavior of returning the container name
        #with the format '/NAME'.  The reformatting makes it compatable with the rest of this harness'
        #codebase
        if containerName[0] == "/":
            containerName = containerName[1:]

        clog = container.logs()

        alog = os.path.join(p, hostname+"_"+containerName+".log")
        with open(alog, 'w') as alogFile:
            alogFile.write(clog)

        if(logger.logger.isEnabledFor(logging.DEBUG)): #totally bizzare check to see if the python logger in Logger is enabled for DEBUG and if so then print to debug level
            logger.debug(str("Agent log "+hostname+"_"+containerName+" written."))

    logger.info("Agent Logs on "+hostname+" capture.", timestamp=False)

@click.command()
@click.pass_context
def start(ctx):
    """Starts Anax Containers on this host"""
    environment = os.environ.copy()
    aicCommand = ctx.obj[aflag]
    count = ctx.obj[cflag]

    containers = dhelper.produceIndicesList(count)
    runningContainers = dhelper.getRunningContainerList(count)
    for running in runningContainers:
        if running in containers:
            containers.remove(running)

    tries=0

    while ( (len(containers) != 0) or (tries<2) ):
        logger.debug("Starting: " + str(containers) + ", Attempt: " + str(tries), newline=True)
        operations = chelper.generateHorizonContainerCommands(environment=environment, aicCommand=aicCommand, arg="start", containers=containers, logger=logger)
        manager.run(runmode=mode_parallel, operations=operations)

        runningContainers = dhelper.getRunningContainerList(count)
        for running in runningContainers:
            if running in containers:
                containers.remove(running)

        tries=tries+1


@click.command()
@click.pass_context
def stop(ctx):
    """Stops Anax Containers on this host"""
    environment = os.environ.copy()
    aicCommand = ctx.obj[aflag]
    count = ctx.obj[cflag]
    containers = dhelper.getRunningContainerList(count)
    logger.debug("Stopping: "+str(containers), newline=True)
    operations = chelper.generateHorizonContainerCommands(environment=environment, aicCommand=aicCommand, arg="stop", containers=containers, logger=logger)
    manager.run(runmode=mode_parallel, operations=operations)

@click.command()
@click.pass_context
def restart(ctx):
    """Restarts Anax Containers on this host"""
    environment = os.environ.copy()
    aicCommand = ctx.obj[aflag]
    count = ctx.obj[cflag]
    containers = dhelper.getRunningContainerList(count)
    logger.debug("Stopping: " + str(containers), newline=True)
    operations = chelper.generateHorizonContainerCommands(environment=environment, aicCommand=aicCommand, arg="restart", containers=containers, logger=logger)
    manager.run(runmode=mode_parallel, operations=operations)

@click.command()
@click.pass_context
def agreements(ctx):
    """Returns True if all agreements on this host are validated."""
    count = ctx.obj[cflag]
    callList = ['agreement', 'list']

    result = True

    for i in range(count):
        result = agreementWorker(i+1) and result

    logger.info(result, timestamp=False)

def agreementWorker(index: int)->bool:
    result = False
    callList = ['agreement', 'list', "-v"]
    try:
        out = executeSingleHzn(hzncmd, callList, index)
        jout = json.loads(out)

        if len(jout) > 0:
            val = jout[0]["agreement_execution_start_time"]
            result = val != ""


        logger.debug("AGREEMENT INFORMATION:\nHOSTNAME: "+hostname+"\nAGENT "+hhelper.generateHorizonURL(index)+"\nAGREEMENT:\n"+json.dumps(jout), newline=True)
    except:
        logger.debug("Issue encountered executing: Node is "+hznprefix+str(index)+" Command is "+str([hzncmd]+callList), newline=True)
        pass

    return result

@click.command()
@click.argument('anax_container_number',default=1)
def agreement(anax_container_number):
    """Returns True if an agreement has been established and is running; otherwise returns False. Note: Does not consume count flag.  Must pass container number as argument.  """
    result = agreementWorker(anax_container_number)
    logger.info(result, timestamp=False)
    return result


@click.command()
@click.argument('anax_container_number',default=1)
def node(anax_container_number):
    """Returns True if node has been configured; otherwise returns False. Note: Does not consume count flag.  Must pass container number as argument.  """
    result = False
    callList = ['node', 'list', "-v"]

    try:
        out = executeSingleHzn(hzncmd, callList, anax_container_number)
        jout = json.loads(out)

        if len(jout) > 0:
            val = jout["configstate"]["state"]
            result = val == "configured"

    except:
        pass

    logger.info(result, timestamp=False)

def runprocess(runlist: [str]) -> int:
    p = subprocess.Popen(runlist, stdout=subprocess.PIPE)
    p.wait()
    rc = p.returncode
    logger.debug(str(runlist)+"..."+str(rc), newline=True)
    return p.returncode

def servicestart(service: str) -> int:
    logger.debug("CALLING SERVICE START: "+service, newline=True)
    if serviceisactive(service): #if service is active stop it before trying to start it
        servicestop(service)

    rc = 0
    runlist = ["systemctl", "start", service]
    rc = runprocess(runlist)
    return rc

def servicestop(service: str) -> int:
    logger.debug("CALLING SERVICE STOP: "+service, newline=True)
    rc=0
    if serviceisactive(service):
        runlist = ["systemctl", "stop", service]
        rc=runprocess(runlist)
    return rc

def serviceisactive(service: str) -> bool:
    runlist = ["systemctl", "is-active", service]
    rc = runprocess(runlist)
    return (rc == 0)

@click.command()
@click.pass_context
def prune(ctx):
    """Ensures there is a clean environment for scale testing"""
    client = docker.from_env()

    try:
        logger.debug("Unregisters all agents.  Stops all containers, Prunes all docker elements, Restarts docker.socket and docker.service", newline=True)
        ctx.obj[cflag]=len(client.containers.list())
        unregister(ctx)
    except:
        pass

    try:
        logger.debug("Stoping all running containers...", newline=True)
        client = docker.from_env()
        for container in client.containers.list():
            try:
                container.stop()
            except:
                pass
    except:
        pass

    try:
        logger.debug("Pruning System...", newline=True)
        pruneContainers = client.containers.prune()
        pruneImages = client.images.prune(filters={'dangling': False})
        pruneNetworks = client.networks.prune()
        pruneVolumes = client.volumes.prune()

        logger.debug("Prune Containers: "+ str(pruneContainers), newline=True)
        logger.debug("Prune Images: " + str(pruneImages), newline=True)
        logger.debug("Prune Networks: " + str(pruneNetworks), newline=True)
        logger.debug("Prune Volumes: " + str(pruneVolumes), newline=True)
    except:
        pass

    #clear syslog
    try:
        open("/var/log/syslog", "w").close()
    except:
        pass


    servicestop(docker_socket)
    servicestop(docker_service)

    servicestart(docker_socket)
    servicestart(docker_service)

    logger.debug("CALLING ISACTIVE VALIDATIONS:", newline=True)
    dcksctrc = serviceisactive(docker_socket)
    dcksvcrc = serviceisactive(docker_service)
    logger.debug("IsActive - docker.socket: " + str(dcksctrc), newline=True)
    logger.debug("IsActive - docker.service: " + str(dcksvcrc), newline=True)


@click.command()
@click.option('--list', '-l', is_flag=True, help="List anax containers running")
@click.option('--count', '-c', is_flag=True, help="Return the running anax container count")
@click.pass_context
def queryrunning(ctx, list, count):
    """Lists the names of running anax containers.  Note: Does not consume count flag"""
    if list:
        logger.info(str(dhelper.getRunningAnaxContainerNames()), timestamp=False)
    else:
        logger.info(str(len(dhelper.getRunningAnaxContainerNames())), timestamp=False)


@click.command()
@click.pass_context
def validaterunning(ctx):
    """Validates containers have transitioned to running.  Note: Does not consume count flag."""
    client = docker.from_env()
    #for container in client.containers.list(filters={"name": "horizon"}):
    for container in client.containers.list(all=True, filters={"name": "horizon"}):
        containerName = container.attrs['Name']

        #remove the '/' character from the default docker api behavior of returning the container name
        #with the format '/NAME'.  The reformatting makes it compatable with the rest of this harness'
        #codebase
        if containerName[0] == "/":
            containerName = containerName[1:]

        running = container.attrs['State']['Running']
        status = {
            "Host": hostname,
            "Container": containerName,
            "Running": running
                  }

        if(logger.logger.isEnabledFor(logging.DEBUG)):
            logger.debug(str(status))
        else:
            logger.info(running, timestamp=False)


def dockercpworker(ctx, source, destination):
    count = ctx.obj[cflag]
    containers = dhelper.getRunningContainerList(count)

    operations = []
    for container in containers:
        command = [dockerOp, cpOp, source, hznprefix + str(container) + ":" + destination]
        operation = Operation(operation=command, logger=logger)
        operations.append(operation)

    logger.info("Performing Docker CP", timestamp=False)
    manager.run(runmode=mode_parallel, operations=operations)

@click.command()
@click.option('--source', '-s', type=str, required=True, help="Source file/directory to be transfered")
@click.option('--destination', '-d', type=str, required=True, help="Destination file/directory to recieve transfer")
@click.pass_context
def dockercp(ctx, source, destination):
    """Executes Docker's cp command across every host in the configuration file for every container specified with -c"""
    dockerexecworker(ctx, source, destination)

def dockerexecworker(ctx, commandargument):
    count = ctx.obj[cflag]
    containers = dhelper.getRunningContainerList(count)

    operations = []
    for container in containers:
        command = [dockerOp, execOp, "-i", hznprefix + str(container)] + list(commandargument)
        operation = Operation(operation=command, logger=logger)
        operations.append(operation)

    logger.info("Performing Docker Exec", timestamp=False)
    manager.run(runmode=mode_parallel, operations=operations)

@click.command()
@click.argument('commandargument', nargs=-1)
@click.pass_context
def dockerexec(ctx, commandargument):
    """Executes Docker's exec command on the passed in argment"""
    dockerexecworker(ctx, commandargument)

@click.command()
@click.pass_context
def containerconfigupdate(ctx):
    """[Temporary Command] Used to perform an update on all containers anax.json files"""
    logger.info("UPDATING CONTAINER CONFIGURATIONS", timestamp=False)
    dockerexecworker(ctx, ("mkdir", "/root/scaler"))
    dockerexecworker(ctx, ("ls", "-al", "/root"))
    dockercpworker(ctx, "/root/scaler/tools/configupdate.sh", "/root/scaler/")
    dockerexecworker(ctx, ("ls", "-al", "/root/scaler"))
    dockerexecworker(ctx, ("/root/scaler/configupdate.sh", ""))
    logger.info("Contents of: /etc/horizon/anax.json", timestamp=False)
    dockerexecworker(ctx, ("cat", "/etc/horizon/anax.json"))
    logger.info("Contents of: /root/scaler/anax.json", timestamp=False)
    dockerexecworker(ctx, ("cat", "/root/scaler/anax.json"))
    logger.info("Copying: /root/scaler/anax.json to /etc/horizon/anax.json", timestamp=False)
    dockerexecworker(ctx, ("cp", "/root/scaler/anax.json", "/etc/horizon/anax.json"))
    logger.info("Contents of: /etc/horizon/anax.json", timestamp=False)
    dockerexecworker(ctx, ("cat", "/etc/horizon/anax.json"))


cli.add_command(start)
cli.add_command(restart)
cli.add_command(stop)

cli.add_command(register)
cli.add_command(unregister)

cli.add_command(agreements)
cli.add_command(agreement)
cli.add_command(eventlog)
cli.add_command(agentlogs)

cli.add_command(node)
cli.add_command(queryrunning)
cli.add_command(validaterunning)
cli.add_command(prune)

cli.add_command(dockercp)
cli.add_command(dockerexec)
cli.add_command(containerconfigupdate)

if __name__ == '__main__':
    cli()
