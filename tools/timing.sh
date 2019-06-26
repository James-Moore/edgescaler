#!/usr/bin/env bash

runstart=`date +%s`
logdir="$PWD/log"
runtimelog="$logdir/runtime.log"
rm $logdir/*


runend=`date +%s`
runtime=$((runend-runstart))
echo "$runtime" > "$runtimelog"

