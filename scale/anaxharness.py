import os
import click
import json
import logging
from pprint import pprint
from scale import *
from scale.artifacts.job import *
import subprocess
from subprocess import TimeoutExpired

logger = logging.getLogger(__name__)


def setupLogger(loglevel: int):
    # create logger
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

def setupConfig(configfile: str):
    f = open(file=configfile)
    j = json.loads(f.read())

@click.group()
@click.option('--configfile', '-f', type=str, required=True, help="File containing harness json")
@click.option('--loglevel', '-l', type=int, default=0, show_default=True, help="0=debug, 1=info, 2=produciton, 3=error, 4=critical")
@click.pass_context
def cli(ctx, configfile, loglevel):
    """Harness used to drive scale analysis jobs"""
    setupLogger(loglevel=loglevel)

    f = open(file=configfile)
    ctx.obj = {
        jobskey: json.loads(f.read())
    }

@click.command()
@click.pass_context
def execute(ctx):
    """Executes the jobs defined in the configuration"""
    getJobdefs(ctx)


def getJobdefs(ctx):
    jobs=[]

    for entry in ctx.obj[jobskey]:
        jobs.append(Job(entry[jobkey]))

    pprint(jobs[0].toJson())

cli.add_command(execute)

if __name__ == '__main__':
    cli()
