import json
import subprocess
from subprocess import TimeoutExpired
from pprint import pprint

def main():
    result = False
    processes = {}

    i = 0
    callList = ["ls"]
    #callList = ["ls"]
    print("Calling: " + str(callList))
    p = subprocess.Popen(callList, stdout=subprocess.PIPE, universal_newlines=True)
    entry = {p: callList}
    processes.update(entry)


    callList = ["ls", "/home/"]
    # callList = ["ls"]
    print("Calling: " + str(callList))
    p = subprocess.Popen(callList, stdout=subprocess.PIPE, universal_newlines=True)
    entry = {p: callList}
    processes.update(entry)

    print("All Processes Scheduled...  Waiting for completion... Do not interupt..")

    for key in processes:
        process = key
        cl = processes[key]
        print("Waiting for: " + str(process.pid))

        outs = str()
        errs = str()

        try:
            outs, errs = process.communicate(timeout=15)
        except TimeoutExpired:
            process.kill()
            outs, errs = process.communicate()

        print(cl)
        print (outs)
        print (errs)

    print("All Processes Completed.")
    return result


if __name__ == '__main__':
    main()
