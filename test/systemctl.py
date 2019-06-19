from pydbus import SystemBus
import sys


def main():
    bus = SystemBus()
    systemd = bus.get(".systemd1")
    manager = systemd[".Manager"]

    try:
        if len(sys.argv) < 2:
            for unit in manager.ListUnits():
                print(unit)
        else:
            if sys.argv[1] == "--help":
                help(manager)
            else:
                command = sys.argv[1]
                command = "".join(x.capitalize() for x in command.split("-"))
                result = getattr(manager, command)(*sys.argv[2:])

                for var in result:
                    if type(var) == list:
                        for line in var:
                            print(line)
                    else:
                        print(var)
    except Exception as e:
        print(e)



if __name__ == '__main__':
    main()
