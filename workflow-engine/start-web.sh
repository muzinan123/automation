#!/usr/bin/env bash

cat /alidata1/admin/logs/duang/*.pid|xargs -i kill -HUP {}