#!/bin/bash
cd /Users/sylvanzhang/code/vncmanagementdb
source django/bin/activate
export PYTHONPATH="/Users/sylvanzhang/code/vncmanagementdb:$PYTHONPATH"
celery -A apps.novncdb worker -l info

