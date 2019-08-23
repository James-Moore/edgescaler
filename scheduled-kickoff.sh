#!/usr/bin/env bash

if [ "$#" -ne 4 ]; then
    echo ""
    echo "    USAGE:"
    echo "    scheduled-kickoff.sh  RegistrationRunModes  UnregistrationRunModes  NumberOfVMs  NumberOfContainersPerVM"
    echo "        RegistrationRunModes:    MS | M=MasterRunMode, S=SlaveRunMode and available modes are: 0=Parallel, 1=PseudoSerial, 2=Serial"
    echo "        UnregistrationRunModes:  MS | M=MasterRunMode, S=SlaveRunMode and available modes are: 0=Parallel, 1=PseudoSerial, 2=Serial"
    echo "        NumberOfVMs:             The number of slave virtual machines defined in config.json"
    echo "        NumberOfContainersPerVM: COUNT is used in the kickoff script"
    echo ""
    exit -1
fi

kickoff=kickoff-r${1}u${2}.sh
runlog=run_${3}vm_${4}container_r${1}u${2}.log

if [ ! -x ${kickoff} ]; then
    echo "File ${kickoff} must exist and be executable.  Exiting."
    exit -1
fi

export COUNT=${4}
cd /root/scaler
${kickoff} &> ${runlog}
unset COUNT