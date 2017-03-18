#!/bin/sh

BOT_HOME=$HOME/decision_bot

cd $BOT_HOME
echo 'Restarted bot at' `date` >> ./log.txt
./bin/stop.sh
./bin/start-background.sh
