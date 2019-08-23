#!/usr/bin/env bash

function icpLogin() {
    #ICP Login
    cloudctl login -u $1 -p $2 -n kube-system -a $3 --skip-ssl-validation
}

function validateEnviroment() {
    #Verify the envionment is properly setup
    if [ -z "$SCALERENVSET" ]; then
            echo "Scaler environment is not set. Cannot proceed without proper envionrment. System Exiting."
            exit 1
    fi

    #Verify the envionment is properly setup
    if [ -z "${COUNT}" ]; then
            echo "Scaler Container Count is not set. Cannot proceed without proper envionrment.  Must know the number of containers per virtual machine. System Exiting."
            exit 1
    fi
}

function captureEnviornment() {
    #capture environment
    env |& tee log/env.log
    python3 -m scale.anaxremote -f config.json -l 0 -r -0 -c $COUNT dockerexec 'hzn version' |& tee log/agents-hzn_version.log
    python3 -m scale.anaxremote -f config.json -l 0 -r -0 -c $COUNT dockerexec 'cat /etc/horizon/anax.json' |& tee log/agents-anaxjson.log
}

function captureAgreements(){
    python3 -m scale.anaxremote -f config.json -l 2 -r 1 -c $COUNT agreements |& tee log/agreements_$1.log
    python3 -m scale.anaxremote -f config.json -l 0 -r 0 -c $COUNT agreements |& tee log/agreements_$1-verbose.log
}

function captureEventlogs() {
    #Collect eventlogs
    python3 -m scale.anaxremote -f config.json -l 0 -r 0 -c $COUNT eventlog -m $1 -s $2 -e $3 |& tee log/eventlogs_$4.log
}

function captureExchangeNodes() {
    #document horizon exchange nodes after registration
    hzn exchange node list | jq -r .[] | grep $nodesearchkey |& tee log/exchangenodes_$1.log
}


function captureAgbotsNodes() {
    agbots=$(kubectl get pod | grep "Running" | grep -v "agbot-db" | grep "agbot" | awk '{print $1}')
    for ab in ${agbots} ; do
        captureAgbotNodes ${ab}
    done
}

