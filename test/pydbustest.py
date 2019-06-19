from pydbus import SystemBus
import sys


def main():
    bus = SystemBus()

    systemd = bus.get(".systemd1")
    manager = systemd[".Manager"]
    service = manager.GetUnit("docker.service")

    print( systemd )

    #help(manager)



if __name__ == '__main__':
    main()
