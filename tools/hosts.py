import time
import json
import logging
import click
import subprocess
from subprocess import TimeoutExpired
from scale import anaxremote
from pprint import pprint

logger = logging.getLogger(__name__)
pflag="prefix"
dflag="domain"
cflag="count"
sflag = "serial"
srcflag="source"
dstflag="destination"
vcmd = "hostname"
json_env = 'env'
json_endpoints = 'endpoints'




def setupLogging(loglevel: int):
    """Used to control the lifecycle of 1 or more Anax Docker Containers"""
    global logger
    lglvl_local = logging.INFO
    if loglevel == 0:
        lglvl_local = logging.DEBUG
    elif loglevel == 1:
        lglvl_local = logging.INFO
    elif loglevel >= 2:
        lglvl_local = logging.WARNING

    logger.setLevel(lglvl_local)
    ch = logging.StreamHandler()
    ch.setLevel(lglvl_local)
    logger.addHandler(ch)

def isSerial(ctx)->bool:
    return ctx.obj[sflag]

def generateHostnames(ctx)->[str]:
    list=[]
    for i in range(ctx.obj[cflag]):
        hostname = ctx.obj[pflag]+str(i+1).zfill(2)+"."+ctx.obj[dflag]
        list.append(hostname)
    return list

def generateCmds(hostnames: [str], cmd: str)->[str]:
    result = []
    for hostname in hostnames:
        sshcmd = anaxremote.generateSshLogin(hostname)
        valcmd = sshcmd+[cmd]
        result.append(valcmd)
    return result

def generateValidationCmds(hostnames: [str])->[str]:
    return generateCmds(hostnames, vcmd)

def generageScpCmds(source: str, destination: str, hostnames: [str]):
    result = []
    for hostname in hostnames:
        command = ["scp", "-r", source, "root@"+hostname+":"+destination]
        result.append(command)
    return result


def run(ctx, commands: [str]):
    logger.debug("Scheduling all commands...")
    processes = {}
    #Kickoff all asynchronous processes
    for command in commands:
        sshinfo = str(command) #this is the user@hostname portion of the ssh command
        logger.info("Scheduling: "+sshinfo)
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        processes.update({sshinfo: p})

        if isSerial(ctx):
            time.sleep(.05)

    logger.debug("")
    logger.debug("Processes Scheduled...  Waiting for completion... Do not interupt..\n")

    failed = []
    #Wait for all background processes
    for command in commands:
        sshinfo = str(command)
        process = processes[sshinfo]

        #aquire remote command's output
        outs = str()
        errs = str()
        try:
            errs, outs = process.communicate(timeout=2)
        except TimeoutExpired:
            process.kill()
            errs, outs = process.communicate()
            failed.append(command)

        #print output according to local log level
        out=str(outs).rstrip()+str(errs).rstrip()
        if(out != ""):
            logger.info(out)


    # inform user of completion
    logger.info("All Processes Completed.")

    if len(failed) > 0:
        logger.info("Encountered the following failures:")
        for failure in failed:
            logger.info(str(failure))

def loadConfig(ctx, configfile: str):
    f = open(file=configfile)
    j = json.loads(f.read())
    ctx.obj[json_endpoints]=j[json_endpoints]
    ctx.obj[json_env]=j[json_env]

@click.group()
@click.option('--loglevel', '-l', type=int, default=0, show_default=True, help="0=debug, 1=info, 2=produciton, 3=error, 4=critical")
@click.option('--serial', '-s', is_flag=True, help="Change default parallel execution to serial.")
@click.pass_context
def cli(ctx, loglevel, serial):
    setupLogging(loglevel)
    ctx.obj = {}
    ctx.obj[sflag]=serial

@click.command()
@click.option('--prefix', '-p', type=str, required=True, help="Hostname prefix for which an index will be appended")
@click.option('--domain', '-d', type=str, required=True, help="Domain upon which which hostname will be prefixed")
@click.option('--count', '-c', type=int, default=1, show_default=True, help="Number of horizon containers")
@click.pass_context
def validateHosts(ctx, prefix, domain, count):
    """Checks each hostname given the hostname prefix and domain. Runs: ssh hostINDEX.domain hostname"""
    ctx.obj[pflag]=prefix
    ctx.obj[dflag]=domain
    ctx.obj[cflag]=count
    hostnames = generateHostnames(ctx)
    valcmds = generateValidationCmds(hostnames)
    run(ctx, valcmds)

@click.command()
@click.option('--configfile', '-f', type=str, required=True, help="File containing configuration json")
@click.pass_context
def validateConfig(ctx, configfile):
    """Checks each each hostname in the json configuation file"""
    loadConfig(ctx, configfile)
    hostnames = ctx.obj[json_endpoints]
    valcmds = generateValidationCmds(hostnames)
    run(ctx, valcmds)

@click.command()
@click.option('--source', '-s', type=str, required=True, help="Source file/directory to be transfered")
@click.option('--destination', '-d', type=str, required=True, help="Destination file/directory to recieve transfer")
@click.option('--configfile', '-f', type=str, required=True, help="File containing configuration json")
@click.pass_context
def scp(ctx, source, destination, configfile):
    """Starts Anax Containers on all hosts (see count flag for >1 container)"""
    loadConfig(ctx, configfile)
    cmds = generageScpCmds(source, destination, ctx.obj[json_endpoints])
    run(ctx, cmds)


cli.add_command(validateHosts)
cli.add_command(validateConfig)
cli.add_command(scp)

if __name__ == '__main__':
    cli()