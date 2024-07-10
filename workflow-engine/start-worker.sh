#!/usr/bin/env bash

ps -ef|grep python|grep duang_worker|grep " 1 "|awk '{print $2;}'|xargs -i kill {}
ps -ef|grep python|grep duang_beat|grep " 1 "|awk '{print $2;}'|xargs -i kill {}

sleep 2

ps -ef|grep python|grep duang_worker|awk '{print $2;}'|xargs -i kill -9 {}
ps -ef|grep python|grep duang_beat|awk '{print $2;}'|xargs -i kill -9 {}

export _IN_CELERY=1

nohup python ./duang_worker.py>>/alidata1/admin/logs/duang/worker.log 2>&1 &
nohup python ./duang_beat.py>>/alidata1/admin/logs/duang/beat.log 2>&1 &
