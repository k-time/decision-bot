#!/bin/sh

BOT_HOME=$HOME/decision_bot

echo 'Restarted bot at' `date` >> $BOT_HOME/log.txt
$BOT_HOME/stop.sh
$BOT_HOME/start-background.sh