function captureAgbotNodes() {
    agbot=${1}
    printf "CAPTURING HORIZON AGBOT STATE\n" |& tee log/agbot_${agbot}.log
    printf "DEBUG: Agbot... $agbot \n"  |& tee -a log/agbot_${agbot}.log

    agreements=$(kubectl exec -i $agbot -- curl -sS http://localhost:8080/agreement)

    activeAgreementList=$(echo $agreements | jq -r ".agreements.active[].current_agreement_id")
    printf "DEBUG: Active Agreement IDs... \n ${activeAgreementList} \n" |& tee -a log/agbot_${agbot}.log

    activeAgreements=$(echo $agreements | jq -r ".agreements.active[]")
    printf "DEBUG: Active Agreements... $activeAgreements \n\n\n\n" >> log/agbot_${agbot}.log 2>&1

    archivedAgreements=$(echo $agreements | jq -r ".agreements.archived[]")
    printf "DEBUG: Archived Agreements... $archivedAgreements \n\n\n\n" >> log/agbot_${agbot}.log 2>&1
}

function cleanHorizonExchange() {
    printf "CLEANING HORIZON EXCHANGE\n" |& tee log/cleaning-horizon-exchange.log

    #Capture horizon state: Exchange, Agent Node Listings
    printf "Looking for lingering agent nodes within the horizon exchange... \n" |& tee -a log/cleaning-horizon-exchange.log
    for NODE in $(hzn exchange node list | jq -r .[] | grep $nodesearchkey | awk -F '/' '{print $2}'); do echo "Node Exists: $NODE" ; done |& tee -a log/cleaning-horizon-exchange.log

    #Clean horizon state: Exchange, Agent Node Listings
    printf "Cleaning Horizon State: Exchange, Agent Node Listings: \n" |& tee -a log/cleaning-horizon-exchange.log
    for NODE in $(hzn exchange node list | jq -r .[] | grep $nodesearchkey | awk -F '/' '{print $2}'); do echo "Removing node $NODE"; sleep .1; hzn exchange node remove -f ${NODE} & done |& tee -a log/cleaning-horizon-exchange.log
    wait
}

function cleanHorizonAgbots() {
    agbots=$(kubectl get pod | grep "Running" | grep -v "agbot-db" | grep "agbot" | awk '{print $1}')
    for ab in ${agbots} ; do
        cleanHorizonAgbot ${ab}
    done
}

function cleanHorizonAgbot() {
    agbot=${1}
    printf "CLEANING HORIZON AGBOT\n" |& tee log/cleaning-horizon-${agbot}.log
    printf "DEBUG: Agbot... $agbot \n"  |& tee -a log/cleaning-horizon-${agbot}.log

    agreements=$(kubectl exec -i $agbot -- curl -sS http://localhost:8080/agreement)

    activeAgreements=$(echo $agreements | jq -r ".agreements.active[]")
    printf "DEBUG: Active Agreements... $activeAgreements \n\n\n\n" >> log/cleaning-horizon-${agbot}.log 2>&1

    archivedAgreements=$(echo $agreements | jq -r ".agreements.archived[]")
    printf "DEBUG: Archived Agreements... $archivedAgreements \n\n\n\n" >> log/cleaning-horizon-${agbot}.log 2>&1

    killAgreements=$(echo $agreements | jq -r ".agreements.active[].current_agreement_id")
    printf "DEBUG: KillAgreementIDs... \n ${killAgreements} \n" |& tee -a log/cleaning-horizon-${agbot}.log

    if [ -n "${killAgreements}" ]; then
        printf "Removing agreements from: $agbot \n" |& tee -a log/cleaning-horizon-${agbot}.log
        for agreement in ${killAgreements}; do
            printf "Deleting agreement: ${agreement} \n" |& tee -a log/cleaning-horizon-${agbot}.log
            deleteAgreement="curl -X DELETE -sS http://localhost:8080/agreement/${agreement}"
            printf "Running... kubectl exec -i $agbot -- $deleteAgreement \n"  |& tee -a log/cleaning-horizon-${agbot}.log
            kubectl exec -i $agbot -- $deleteAgreement |& tee -a log/cleaning-horizon-${agbot}.log
        done
    else
        printf "No agreements to remove from: $agbot \n" |& tee -a log/cleaning-horizon-${agbot}.log
    fi
}

function cleanHorizonAgents() {
    python3 -m scale.anaxremote -f config.json -l 0 -r 0 -c $COUNT prune |& tee log/cleaning-horizon-agents.log
    python3 -m tools.hosts -l 0 pushcommand -f config.json "rm -rf /root/scaler/log/* 2> /dev/null" |& tee -a log/cleaning-horizon-agents.log
}

function stopHorizon() {
    python3 -m tools.hosts -l 0 pushcommand -f config.json "systemctl stop horizon 2> /dev/null" |& tee -a log/stop-horizon.log
}

function cleanHorizon() {
    stopHorizon
    cleanHorizonExchange
    cleanHorizonAgbots
    cleanHorizonAgents
}

function cleanScaler() {
    printf "Cleaning any lingering scaler components... \n" |& tee log/cleaning-scaler.log
    python3 -m tools.hosts -l 0 pushcommand -f config.json "kill \$(ps aux | grep 'scale.anax' | grep -v grep | awk '{print \$2}') 2> /dev/null" |& tee -a log/cleaning-scaler.log
    python3 -m tools.hosts -l 0 pushcommand -f config.json "kill \$(ps aux | grep 'tools.hosts' | grep -v grep | awk '{print \$2}') 2> /dev/null" |& tee -a log/cleaning-scaler.log
}

function startAgents() {
    #start the agent containers
    python3 -m scale.anaxremote -f config.json -l 0 -r 1 -c $COUNT start |& tee log/agents-starting.log
}

function stopAgents() {
    #Stop all agent containers
    python3 -m scale.anaxremote -f config.json -l 0 -r 1 -c $COUNT stop  |& tee log/agents-stopping.log
}

function queryAgents() {
    #check how many containers were created
    python3 -m scale.anaxremote -f config.json -l 2 -r 1 queryrunning --count |& tee log/agents-queryrunning_$1.log

    #check the created containers are all in the running state
    python3 -m scale.anaxremote -f config.json -l 2 -r 1 validaterunning |& tee log/agents-validaterunning_$1.log
}

function agentsAreRunning(){
    #fail if the created containers are not all in the running state
    NOTRUNNING=$(python3 -m scale.anaxremote -f config.json -l 2 -r 1 validaterunning |& grep False | wc -l)
    if [ $NOTRUNNING -ne 0 ]; then
        echo "At least one agent container has not started properly.  System Exiting."
        exit
    fi
}

function initializeAgents(){
    startAgents
    queryAgents poststart
    agentsAreRunning
}

function destroyAgents() {
    stopAgents
    queryAgents poststop
}

function registerAgents() {
    #Perform registrations on all running containers
    python3 -m scale.anaxremote -f config.json -l $1 -r $2 -c $COUNT register -m $3 -s $4 ${pattern} |& tee log/register.log
}

function waitForAgreements() {
    timedBreak=$1
    timedBreakInit=`date +%s`

    #Wait for agreements to be established
    while [ $(python3 -m scale.anaxremote -f config.json -l 2 -r 1 -c $COUNT agreements |& grep False | wc -l) -ne 0 ]; do
        timedBreakCurr=`date +%s`
        timedBreakWait=$((timedBreakCurr-timedBreakInit))
        if [ ${timedBreak} -lt ${timedBreakWait} ]; then
            break
        fi
        echo "Waiting for agreements to be established.  Will sleep for 30 seconds and check again";
        sleep 30;
    done
}

function unregisterAgents() {
    #Unregister all agents
    python3 -m scale.anaxremote -f config.json -l $1 -r $2 -c $COUNT unregister -m $3 -s $4 |& tee log/unregister.log

    #keep checking until all agreements have been destroyed
    while [ $(python3 -m scale.anaxremote -f config.json -l 2 -r 1 -c $COUNT agreements |& grep True | wc -l) -ne 0 ]; do echo "Waiting for agreements to be destroyed.  Will sleep for ten seconds and check again"; sleep 10; done
}

function redactLogs() {
    #Redact your cloud token
    find ./log/ -type f -exec sed -i 's/$1/REDACTED/g' {} \;
}

function packageLogs() {
    d=$(date +%s)
    printf "$(date "+[%Y-%m-%d %H:%M:%S]" -d @${d})   Packaging Scale Assessment Run Data\n"

    #Package the run results
    if [ -d log ]; then
        [ -f run*.log ] && mv run*.log log
        tar -zcvf edgescale-log-$(date "+%Y%m%d_%H%M%S" -d @${d}).tar.gz log
    fi
}

function startAgentLogging() {
    printf "Starting Log Collection for Agents... \n" | tee log/agentlogging-starting.log
    python3 -m tools.hosts -l 0 pushcommand -f config.json "rm -rf /root/scaler/syslogs 2> /dev/null; mkdir /root/scaler/syslogs; cd /root/scaler/syslogs; \$(nohup tail -f /var/log/syslog | rotatelogs -n 10 \$(hostname)_syslog.log 3600 1> /dev/null 2> /dev/null &)"  | tee -a log/agentlogging-starting.log
}

function captureAgentLogging() {
    printf "Capturing Logs Collected for Agents... \n" | tee log/agentlogging-capture.log
    python3 -m tools.hosts -l 0 pushcommand -f config.json 'sldir=/root/scaler/syslogs; mkdir ${sldir} 2> /dev/null; cnts="docker ps --filter name=horizon -q"; for i in $(${cnts}); do docker logs $i > ${sldir}/$(hostname)_$(docker inspect --format={{.Name}} ${i} | tail -c +2).log ; done; find /root/scaler/syslogs -type f -name "*.log*" -exec sed -i "/GovernanceWorker: GovernanceWorker command processor waiting for device registration/d" {} \;'
    python3 -m tools.hosts -m 1 --headpseudodelay .05 -l 0 scpreceive -s /root/scaler/syslogs/ -d /root/scaler/log/syslogs/ -f config.json | tee -a log/agentlogging-capture.log

}

function stopAgentLogging() {
    printf "Stopping Log Collection for Agents... \n" | tee log/agentlogging-stopping.log
    python3 -m tools.hosts -l 0 pushcommand -f config.json "kill \$(ps -ef | grep 'tail -f /var/log/syslog' | grep -v grep | awk '{print \$2}') 2> /dev/null" | tee -a log/agentlogging-stopping.log
}

function captureAgbotLogging() {
    printf "Capturing Logs for Agbots...\n"
    ldnaCapURL="https://api.us-south.logging.cloud.ibm.com/v1/export?apps=edge-computing-agbot&to=$(date +%s)000&from=$(($(date +%s)-${1}))000"
    printf "URL: ${ldnaCapURL}\n"
    curl -sS "${ldnaCapURL}" -u e145a51f58e845ac898fd68cfd1f6d1d: | jq -r ._line | tee log/agbot_temp.log
    tac log/agbot_temp.log &> log/agbot-capture.log
    rm log/agbot_temp.log
}

function captureExchangeLogging() {
    printf "Capturing Logs for Exchange... \n"
    ldnaCapURL="https://api.us-south.logging.cloud.ibm.com/v1/export?apps=edge-computing-exchange&to=$(date +%s)000&from=$(($(date +%s)-${1}))000"
    printf "URL: ${ldnaCapURL}\n"
    curl -sS "${ldnaCapURL}" -u e145a51f58e845ac898fd68cfd1f6d1d: | jq -r ._line | tee log/exchange_temp.log
    tac log/exchange_temp.log &> log/exchange-capture.log
    rm log/exchange_temp.log
}

function stopLogging() {
    stopAgentLogging
}

function cleanLogs() {
    #Clean logging directory before run
    stopLogging
    rm -rf log/*
}

function markTime() {
    mark=`date +%s`
    echo ${mark} &> log/${1}time.log
}

function markStarttime() {
    markTime start
}
function markEndtime() {
    markTime end
}

function markRuntime() {
    secondsRunning > log/runtime.log
}

function readStartTime() {
    timefile=log/starttime.log
    time=$(head -n 1 ${timefile})
    echo ${time}
}

function readEndTime(){
    timefile=log/endtime.log
    time=$(head -n 1 ${timefile})
    echo ${time}
}

function secondsRunning() {
    if [ ! -e log/starttime.log ]; then
        markStarttime
    fi
    markEndtime
    starttime=$(readStartTime)
    endtime=$(readEndTime)
    runtime=$((endtime-starttime))
    echo ${runtime}
}

function killRun() {
    id=$(ps -ef | grep kickoff | grep -v grep | awk '{print $2}')
    if [ -n "${id}" ]; then
        echo "Killing Kickoff PID ${id}"
        kill ${id}
    else
        echo "Kickoff Not Running. Nothing To Kill."
    fi
}
