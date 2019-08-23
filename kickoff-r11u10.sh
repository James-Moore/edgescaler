#!/usr/bin/env bash
source /root/.local/env/myenv.sh
source libkickoff.sh

pattern="IBM/pattern-ibm.helloworld"
nodesearchkey="edge-scale-test"

validateEnviroment
icpLogin ICPUSER ICPPASS https://IPADDRESS:PORT
cleanLogs
cleanScaler
cleanHorizon

markStarttime
startAgentLogging

initializeAgents
captureEnviornment
captureExchangeNodes preregister
captureAgbotsNodes preregister

registerAgents 0 0 1 1 #args are localLoggingLevel, RemoteLoggingLevel, MasterParallelismLevel, SlaveParallelismLevel
waitForAgreements 900

captureAgreements postregister
captureExchangeNodes postregister
captureAgbotsNodes postregister
#captureEventlogs 1 1 val postregister-verbose #args are MasterParallelismLevel, SlaveParallelismLevel, eventlog flags, logfile descriptor
captureEventlogs 1 1 va postregister #args are MasterParallelismLevel, SlaveParallelismLevel, eventlog flags, logfile descriptor


unregisterAgents 0 0 1 0  #args are localLoggingLevel, RemoteLoggingLevel, MasterParallelismLevel, SlaveParallelismLevel
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

#redactLogs PASSWORD
packageLogs