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


logger = logging.getLogger(__name__)

docker_socket="docker.socket"
docker_service="docker.service"

cflag = 'count'
aflag = 'anax'
oflag = 'organization'

smflag = "smode"
mode_parallel = 0
mode_pseudoserial = 1
mode_serial = 2
pseudoDelay=1

hznprefix = 'horizon'
hzncmd = 'hzn'
baseport = 8080
hostname = socket.gethostname()

uuidlog = open("uuid.log","a+")


def generateHorizonURL(index: int)->str:
    port = baseport + index
    HORIZON_URL = "http://localhost:" + str(port)
    return HORIZON_URL

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

#save all the nodes created by this script because I have no idea what happens to them on the exchange
#do they persist forever???
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


#returns the list built from a command, its arguments, and a count
def buildCallList(cmd: str, args: [str], container: int)->[]:
    cmdAsList = [cmd]
    countAsList = [str(container)] #must be a list of strings
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


#executes a single command against an individual container rathern than a command for each container
def singleHznCommand(cmd: str, argList: [str], index: int)->str:
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

#This fucntion wraps anax_in_container horizon-container operations.  It is essentially AIC_HC*
def executeAnaxInContainer(ctx, args: [str], containers: [int])->bool:
    cmd = ctx.obj[aflag]
    runmode = ctx.obj[smflag]
    result = False
    processes = []
    #verify that the command exists
    if shutil.which(cmd):
        #Use subprocess to run the command 'count' number of times
        for container in containers:
            # build the list to send as the args parameter to subprocess.call
            callList = buildCallList(cmd, args, container)
            debug("Call" + str(container) + ": " + str(callList))
            p = subprocess.Popen(callList, stdout=subprocess.PIPE)
            processes.append(p)
            # User defined mode of operation
            if isPseudoSerial(runmode):
                debug(str(["Sleeping: " + str(pseudoDelay)]))
                time.sleep(pseudoDelay)
            elif isSerial(runmode):
                debug("Waiting for process to complete before continuing...")
                p.wait()

        debug("All Processes Scheduled...  Waiting for completion... Do not interupt..")

        for process in processes:
            debug("Waiting for: " + str(process.pid))
            process.wait()  # wait for all processes to run to completion

        debug("All Processes Complted.")
        result = True

    else:
        error("The required command "+cmd+" has not been found.")

    return result

#This fucntion wraps anax_in_container horizon-container operations.  It is essentially AIC_HC*
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
    """Used to control the lifecycle of 1 or more Anax Docker Containers"""
    # create logger
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

    # add ch to logger
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
    """Registers the Anax Containers with hello world (see count flag)"""
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
    """Registers the Anax Containers with hello world (see count flag)"""
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
    """Registers the Anax Containers with hello world (see count flag)"""
    ctx.obj[smflag] = smode
    count = ctx.obj[cflag]
    containers = getRunningContainerList(count)
    hznattrLists = generateEventlogAttrLists(containers)
    result = executeHZN(ctx, hznattrLists, containers, True)
    logger.info(result)

@click.command()
@click.pass_context
def start(ctx):
    """Starts Anax Containers (see count flag for >1 container)"""
    count = ctx.obj[cflag]
    containers = getContainersList(count)
    debug("Starting: " + str(containers))
    result = executeAnaxInContainer(ctx, ["start"], containers)
    logger.info(result)

@click.command()
@click.pass_context
def stop(ctx):
    """Stops Anax Containers (see count flag for >1 container)"""
    count = ctx.obj[cflag]
    containers = getRunningContainerList(count)
    debug("Stopping: "+str(containers))
    result = executeAnaxInContainer(ctx, ["stop"], containers)
    logger.info(result)

@click.command()
@click.pass_context
def restart(ctx):
    """Restarts Docker Containers (see count flag for >1 container)"""
    count = ctx.obj[cflag]
    containers = getRunningContainerList(count)
    debug("Stopping: " + str(containers))
    result = executeAnaxInContainer(ctx, ["restart"], containers)
    logger.info(result)

@click.command()
@click.pass_context
def agreements(ctx):
    """Returns True if agreements for containers 1..Count are validated. Uses count flag."""
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
        out = singleHznCommand(hzncmd, callList, index)
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
    """Returns True if an agreement has been established and is running; otherwise returns False"""
    result = agreementWorker(anax_container_number)
    logger.info(result)
    return result

@click.command()
@click.argument('anax_container_number',default=1)
def node(anax_container_number):
    """Returns True if node has been registered; otherwise returns False"""
    result = False
    callList = ['node', 'list', "-v"]

    try:
        out = singleHznCommand(hzncmd, callList, anax_container_number)
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
        debug("Unregistering all agents that may be running and registered...")
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
    """Lists the names of running anax containers"""
    if list:
        logger.info(str(getRunningAnaxContainerNames()))
    else:
        logger.info(str(len(getRunningAnaxContainerNames())))

@click.command()
@click.pass_context
def validaterunning(ctx):
    """Validates containers have transitioned to running"""
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




cli.add_command(eventlog)
cli.add_command(validaterunning)
cli.add_command(queryrunning)
cli.add_command(prune)
cli.add_command(node)
cli.add_command(agreements)
cli.add_command(agreement)
cli.add_command(unregister)
cli.add_command(register)
cli.add_command(restart)
cli.add_command(stop)
cli.add_command(start)

if __name__ == '__main__':
    cli()
