import os
from uuid import uuid4
from scale import *
from scale.horizonhelper import HorizonHelper
from scale.logger import Logger


class Operation:
    def __init__(self, operation: [str], logger: Logger):
        self.environment = os.environ.copy()
        self.operation = operation
        self.uuid = uuid4()

    def updateEnvironment(self, environment: {}, containerNumber: int, ) -> {}:
        hhelper = HorizonHelper()
        self.environment[env_hznurl] = hhelper.generateHorizonURL(containerNumber)
        self.environment[env_hzncontainer] = hhelper.generateHorizonContainerName(containerNumber)

        for key in environment.keys():
            self.environment[key] = environment[key]

    def getOperation(self) -> [str]:
        return self.operation

    def getOperationAsString(self) -> str:
        return " ".join(self.getOperation())

    def getEnvironment(self) -> {}:
        return self.environment

    def getUUID(self) -> str:
        return str(self.uuid)
