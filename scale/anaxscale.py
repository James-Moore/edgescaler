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
import logging
import datetime
import shlex


logger = logging.getLogger(__name__)
docker_socket="docker.socket"
docker_service="docker.service"
dockerOp="docker"
cpOp="cp"
execOp="exec"
cflag = 'count'
aflag = 'anax'
oflag = 'organization'
smflag = "smode"
mode_parallel = 0
mode_pseudoserial = 1
mode_serial = 2
pseudoDelay=.2
hznprefix = 'horizon'
hzncmd = 'hzn'
baseport = 8080
hostname = socket.gethostname()
uuidlog = open("uuid.log","a+")



def timestamp()->str:
    return "["+str(datetime.datetime.now()).split('.')[0]+"]\t"

def debug(out):
    logger.debug(timestamp()+str(out))

def info(out):
    logger.info(timestamp()+str(out))

def warning(out):
    logger.warning(timestamp()+str(out))

def error(out):
    logger.error(timestamp()+str(out))

def isSerial(mode: int)->bool:
    return mode == mode_serial

def isPseudoSerial(mode: int)->bool:
    return mode == mode_pseudoserial

def isParallel(mode: int)->bool:
    return mode == mode_parallel

def generateHorizonURL(index: int)->str:
    port = baseport + index
    HORIZON_URL = "http://localhost:" + str(port)
    return HORIZON_URL

def generateUniqueNodeAuth():
    unique = generateUniqueNodeName()+":"+generageUniqueNodeToken()
    print(unique, file=uuidlog)
    return unique

def generageUniqueNodeToken():
    return str(uuid4())

def generateUniqueNodeName():
    return str(uuid4())+"."+hostname

def generateNodeAuth(index: int):
    unique = hostname+"_"+hznprefix+str(index)+":"+"repeatabletoken"
    print(unique, file=uuidlog)
    return unique

def buildHorizonContainerCommands(ctx, args: [str], containers: [int])->[]:
    commands = []
    cmd = ctx.obj[aflag]
    for container in containers:
        # build the list to send as the args parameter to subprocess.call
        callList = buildHorizonContainerCommand(cmd, args, container)
        commands.append(callList)
    return commands

#returns the list built from a command, its arguments, and a count
def buildHorizonContainerCommand(cmd: str, args: [str], container: int)->[]:
    cmdAsList = [cmd]
    countAsList = [str(container)] #creating a list of strings to return in this method so we have to convert to string array element
    callList = cmdAsList + args + countAsList #concat all elements into a single list
    return callList #return the call list

#Make the attribute lists.  Each list will be associated with a running anax container
def generateRegAttrLists(org: str, pattern: str, containers: [int])->[str]:
    attrLists = []
    for i in containers:
        #attrLists.append(["register", "-n", generateUniqueNodeAuth(), org, pattern])
        attrLists.append(["register", "-v", "-n", generateNodeAuth(i), org, pattern])

    return attrLists

#Make the attribute lists.  Each list will be associated with a running anax container
def generateUnregAttrLists(containers: [int])->[str]:
    attrLists = []
    for i in containers:
        attrLists.append(["unregister", "-v", "-f", "-r"])
    return attrLists

#Make the attribute lists.  Each list will be associated with a running anax container
def generateEventlogAttrLists(containers: [int])->[str]:
    attrLists = []
    for i in containers:
        attrLists.append(["eventlog", "list", "-v", "-a"])
    return attrLists

#get the list of indexes assosciated with containers that are running from 1..COUNT
def getRunningContainerList(count: int)->[int]:
    client = docker.from_env()

    containers2stop = []

    # generate list of running anax containers
    for i in range(count):
        index = i+1 #accouting for the fact that there is non-zero indexing in AIC horizon-container
        try:
            name = hznprefix+str(index) #name of the horizon container
            out = client.containers.get(name) #check if the container exists
            containers2stop.append(index) #if it does then add the index of the running container to the list
        except:
            #if the container does not exist then do nothing
            pass

    #return list of running containers
    return containers2stop

#get the names of all running anax containers
def getRunningAnaxContainerNames()->[str]:
    client = docker.from_env()

    names = []

    for container in client.containers.list(filters={"name": "horizon"}):
        cenv = container.attrs['Config']['Env']
        for val in cenv:
            sval = val.split('=')
            if sval[0] == 'DOCKER_NAME' and sval[1].startswith('horizon'):
                names.append(sval[1])

    return names

def getContainersList(count: int)->[]:
    containers = []
    for i in range(count):
        containers.append(i+1)
    return containers

def isAnaxRunning(index: int)->bool:
    return hznprefix+str(index) in getRunningAnaxContainerNames()

