import json

json_endpoints = 'endpoints'

def main():
    f = open(file="/home/parallels/PycharmProjects/edgescaler/config.json")
    j = json.loads(f.read())
    j[json_endpoints] = []

    for i in range(250):
        hostindex = str(i+1).zfill(2)
        hostname = "edge-scale-test"+hostindex+".rtp.raleigh.ibm.com"
        j[json_endpoints].append(hostname)

    print (j[json_endpoints])

    f.close()
    f = open(file="/home/parallels/PycharmProjects/edgescaler/config.json", mode="w")
    json.dump(j, f, indent=4, sort_keys=True,)


if __name__ == '__main__':
    main()