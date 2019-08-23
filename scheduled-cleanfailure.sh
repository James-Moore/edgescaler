#!/usr/bin/env bash

if [ "$#" -ne 2 ]; then
    echo ""
    echo "    USAGE:"
    echo "    scheduled-cleanfailure.sh NumberOfContainersPerVM RunPhase"
    echo "        NumberOfContainersPerVM:  COUNT is used in the kickoff script"
    echo "        RunPhase:                 Horizon frozen in phase, 0=Registration, 1=Unregistration"
    echo ""
    exit -1
fi

cleanfailure=cleanfailure.sh
runlog=log/cleanfailure.log

if [ ! -x ${cleanfailure} ]; then
    echo "File ${cleanfailure} must exist and be executable.  Exiting."
    exit -1
fi

if [ ${2} -lt 0 ] || [ ${2} -gt 1 ]; then
    echo "RunPhase must be 0 or 1.  Exiting."
    exit -1
fi

kid=$(ps -ef | grep kickoff | grep -v grep | awk '{print $2}')
if [ -n "${kid}" ]; then
    export COUNT=${1}
    cd /root/scaler
    ${cleanfailure} ${2} &> ${runlog}
fi
unset COUNT