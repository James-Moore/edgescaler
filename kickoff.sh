#!/usr/bin/env bash

#Validate Correct Number of Arguments
if [ "$#" -ne 6 ]; then
    echo ""
    echo "    USAGE:"
    echo "    kickoff.sh NumberOfVMs  NumberOfContainersPerVM MasterRegistrationRunMode SlaveRegistrationRunMode MasterUnegistrationRunMode SlaveUnegistrationRunMode"
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

echo "###########################"
echo "SCALER KICKOFF RECIPE"
echo "VMS: ${1}"
echo "ContainersPerVM: ${2}"
echo "Master Registration Mode: ${3}"
echo "Slave Registration Mode: ${4}"
echo "Master Unregistration Mode: ${5}"
echo "Slave Unregistration Mode: ${6}"
echo "###########################"

vms=${1}
cpv=${2}
mrmode=${3}
srmode=${4}
mumode=${5}
sumode=${6}

source /root/.local/env/myenv.sh
source libkickoff.sh

pattern="IBM/pattern-ibm.helloworld"
nodesearchkey="edge-scale-test"

validateEnviroment
icpLogin ${ICPUSER} ${ICPPASS} ${ICPADDRESS}
cleanLogs
cleanScaler
cleanHorizon

markStarttime
startAgentLogging

initializeAgents
captureEnviornment
captureExchangeNodes preregister
captureAgbotsNodes preregister

registerAgents 0 0 ${mrmode} ${srmode} #args are localLoggingLevel, RemoteLoggingLevel, MasterParallelismLevel, SlaveParallelismLevel
waitForAgreements 900

captureAgreements postregister
captureExchangeNodes postregister
captureAgbotsNodes postregister
#captureEventlogs 1 1 val postregister-verbose #args are MasterParallelismLevel, SlaveParallelismLevel, eventlog flags, logfile descriptor
captureEventlogs 1 1 va postregister #args are MasterParallelismLevel, SlaveParallelismLevel, eventlog flags, logfile descriptor


unregisterAgents 0 0 ${mumode} ${sumode}  #args are localLoggingLevel, RemoteLoggingLevel, MasterParallelismLevel, SlaveParallelismLevel
captureAgreements postunregister
captureExchangeNodes postunregister
captureAgbotsNodes postunregister
#captureEventlogs 1 1 val postunregister-verbose #args are MasterParallelismLevel, SlaveParallelismLevel, eventlog flags, logfile descriptor
captureEventlogs 1 1 va postunregister #args are MasterParallelismLevel, SlaveParallelismLevel, eventlog flags, logfile descriptor

secs=$(secondsRunning)
captureExchangeLogging ${secs}
captureAgbotLogging ${secs}
captureAgentLogging

destroyAgents
stopAgentLogging
markRuntime

redactLogs [YOURKEYHERE]
packageLogs