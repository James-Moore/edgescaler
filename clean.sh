#!/usr/bin/env bash

source /root/.local/env/myenv.sh
source libkickoff.sh

#pattern="obliging-snail-icp-cluster/unhealthyhello"
pattern="IBM/pattern-ibm.helloworld"
nodesearchkey="edge-scale-test"
runstart=`date +%s`
logdir="$PWD/log"
runtimelog="$logdir/runtime.log"
COUNT=20

validateEnviroment
icpLogin ICPUSER ICPPASS https://IPADDRESS:PORT
destroyAgents
cleanScaler
cleanHorizon

runend=`date +%s`
runtime=$((runend-runstart))
echo "$runtime" > "$runtimelog"
