#!/usr/bin/env bash
translateStart="tr '\n' '\r'"
translateEnd="tr '\r' '\n'"
replaceKey="\"APIListen\": \"0.0.0.0:80\",\r"
replaceValue="\"APIListen\": \"0.0.0.0:80\",\r        \"ExchangeMessageTTL\": 120,\r"
anaxjsonupdate="cat /etc/horizon/anax.json | ${translateStart} | sed -e 's/${replaceKey}/${replaceValue}/'  | ${translateEnd} > /root/scaler/anax.json"
eval ${anaxjsonupdate}
