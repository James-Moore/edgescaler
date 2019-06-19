#!/usr/bin/env bash

COUNT=4

#cleanup before run
rm log/*
python3 -m scale.anaxremote -f config.json -l 1 -r 0 prune |& tee log/initprune.log

#start the agent containers
python3 -m scale.anaxremote -f config.json -l 0 -r 1 -c $COUNT start  |& tee log/start.log

#check how many containers were created
python3 -m scale.anaxremote -f config.json -l 2 -r 1 queryrunning --count |& tee log/queryrunning_poststart.log

#check the created containers are all in the running state
python3 -m scale.anaxremote -f config.json -l 2 -r 1 validaterunning |& tee log/validaterunning_poststart.log

#fail if the created containers are not all in the running state
NOTRUNNING=$(python3 -m scale.anaxremote -f config.json -l 2 -r 1 validaterunning |& grep False | wc -l)
if [ $NOTRUNNING -ne 0 ]; then
    echo "At least one agent container has not started properly.  System Exiting."
    exit
fi

#Perform registrations on all running containers
python3 -m scale.anaxremote -f config.json -l 0 -r 0 -c $COUNT register -m 2 -s 0 |& tee log/register.log

#Wait for agreements to be established
while [ $(python3 -m scale.anaxremote -f config.json -l 2 -r 1 -c $COUNT agreements |& grep False | wc -l) -ne 0 ]; do echo "Waiting for agreements to be established.  Will sleep for 30 seconds and check again"; sleep 30; done
python3 -m scale.anaxremote -f config.json -l 2 -r 1 -c $COUNT agreements |& tee log/agreements_postregister.txt

#Unregister all agents
python3 -m scale.anaxremote -f config.json -l 0 -r 0 -c $COUNT unregister -m 1 -s 0 |& tee log/unregister.log

#keep checking until all agreements have been destroyed
while [ $(python3 -m scale.anaxremote -f config.json -l 2 -r 1 -c $COUNT agreements |& grep True | wc -l) -ne 0 ]; do echo "Waiting for agreements to be destroyed.  Will sleep for ten seconds and check again"; sleep 10; done
python3 -m scale.anaxremote -f config.json -l 2 -r 1 -c $COUNT agreements |& tee log/agreements_postunregister.txt

#Stop all agent containers
python3 -m scale.anaxremote -f config.json -l 0 -r 1 -c $COUNT stop  |& tee log/stop.log
#Document the fact all containers are stopped
python3 -m scale.anaxremote -f config.json -l 2 -r 1 queryrunning --count |& tee log/queryrunning_poststop.log
python3 -m scale.anaxremote -f config.json -l 2 -r 1 validaterunning |& tee log/validaterunning_poststop.log

#Redact your cloud token
find ./log/ -type f -exec sed -i 's/YOURTOKENHERE/PW_REDACTED/g' {} \;

#Package the run results
tar -zcvf edgescale-log-$(date +%Y%m%d_%H%M%S).tar.gz log

