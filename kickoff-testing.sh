#!/usr/bin/env bash

runstart=`date +%s`
logdir="$PWD/log"
runtimelog="$logdir/runtime.log"

#used to just easily copy and paste into a separate terminal

rm log/*
python3 -m scale.anaxremote -f config.json -l 1 -r 0 -c $COUNT prune
COUNT=2;  python3 -m scale.anaxremote -f config.json -l 0 -r 1 -c $COUNT start  |& tee log/start.log
COUNT=2;  python3 -m scale.anaxremote -f config.json -l 2 -r 1 queryrunning --count |& tee log/queryrunning_poststart.log
COUNT=2;  python3 -m scale.anaxremote -f config.json -l 2 -r 1 validaterunning |& tee log/validaterunning_poststart.log
COUNT=2;  python3 -m scale.anaxremote -f config.json -l 0 -r 0 -c $COUNT register -m 2 -s 0 |& tee log/register.log
#keep checking until all agreements have been established
COUNT=2;  while [ $(python3 -m scale.anaxremote -f config.json -l 2 -r 1 -c $COUNT agreements |& grep False | wc -l) -ne 0 ]; do echo "Waiting for agreements to be established.  Will sleep for 30 seconds and check again"; sleep 30; done
COUNT=2;  python3 -m scale.anaxremote -f config.json -l 2 -r 1 -c $COUNT agreements |& tee log/agreements_postregister.log
COUNT=2;  python3 -m scale.anaxremote -f config.json -l 0 -r 0 -c $COUNT agreements |& tee log/agreements_postregister-verbose.log
#Collect eventlogs
COUNT=2;  python3 -m scale.anaxremote -f config.json -l 0 -r 0 -c $COUNT eventlog |& tee log/eventlogs.log
COUNT=2;  python3 -m scale.anaxremote -f config.json -l 0 -r 0 -c $COUNT unregister -m 1 -s 0 |& tee log/unregister.log
#keep checking until all agreements have been destroyed
COUNT=2;  while [ $(python3 -m scale.anaxremote -f config.json -l 2 -r 1 -c $COUNT agreements |& grep True | wc -l) -ne 0 ]; do echo "Waiting for agreements to be destroyed.  Will sleep for ten seconds and check again"; sleep 10; done
COUNT=2;  python3 -m scale.anaxremote -f config.json -l 2 -r 1 -c $COUNT agreements |& tee log/agreements_postunregister.txt
#collect syslogs
COUNT=2;  python3 -m tools.hosts recievesyslogs -f config/config.json.large -o log |& tee log/syslogcollect.log
COUNT=2;  python3 -m scale.anaxremote -f config.json -l 0 -r 1 -c $COUNT stop  |& tee log/stop.log
COUNT=2;  python3 -m scale.anaxremote -f config.json -l 2 -r 1 queryrunning --count |& tee log/queryrunning_poststop.log
COUNT=2;  python3 -m scale.anaxremote -f config.json -l 2 -r 1 validaterunning |& tee log/validaterunning_poststop.log

runend=`date +%s`
runtime=$((runend-runstart))
echo "$runtime" > "$runtimelog"

#Redact your cloud token
find ./log/ -type f -exec sed -i 's/YOUR_USER_PW/PW_REDACTED/g' {} \;

#Package the run results
tar -zcvf edgescale-log-$(date +%Y%m%d_%H%M%S).tar.gz log