#Executes every command in the array
def executeCommands(ctx, commands: [str])->bool:
    cmd = ctx.obj[aflag]
    runmode = ctx.obj[smflag]
    processes = []

    #Use subprocess to run the command 'count' number of times
    for command in commands:
        debug("Calling: "+str(command))
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        processes.append(p)
        # User defined mode of operation
        if isPseudoSerial(runmode):
            debug(str(["Sleeping: " + str(pseudoDelay)]))
            time.sleep(pseudoDelay)
        elif isSerial(runmode):
            debug("Waiting for process to complete before continuing...")
            p.wait()

    debug("All Processes Scheduled...  Waiting for completion... Do not interupt..")

    output = []
    for process in processes:
        debug("Waiting for: " + str(process.pid))
        process.wait()  # wait for all processes to run to completion
        outs = str()
        errs = str()
        try:
            errs, outs = process.communicate()
        except TimeoutExpired:
            pass

        output.append(timestamp() + "\n"+str(outs).rstrip() + str(errs).rstrip())


    for out in output:
        logger.info(out) #timestamps added in while loop above so nno need to call info() which adds its own timestamp

    debug("All Processes Complted.")
    return True


#executes a single hzn command
def executeSingleHzn(cmd: str, argList: [str], index: int)->str:
    HORIZON_URL = generateHorizonURL(index)
    os.environ["HORIZON_URL"] = HORIZON_URL

    #verify that the command exists
    if not shutil.which(cmd):
        debug("The required command " + hzncmd + " has not been found.")
        raise Exception()

    #verify that the indexed anax container is running
    if not isAnaxRunning(index):
        debug("Anax container " + hznprefix+str(index) + " is not running.")
        raise Exception()

    callList = [cmd] + argList
    debug("Call: " + HORIZON_URL)
    debug("Call: " + str(callList))
    out = subprocess.check_output(callList)

    return out

