import os
import time
import json
import logging
import click
import subprocess
from subprocess import TimeoutExpired
from scale import anaxremote
from pprint import pprint

lineNumber = 1

registrationSignature = ["Start node configuration/registration for node",
    "Start service auto configuration for",
    "Complete service auto configuration for",
    "Complete node configuration/registration for node",
    "Start policy advertising with the exchange for service",
    "Complete policy advertising with the exchange for service",
    "Node received Proposal message for service",
    "Agreement reached for service",
    "Start dependent services for",
    "Start workload service for",
    "Image loaded for",
    "are up and running."]

unregistrationSignature = ["Start node unregistration.",
                         "Termination reason: node was unconfigured",
                         "Workload destroyed for",
                         "Node unregistration complete for node"]

logger = logging.getLogger(__name__)

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

@click.group()
@click.option('--loglevel', '-l', type=int, default=0, show_default=True, help="0=debug, 1=info, 2=production, 3=error, 4=critical")
@click.pass_context
def cli(ctx, loglevel):
    setupLogging(loglevel)
    ctx.obj = {}


def validateOperationSignature(operationSignature: [str], anomolies: [str], line: str, fp):
    global lineNumber
    valid = True
    for element in operationSignature:
        if (valid and (element in line)):
            line = fp.readline()
            #print(line, end="")
            lineNumber = lineNumber + 1
        else:
            valid = False
            anomoly = "ANOMOLY ON LINE: " + str(lineNumber) + "\n" + \
                      "EXPECTED:\t" + element + "\n" + \
                      "FOUND:\t" + line
            anomolies.append(anomoly)
            return

def validateLog(operationSignature: [str], logfile: str) -> [str]:
    """Validates eventlog signatures for registrations abnormalitites"""
    global  lineNumber
    lineNumber = 1
    anomolies = []
    try:
        with open(logfile) as fp:
            line = fp.readline()
            while line:
                if(operationSignature[0] in line):
                    validateOperationSignature(operationSignature=operationSignature, anomolies=anomolies, line=line, fp=fp)
                line = fp.readline()
                #print(line, end="")
                lineNumber=lineNumber+1
    except IOError:
        print("File: "+logfile+"\nLogfile does not exist.  Correct and try again.")



    return anomolies

def printAnomolies(anomolies: [str]):
    anomolyCount = len(anomolies)
    print("Issues Found: " + str(anomolyCount))

    if (anomolyCount != 0):
        print("")

        for i in anomolies:
            print(i)

def validateRegistration(logfile: str):
    global registrationSignature
    anomolies = validateLog(operationSignature=registrationSignature, logfile=logfile)
    print("VALIDATING REGISTRATION")
    printAnomolies(anomolies=anomolies)


def validateUnregistration(logfile: str):
    global unregistrationSignature
    anomolies = validateLog(operationSignature=unregistrationSignature, logfile=logfile)
    print("VALIDATING UNREGISTRATION")
    printAnomolies(anomolies=anomolies)

@click.command()
@click.argument('logfile')
@click.pass_context
def eventlogs(ctx, logfile):
    validateRegistration(logfile=logfile)
    validateUnregistration(logfile=logfile)

cli.add_command(eventlogs)

if __name__ == '__main__':
    cli()