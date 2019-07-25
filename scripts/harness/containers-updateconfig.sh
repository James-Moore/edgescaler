#!/usr/bin/env bash

pattern="obliging-snail-icp-cluster/unhealthyhello"
runstart=`date +%s`
logdir="$PWD/log"
runtimelog="$logdir/runtime.log"

COUNT=1

#cleanup before run
rm log/*
python3 -m scale.anaxremote -f config.json -l 1 -r 0 -c $COUNT prune |& tee log/initprune.log

#start the agent containers
python3 -m scale.anaxremote -f config.json -l 0 -r 1 -c $COUNT start  |& tee log/start.log

python3 -m scale.anaxremote -f config.json -l 0 -r -0 -c $COUNT dockerexec 'hzn version' |& tee log/containers-hzn_version.log
python3 -m scale.anaxremote -f config.json -l 0 -r -0 -c $COUNT dockerexec 'cat /etc/horizon/anax.json' |& tee log/containers-anaxjson_preupdate.log
python3 -m scale.anaxremote -f config.json -l 0 -r 0 -c $COUNT containerconfigupdate |& tee log/containers-configupdate.log
python3 -m scale.anaxremote -f config.json -l 0 -r -0 -c $COUNT dockerexec 'cat /etc/horizon/anax.json' |& tee log/containers-anaxjson_prerestart.log
python3 -m scale.anaxremote -f config.json -l 0 -r 1 -c $COUNT restart  |& tee log/containers-restart.log
python3 -m scale.anaxremote -f config.json -l 0 -r -0 -c $COUNT dockerexec 'cat /etc/horizon/anax.json' |& tee log/containers-anaxjson_postrestart.log

#Stop all agent containers
python3 -m scale.anaxremote -f config.json -l 0 -r 1 -c $COUNT stop  |& tee log/stop.log

runend=`date +%s`
runtime=$((runend-runstart))
echo "$runtime" > "$runtimelog"

