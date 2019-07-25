#!/usr/bin/env bash

#kill any lingering scaler processes that might be present as a result of failures
for i in $(cat config.json | jq -r '.endpoints | .[]'); do ssh root@$i "hostname & pkill -f scale.anaxscale" ; done

#validate no lingering scaler processes exist
for i in $(cat config.json | jq -r '.endpoints | .[]'); do ssh root@$i "hostname & ps -ef | grep scale.anaxscale | grep -v grep | awk '{ print $2}'" ; done

