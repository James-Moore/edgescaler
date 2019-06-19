#!/usr/bin/env bash

COUNT=2

rm log/*
python3 -m scale.anaxremote -f config.json -l 1 -r 0 prune
python3 -m scale.anaxremote -f config.json -l 0 -r 1 -c $COUNT start  |& tee log/start.log
python3 -m scale.anaxremote -f config.json -l 2 -r 1 queryrunning --count |& tee log/queryrunning_poststart.log
python3 -m scale.anaxremote -f config.json -l 2 -r 1 validaterunning |& tee log/validaterunning_poststart.log
python3 -m scale.anaxremote -f config.json -l 0 -r 0 -c $COUNT register -m 2 -s 0  |& tee log/register.log
#keep checking until all agreements have been established
while [ $(python3 -m scale.anaxremote -f config.json -l 2 -r 1 -c $COUNT agreements |& grep False | wc -l) -ne 0 ]; do echo "Waiting for agreements to be established.  Will sleep for 30 seconds and check again"; sleep 30; done
python3 -m scale.anaxremote -f config.json -l 2 -r 1 -c $COUNT agreements |& tee log/agreements_postregister.txt
python3 -m scale.anaxremote -f config.json -l 0 -r 0 -c $COUNT unregister -m 2 -s 0  |& tee log/unregister.log
#keep checking until all agreements have been destroyed
while [ $(python3 -m scale.anaxremote -f config.json -l 2 -r 1 -c $COUNT agreements |& grep True | wc -l) -ne 0 ]; do echo "Waiting for agreements to be destroyed.  Will sleep for ten seconds and check again"; sleep 10; done
python3 -m scale.anaxremote -f config.json -l 2 -r 1 -c $COUNT agreements |& tee log/agreements_postunregister.txt
python3 -m scale.anaxremote -f config.json -l 0 -r 1 -c $COUNT stop  |& tee log/stop.log
python3 -m scale.anaxremote -f config.json -l 2 -r 1 queryrunning --count |& tee log/queryrunning_poststop.log
python3 -m scale.anaxremote -f config.json -l 2 -r 1 validaterunning |& tee log/validaterunning_poststop.log


find ./log/ -type f -exec sed -i 's/YOURTOKENHERE/PW_REDACTED/g' {} \;
tar -zcvf edgescale-log-$(date +%Y%m%d_%H%M%S).tar.gz log

