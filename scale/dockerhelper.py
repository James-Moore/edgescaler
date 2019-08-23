import docker
from uuid import uuid4
from scale import *
from scale.operation import Operation
from scale.logger import Logger

class DockerHelepr:
    def __init__(self):
        pass

    # get the list of indexes assosciated with containers that are running from 1..COUNT
    def getRunningContainerList(self, count: int) -> [int]:
        client = docker.from_env()

        containers2stop = []

        # generate list of running anax containers
        for i in range(count):
            index = i + 1  # accouting for the fact that there is non-zero indexing in AIC horizon-container
            try:
                name = hznprefix + str(index)  # name of the horizon container
                out = client.containers.get(name)  # check if the container exists
                containers2stop.append(index)  # if it does then add the index of the running container to the list
            except:
                # if the container does not exist then do nothing
                pass

        # return list of running containers
        return containers2stop

    # get the names of all running anax containers
    def getRunningAnaxContainerNames(self, ) -> [str]:
        client = docker.from_env()

        names = []

        for container in client.containers.list(filters={"name": "horizon"}):
            cenv = container.attrs['Config']['Env']
            for val in cenv:
                sval = val.split('=')
                if sval[0] == 'DOCKER_NAME' and sval[1].startswith('horizon'):
                    names.append(sval[1])

        return names

    def produceIndicesList(self, count: int) -> []:
        containers = []
        for i in range(count):
            containers.append(i + 1)
        return containers

