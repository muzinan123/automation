#!/usr/bin/env bash

ps -ef|grep python|grep cmdb_docker|grep " 1 "|awk '{print $2;}'|xargs -i kill {}
ps -ef|grep celeryd|grep MainProcess|awk '{print $2;}'|xargs -i kill {}
ps -ef|grep celery|grep beat|awk '{print $2;}'|xargs -i kill {}

nohup python ./cmdb_docker_worker.py>>/alidata1/admin/logs/cmdb-docker/worker.log 2>&1 &
nohup python ./cmdb_docker_beat.py>>/alidata1/admin/logs/cmdb-docker/beat.log 2>&1 &
