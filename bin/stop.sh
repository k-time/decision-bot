#!/bin/sh

BOT_HOME=$HOME/decision_bot

cd $BOT_HOME
echo "Processes before:"
./bin/check.sh
pkill -f decision_bot.py
echo "Processes after:"
./bin/check.sh
echo "Decision bot stopped."