#This fucntion wraps hzn operations
def executeHZN(ctx, hznattrLists: [], containers: [int], print: bool)->bool:
    cmd = hzncmd
    result = False
    processes = []
    runmode = ctx.obj[smflag]
    #verify that the command exists
    if shutil.which(cmd):

        i = 0
        #Use subprocess to run the command 'count' number of times
        for container in containers:
            # build the list to send as the args parameter to subprocess.call
            callList = [cmd]+hznattrLists.pop()

            HORIZON_URL = generateHorizonURL(container)
            os.environ["HORIZON_URL"] = HORIZON_URL

            debug("Call"+str(container)+": " + HORIZON_URL)
            debug("Call"+str(container)+": " + str(callList))

            p = subprocess.Popen(callList, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            processes.append([HORIZON_URL, p])
            # User defined mode of operation
            if isPseudoSerial(runmode):
                debug(str(["Sleeping: " + str(pseudoDelay)]))
                time.sleep(pseudoDelay)
            elif isSerial(runmode):
                debug("Waiting for process to complete before continuing...")
                p.wait()

        debug("All Processes Scheduled...  Waiting for completion... Do not interupt..")

        output = []
        for arr in processes:
            hznurl=arr[0]
            process=arr[1]
            debug("Waiting for: "+str(process.pid))
            process.wait() #wait for all processes to run to completion
            if print:
                outs = str()
                errs = str()
                try:
                    errs, outs = process.communicate()
                except TimeoutExpired:
                    pass

                output.append(timestamp()+hostname+"\n"+hznurl+"\n"+str(outs).rstrip() + str(errs).rstrip())


        if print:
            for out in output:
                logger.info(out) #timestamps added in while loop above so nno need to call info() which adds its own timestamp

        debug("All Processes Completed.")
        result = True

    else:
        error("The required command "+cmd+" has not been found.")

    return result


@click.group()
@click.option('--log', '-l', type=int, default=1, show_default=True, help="0=debug, 1=info, 2=warning, 3=error, 4=critical")
@click.option('--count', '-c', type=int, default=1, show_default=True, help="Number of horizon containers")
@click.option('--anax', '-a', envvar="HZN_AIC", required=True, help="the location of ANAX_IN_CONTAINER's horizon-container script. Export HZN_AIC instead of cli flag")
@click.option('--organization', '-o', envvar="HZN_ORG_ID", required=True, help="Must set HZN_ORG_ID or pass flag")
@click.pass_context
def cli(ctx, organization, anax, count, log):
    """Used to control the Anax Docker Containers on this host.  All commands consume the count flag unless specified.
    To see which commands consume the count flag issue --help on the individual command.  The count flag replicates a
     given operation across containers 1..COUNT."""

    # create logging
    global logger
    lglvl = logging.INFO

    if log == 0:
        lglvl = logging.DEBUG
    elif log == 1:
        lglvl = logging.INFO
    elif log == 2:
        lglvl = logging.WARNING
    elif log == 3:
        lglvl = logging.ERROR
    elif log == 4:
        lglvl = logging.CRITICAL

    logger.setLevel(lglvl)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(lglvl)

    # create formatter
    #formatter = logging.Formatter('%(message)s')

    # add formatter to ch
    #ch.setFormatter(formatter)

    # add ch to logging
    logger.addHandler(ch)

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
    containers = getRunningContainerList(count)
    hznattrLists = generateRegAttrLists(org, pattern, containers)
    result = executeHZN(ctx, hznattrLists, containers, False)
    logger.info(result)


@click.command()
@click.option('--smode', '-s', envvar="HZN_SCLR_SLAVE_MODE", type=int, default=0, show_default=True, help="Change slave parallelisms: 0=parallel, 1=pseudoparallel, 2=serial")
@click.pass_context
def unregister(ctx, smode):
    """Unregisters the Anax Containers on this host"""
    ctx.obj[smflag] = smode
    count = ctx.obj[cflag]
    containers = getRunningContainerList(count)
    hznattrLists = generateUnregAttrLists(containers)
    result = executeHZN(ctx, hznattrLists, containers, False)
    logger.info(result)


@click.command()
@click.option('--smode', '-s', envvar="HZN_SCLR_SLAVE_MODE", type=int, default=0, show_default=True, help="Change slave parallelisms: 0=parallel, 1=pseudoparallel, 2=serial")
@click.pass_context
def eventlog(ctx, smode):
    """Collects the eventlogs for each container on this host"""
    ctx.obj[smflag] = smode
    count = ctx.obj[cflag]
    containers = getRunningContainerList(count)
    hznattrLists = generateEventlogAttrLists(containers)
    result = executeHZN(ctx, hznattrLists, containers, True)
    logger.info(result)


@click.command()
@click.pass_context
def start(ctx):
    """Starts Anax Containers on this host"""
    count = ctx.obj[cflag]
    containers = getContainersList(count)
    debug("Starting: " + str(containers))
    commands = buildHorizonContainerCommands(ctx,  ["start"], containers)
    result = executeCommands(ctx, commands)
    logger.info(result)


@click.command()
@click.pass_context
def stop(ctx):
    """Stops Anax Containers on this host"""
    count = ctx.obj[cflag]
    containers = getRunningContainerList(count)
    debug("Stopping: "+str(containers))
    commands = buildHorizonContainerCommands(ctx, ["stop"], containers)
    result = executeCommands(ctx, commands)
    logger.info(result)


@click.command()
@click.pass_context
def restart(ctx):
    """Restarts Anax Containers on this host"""
    count = ctx.obj[cflag]
    containers = getRunningContainerList(count)
    debug("Stopping: " + str(containers))
    commands = buildHorizonContainerCommands(ctx, ["restart"], containers)
    result = executeCommands(ctx, commands)
    logger.info(result)


@click.command()
@click.pass_context
def agreements(ctx):
    """Returns True if all agreements on this host are validated."""
    count = ctx.obj[cflag]
    callList = ['agreement', 'list']

    result = True

    for i in range(count):
        result = agreementWorker(i+1) and result

    logger.info(result)

def agreementWorker(index: int)->bool:
    result = False
    callList = ['agreement', 'list', "-v"]
    try:
        out = executeSingleHzn(hzncmd, callList, index)
        jout = json.loads(out)

        if len(jout) > 0:
            val = jout[0]["agreement_execution_start_time"]
            result = val != ""


        debug("AGREEMENT INFORMATION:\nHOSTNAME: "+hostname+"\nAGENT "+generateHorizonURL(index)+"\nAGREEMENT:\n"+json.dumps(jout))
    except:
        warning("Issue encountered executing: Node is "+hznprefix+str(index)+" Command is "+str([hzncmd]+callList))
        pass

    return result

@click.command()
@click.argument('anax_container_number',default=1)
def agreement(anax_container_number):
    """Returns True if an agreement has been established and is running; otherwise returns False. Note: Does not consume count flag.  Must pass container number as argument.  """
    result = agreementWorker(anax_container_number)
    logger.info(result)
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

    logger.info(result)

def runprocess(runlist: [str]) -> int:
    p = subprocess.Popen(runlist, stdout=subprocess.PIPE)
    p.wait()
    rc = p.returncode
    debug(str(runlist)+"..."+str(rc))
    return p.returncode

def servicestart(service: str) -> int:
    debug("CALLING SERVICE START: "+service)
    if serviceisactive(service): #if service is active stop it before trying to start it
        servicestop(service)

    rc = 0
    runlist = ["systemctl", "start", service]
    rc = runprocess(runlist)
    return rc

def servicestop(service: str) -> int:
    debug("CALLING SERVICE STOP: "+service)
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
        debug("Unregisters all agents.  Stops all containers, Prunes all docker elements, Restarts docker.socket and docker.service")
        ctx.obj[cflag]=len(client.containers.list())
        unregister(ctx)
    except:
        pass

    try:
        debug("Stoping all running containers...")
        client = docker.from_env()
        for container in client.containers.list():
            try:
                container.stop()
            except:
                pass
    except:
        pass

    try:
        debug("Pruning System...")
        pruneContainers = client.containers.prune()
        pruneImages = client.images.prune(filters={'dangling': False})
        pruneNetworks = client.networks.prune()
        pruneVolumes = client.volumes.prune()

        debug("Prune Containers: "+ str(pruneContainers))
        debug("Prune Images: " + str(pruneImages))
        debug("Prune Networks: " + str(pruneNetworks))
        debug("Prune Volumes: " + str(pruneVolumes))
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

    debug("CALLING ISACTIVE VALIDATIONS:")
    dcksctrc = serviceisactive(docker_socket)
    dcksvcrc = serviceisactive(docker_service)
    debug("IsActive - docker.socket: " + str(dcksctrc))
    debug("IsActive - docker.service: " + str(dcksvcrc))


@click.command()
@click.option('--list', '-l', is_flag=True, help="List anax containers running")
@click.option('--count', '-c', is_flag=True, help="Return the running anax container count")
@click.pass_context
def queryrunning(ctx, list, count):
    """Lists the names of running anax containers.  Note: Does not consume count flag"""
    if list:
        logger.info(str(getRunningAnaxContainerNames()))
    else:
        logger.info(str(len(getRunningAnaxContainerNames())))


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

        if(logger.isEnabledFor(logging.DEBUG)):
            debug(str(status))
        else:
            logger.info(running)


def dockercpworker(ctx, source, destination):
    count = ctx.obj[cflag]
    containers = getRunningContainerList(count)

    commands = []
    validations = []
    for container in containers:
        command = [dockerOp, cpOp, source, hznprefix + str(container) + ":" + destination]
        commands.append(command)
        validation = [dockerOp, "exec", "-i", hznprefix + str(container), "cat", destination]
        validations.append(validation)

    logger.info("Performing Docker CP")
    executeCommands(ctx, commands)

@click.command()
@click.option('--source', '-s', type=str, required=True, help="Source file/directory to be transfered")
@click.option('--destination', '-d', type=str, required=True, help="Destination file/directory to recieve transfer")
@click.pass_context
def dockercp(ctx, source, destination):
    """Executes Docker's cp command across every host in the configuration file for every container specified with -c"""
    dockerexecworker(ctx, source, destination)

def dockerexecworker(ctx, commandargument):
    count = ctx.obj[cflag]
    containers = getRunningContainerList(count)

    commands = []
    validations = []
    for container in containers:
        command = [dockerOp, execOp, "-i", hznprefix + str(container)] + list(commandargument)
        commands.append(command)

    logger.info("Performing Docker Exec")
    executeCommands(ctx, commands)

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
    logger.info("UPDATING CONTAINER CONFIGURATIONS")
    dockerexecworker(ctx, ("mkdir", "/root/scaler"))
    dockerexecworker(ctx, ("ls", "-al", "/root"))
    dockercpworker(ctx, "/root/scaler/tools/configupdate.sh", "/root/scaler/")
    dockerexecworker(ctx, ("ls", "-al", "/root/scaler"))
    dockerexecworker(ctx, ("/root/scaler/configupdate.sh", ""))
    logger.info("Contents of: /etc/horizon/anax.json")
    dockerexecworker(ctx, ("cat", "/etc/horizon/anax.json"))
    logger.info("Contents of: /root/scaler/anax.json")
    dockerexecworker(ctx, ("cat", "/root/scaler/anax.json"))
    logger.info("Copying: /root/scaler/anax.json to /etc/horizon/anax.json")
    dockerexecworker(ctx, ("cp", "/root/scaler/anax.json", "/etc/horizon/anax.json"))
    logger.info("Contents of: /etc/horizon/anax.json")
    dockerexecworker(ctx, ("cat", "/etc/horizon/anax.json"))


cli.add_command(start)
cli.add_command(restart)
cli.add_command(stop)

cli.add_command(register)
cli.add_command(unregister)

cli.add_command(agreements)
cli.add_command(agreement)
cli.add_command(eventlog)


cli.add_command(node)
cli.add_command(queryrunning)
cli.add_command(validaterunning)
cli.add_command(prune)

cli.add_command(dockercp)
cli.add_command(dockerexec)
cli.add_command(containerconfigupdate)

if __name__ == '__main__':
    cli()
