#!/bin/sh

BOT_HOME=$HOME/decision_bot

echo "Processes before:"
$BOT_HOME/check.sh
pkill -f decision_bot.py
echo "Processes after:"
$BOT_HOME/check.sh
echo "Decision bot stopped."
