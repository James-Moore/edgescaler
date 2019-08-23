import os
from uuid import uuid4
from scale import *
from scale.operation import Operation
from scale.logger import Logger

class CommandHelper:
    def __init__(self):
        pass

    def generateHorizonContainerCommands(self, environment: {}, aicCommand: str, arg: str, containers: [int], logger: Logger) -> []:
        operations = []
        for container in containers:
            # build the list to send as the args parameter to subprocess.call
            operation = [aicCommand, arg, str(container)]
            logger.info("OPERATION: "+str(operation))
            logger.info(str(operation))
            operation = self.generateHorizonCommand(environment=environment, containerIndex=container, operation=operation, logger=logger)
            operations.append(operation)
        return operations


    def generateHorizonCommand(self, environment: {}, containerIndex: int, operation: [str], logger: Logger) -> Operation:
        operation = Operation(operation=operation, logger=logger)
        operation.updateEnvironment(environment=environment, containerNumber=containerIndex)
        return operation