import os
from scale import *
from scale.logger import Logger

class HorizonHelper:
    def __init__(self):
        pass

    def generateHorizonURL(self, index: int)->str:
        port = baseport + index
        HORIZON_URL = "http://localhost:" + str(port)
        return HORIZON_URL

    def generateHorizonContainerName(self, index: int)->str:
        return hznprefix+str(index)

    def generateNodeAuth(self, hostname: str, containerIndex: int) -> str:
        unique = hostname + "_" + self.generateHorizonContainerName(containerIndex) + ":" + "repeatabletoken"
        return unique

    # Make the attribute lists.  Each list will be associated with a running anax container
    def generateRegAttrLists(self, org: str, pattern: str, hostname: str, containers: [int]) -> [str]:
        attrLists = []
        for i in containers:
            attrLists.append(["register", "-n", self.generateNodeAuth(hostname=hostname, containerIndex=i), org, pattern])
            # attrLists.append(["register", "-v", "-n", self.generateNodeAuth(hostname=hostname, containerIndex=i), org, pattern])

        return attrLists

    # Make the attribute lists.  Each list will be associated with a running anax container
    def generateUnregAttrLists(self, containers: [int]) -> [str]:
        attrLists = []
        for i in containers:
            attrLists.append(["unregister", "-v", "-f", "-r"])
        return attrLists

    # Make the attribute lists.  Each list will be associated with a running anax container
    def generateEventlogAttrLists(self, containers: [int], flags: str) -> [str]:
        attrLists = []
        for i in containers:
            attrLists.append(["eventlog", "list", "-" + flags])
        return attrLists

    def generateHorizonOperations(self, hznattrLists, containers: [int], logger: Logger) -> []:
        from scale.operation import Operation
        operations = []
        for container in containers:
            callList = [hzncmd] + hznattrLists.pop(0)
            operation = Operation(operation=callList, logger=logger)
            operation.updateEnvironment(environment=os.environ.copy(), containerNumber=container)
            operations.append(operation)
        return operations
