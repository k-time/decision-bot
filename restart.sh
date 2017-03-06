#!/bin/sh

echo 'Restarted bot at' `date` >> /home/ubuntu/decision_bot/log.txt
/home/ubuntu/decision_bot/stop.sh
/home/ubuntu/decision_bot/start-background.sh
