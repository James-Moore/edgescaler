#!/usr/bin/env bash

runstart=`date +%s`
logdir="$PWD/log"
runtimelog="$logdir/runtime.log"

COUNT=20

#Wait for agreements to be established
python3 -m scale.anaxremote -f config.json -l 2 -r 1 -c $COUNT agreements |& tee log/agreements_postregister.log
python3 -m scale.anaxremote -f config.json -l 0 -r 0 -c $COUNT agreements |& tee log/agreements_postregister-verbose.log

#Collect eventlogs
python3 -m scale.anaxremote -f config.json -l 0 -r 0 -c $COUNT eventlog |& tee log/eventlogs.log

#Unregister all agents
python3 -m scale.anaxremote -f config.json -l 0 -r 0 -c $COUNT unregister -m 1 -s 0 |& tee log/unregister.log

#keep checking until all agreements have been destroyed
while [ $(python3 -m scale.anaxremote -f config.json -l 2 -r 1 -c $COUNT agreements |& grep True | wc -l) -ne 0 ]; do echo "Waiting for agreements to be destroyed.  Will sleep for ten seconds and check again"; sleep 10; done
python3 -m scale.anaxremote -f config.json -l 2 -r 1 -c $COUNT agreements |& tee log/agreements_postunregister.txt
python3 -m scale.anaxremote -f config.json -l 0 -r 0 -c $COUNT agreements |& tee log/agreements_postunregister-verbose.log

#collect syslogs
python3 -m tools.hosts recievesyslogs -f config.json -o log |& tee log/syslogcollect.log

#Stop all agent containers
python3 -m scale.anaxremote -f config.json -l 0 -r 1 -c $COUNT stop  |& tee log/stop.log
#Document the fact all containers are stopped
python3 -m scale.anaxremote -f config.json -l 2 -r 1 queryrunning --count |& tee log/queryrunning_poststop.log
python3 -m scale.anaxremote -f config.json -l 2 -r 1 validaterunning |& tee log/validaterunning_poststop.log

#cleanup before run
python3 -m scale.anaxremote -f config.json -l 1 -r 0 -c $COUNT prune |& tee log/initprune.log
for i in $(cat config.json | jq -r '.endpoints | .[]'); do ssh root@$i "hostname & pkill -f scale.anaxscale" ; done
wait


runend=`date +%s`
runtime=$((runend-runstart))
echo "$runtime" > "$runtimelog"

#Redact your cloud token
find ./log/ -type f -exec sed -i 's/YOURPWHERE/PW_REDACTED/g' {} \;

#Package the run results
if [ -d log ]; then
    [ -f run*.log ] && mv run*.log log
    tar -zcvf edgescale-log-$(date +%Y%m%d_%H%M%S).tar.gz log
fi
