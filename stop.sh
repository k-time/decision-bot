#!/bin/sh

echo "Processes before:"
ps ax | grep decision_bot
pkill python3
echo "Proccesses after:"
ps ax | grep decision_bot
echo "Decision bot stopped."
