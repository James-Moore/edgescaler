#!/usr/bin/env bash

#Validate Correct Number of Arguments
if [ "$#" -ne 6 ]; then
    echo ""
    echo "    USAGE:"
    echo "    scheduled-kickoff.sh NumberOfVMs  NumberOfContainersPerVM MasterRegistrationRunMode SlaveRegistrationRunMode MasterUnegistrationRunMode SlaveUnegistrationRunMode"
    echo "        NumberOfVMs:             The number of slave virtual machines defined in config.json"
    echo "        NumberOfContainersPerVM: COUNT is used in the kickoff script"
    echo "        MasterRegistrationRunMode    int | 0=Parallel, 1=PseudoSerial, 2=Serial"
    echo "        SlaveRegistrationRunMode    int | 0=Parallel, 1=PseudoSerial, 2=Serial"
    echo "        MasterUnregistrationRunMode    int | 0=Parallel, 1=PseudoSerial, 2=Serial"
    echo "        SlaveUnregistrationRunMode    int | 0=Parallel, 1=PseudoSerial, 2=Serial"
    echo ""
    exit -1
fi

#Validate Run Modes are within range
for param in ${3} ${4} ${5} ${6} ; do
    if (( param < 0 )) || (( param > 2 )); then
        echo "Run mode must be valid.  Check and try again."
        exit 1
    fi
done

vms=${1}
cpv=${2}
mrmode=${3}
srmode=${4}
mumode=${5}
sumode=${6}

kickoff=kickoff.sh
runlog=run_${vms}vm_${cpv}container_r${mrmode}${srmode}u${mumode}${sumode}.log

if [ ! -x ${kickoff} ]; then
    echo "File ${kickoff} must exist and be executable.  Exiting."
    exit -1
fi

export COUNT=${cpv}
cd /root/scaler
${kickoff} ${vms} ${cpv} ${mrmode} ${srmode} ${mumode} ${sumode} &> ${runlog}
unset COUNT