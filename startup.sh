#!/bin/bash
process='websocket_main.py'
log="log"
data=$(date +"%Y-%m-%d %H:%M:%S")

while true
do

  exists=`ps -ef|grep "$i"|grep -v grep|wc -l`
  if [ "$exists" -eq "0" ]; then
    echo "${data} : ${i} already running" >> $log
  else
    echo "starting"
    python3 websocket_main.py
  fi

  sleep 10
done