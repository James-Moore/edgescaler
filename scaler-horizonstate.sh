#!/usr/bin/env bash

source /root/.local/env/myenv.sh
source libkickoff.sh

pattern="IBM/pattern-ibm.helloworld"
nodesearchkey="edge-scale-test"
runstart=`date +%s`
logdir="$PWD/log"
runtimelog="$logdir/runtime.log"
COUNT=20

validateEnviroment
icpLogin ICPUSER ICPPASS https://IPADDRESS:PORT
cleanLogs
captureAgbotsNodes
captureExchangeNodes

runend=`date +%s`
runtime=$((runend-runstart))
echo "$runtime" > "$runtimelog"
