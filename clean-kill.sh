#!/usr/bin/env bash
echo "Start"
echo "Stage 1"
id=$(ps -ef | grep scale. | grep -v grep | cut -d " " -f 6)
while [ -n "${id}" ]; do
    kill -9 ${id} 2> /dev/null
    id=$(ps -ef | grep scale. | grep -v grep | cut -d " " -f 6)
done

echo "Stage 2"
id=$(ps -ef | grep tools. | grep -v grep | cut -d " " -f 6)
while [ -n "${id}" ]; do
    kill -9 ${id} 2> /dev/null
    id=$(ps -ef | grep tools. | grep -v grep | cut -d " " -f 6)
done

echo "Stage 3"
id=$(ps -ef | grep kick | grep -v grep | cut -d " " -f 6)
while [ -n "${id}" ]; do
    kill -9 ${id} 2> /dev/null
    id=$(ps -ef | grep kick | grep -v grep | cut -d " " -f 6)
done


echo "Stage 4"
id=$(ps -ef | grep clean | grep -v grep | cut -d " " -f 6)
while [ -n "${id}" ]; do
    kill -9 ${id} 2> /dev/null
    id=$(ps -ef | grep clean | grep -v grep | cut -d " " -f 6)
done
echo "Done"