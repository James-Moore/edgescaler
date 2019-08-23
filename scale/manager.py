import time
import os
import tempfile
import subprocess
from uuid import uuid4
from scale import *
from scale.logger import Logger
from scale.operation import Operation
from pprint import pprint

class Manager:
    def __init__(self, logger: Logger):
        # create logging
        self.logger = logger

    def isSerial(self, mode: int) -> bool:
        return mode == mode_serial

    def isPseudoSerial(self, mode: int) -> bool:
        return mode == mode_pseudoserial

    def isParallel(self, mode: int) -> bool:
        return mode == mode_parallel

    def exportEnv(self, env: {}):
        for key in env:
            os.environ[key] = env[key]

    def generateSshLogin(self, host: str) -> [str]:
        sshcmd = "ssh"
        sshconnect = "root@" + host
        return [sshcmd, sshconnect]

    def generateSshCommands(self, env: {}, hostnames: [str], operation: str, logger: Logger) -> [Operation]:
        #hostnames = ctx.obj[json_endpoints]
        #env = ctx.obj[json_env] #env is {}

        operations = []
        for hostname in hostnames:
            sshOperation = self.generateSshCommand(env=env, host=hostname, operation=operation, workerPseudoDelay=-1, logger=logger)
            operations.append(sshOperation)
        return operations

    def generateSshCommand(self, env: {}, host: str, operation: str, workerPseudoDelay: float, logger: Logger) -> Operation:
        assemble = ""
        for key in env:
            assemble = assemble + "export " + key + "=" + env[key] + "; "

        if(workerPseudoDelay > 0):
            assemble = assemble + "export " + env_scaler_workerpseudodelay + "=" + str(workerPseudoDelay) + "; "

        assemble = assemble + operation

        login = self.generateSshLogin(host)
        sshop = login + [assemble]
        return Operation(operation=sshop, logger=logger)

    def generateSendCommands(self, hostnames: [str], source: str, destination: str, logger: Logger) -> [Operation]:
        #hostnames = ctx.obj[json_endpoints]
        operations = []
        for hostname in hostnames:
            command = self.generateSendCommand(sourceDirectory=source, destinationHostname=hostname, destinationDirectory=destination, logger=logger)
            operations.append(command)
        return operations

    def generateSendCommand(self, sourceDirectory: str, destinationHostname: str, destinationDirectory: str, logger: Logger) -> Operation:
        command = ["scp", "-r", sourceDirectory, "root@" + destinationHostname + ":" + destinationDirectory]
        return Operation(operation=command, logger=logger)

    def generateRecieveCommands(self, hostnames: [str], source: str, destination: str, logger: Logger) -> [Operation]:
        #hostnames = ctx.obj[json_endpoints]
        operations = []
        for hostname in hostnames:
            command = self.generateReceiveCommand(sourceHostname=hostname, sourceDirectory=source, destinationDirectory=destination, logger=logger)
            operations.append(command)
        return operations

    def generateReceiveCommand(self, sourceHostname: str, sourceDirectory: str, destinationDirectory: str, logger: Logger) -> Operation:
        hostnameDestination = os.path.join(destinationDirectory, sourceHostname)
        os.makedirs(hostnameDestination, exist_ok=True)
        command = ["scp", "-r", "root@" + sourceHostname + ":" + sourceDirectory, hostnameDestination]
        return Operation(operation=command, logger=logger)

    # run the remote command asynchronously so all hosts perform their local parallel operations in parallel
    # meaning... parallelism is hostcount*processcount
    #Precondition:  Command array is formatted as [ [UUID4, COMMANDARRAY], ...]
    def run(self, runmode: int, operations: [Operation]):
        # Setup Kickoff
        self.logger.info("Run Mode: " + str(runmode), newline=True)

        processes = {}
        # Kickoff all asynchronous processes
        for o in operations:

            self.logger.debug("Calling operation below with key: "+ o.getUUID(), newline=True)
            self.logger.debug(o.getOperationAsString(), newline=True)
            self.logger.debug("", timestamp=False, newline=True)

            f = tempfile.NamedTemporaryFile(mode='w+t', delete=True)
            p = subprocess.Popen(o.getOperation(), env=o.getEnvironment(), stdout=f, stderr=subprocess.STDOUT, universal_newlines=True)
            processes.update({o.getUUID(): [p, f]})

            # User defined mode of operation
            if self.isPseudoSerial(runmode):
                self.logger.debug(str(["Delay: " + str(pseudoDelay)]), newline=True)
                time.sleep(pseudoDelay)
            elif self.isSerial(runmode):
                self.logger.debug("Waiting for process to complete before continuing...", newline=True)
                p.wait()

        self.logger.info("All Processes Scheduled...  Waiting for completion... Do not interupt..", newline=True)

        # Wait for all background processes
        for o in operations:

            key = o.getUUID()
            value = o.getOperation()
            operation = o.getOperationAsString()

            process = processes[key][0]  # this is the subprocess.process object
            f = processes[key][1]  # this is the temporary file created to hold the process stdout/stderr

            self.logger.debug("Process Wait: " + str(process.pid), newline=True)
            process.wait()
            self.logger.debug("Process Complete: " + str(process.pid), newline=True)

            self.logger.debug("EXECUTION DATA", timestamp=False, newline=True)
            self.logger.debug("Operation: ", timestamp=False, newline=True)
            self.logger.debug(operation, timestamp=False, newline=True)
            self.logger.debug("Return Code: " + str(process.returncode), timestamp=False, newline=True)
            self.logger.debug("Output:  ", timestamp=False, newline=True)

            f.seek(0)
            for line in f:
                self.logger.warning(line, timestamp=False, newline=False)
            f.close()

            self.logger.debug("", timestamp=False, newline=True)

        # inform user of completion
        self.logger.info("All Processes Completed.", newline=True)