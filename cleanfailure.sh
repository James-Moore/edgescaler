#!/usr/bin/env bash
source /root/.local/env/myenv.sh
source libkickoff.sh
killRun

pattern="IBM/pattern-ibm.helloworld"
nodesearchkey="edge-scale-test"

if [ "$#" -ne 1 ]; then
    echo ""
    echo "    USAGE:"
    echo "    scheduled-cleanfailure.sh startPhase"
    echo "        startPhase: Start cleanup after a given system state.  0=register, 1=unregister"
    echo ""
    exit -1
fi

validateEnviroment
icpLogin ICPUSER ICPPASS https://IPADDRESS:PORT

phase=$1

#Execute if starting in phase register
if (( phase < 1 )); then
    captureAgreements postregister_CF
    captureExchangeNodes postregister_CF
    captureAgbotsNodes postregister_CF
    #captureEventlogs 1 1 val postregister-verbose #args are MasterParallelismLevel, SlaveParallelismLevel, eventlog flags, logfile descriptor
    captureEventlogs 1 1 va postregister_CF #args are MasterParallelismLevel, SlaveParallelismLevel, eventlog flags, logfile descriptor
    unregisterAgents 0 0 1 0  #args are localLoggingLevel, RemoteLoggingLevel, MasterParallelismLevel, SlaveParallelismLevel
fi

#Execute if starting in phase register and unregister
if (( phase < 2 )); then
    captureAgreements postunregister_CF
    captureExchangeNodes postunregister_CF
    captureAgbotsNodes postunregister_CF
    #captureEventlogs 1 1 val postunregister-verbose #args are MasterParallelismLevel, SlaveParallelismLevel, eventlog flags, logfile descriptor
    captureEventlogs 1 1 va postunregister_CF #args are MasterParallelismLevel, SlaveParallelismLevel, eventlog flags, logfile descriptor
fi

logtime=$(secondsRunning)
captureExchangeLogging ${logtime}
captureAgbotLogging ${logtime}
captureAgentLogging

destroyAgents
stopAgentLogging
markRuntime

#redactLogs PASSWORDTOSCRUBHERE
packageLogs
