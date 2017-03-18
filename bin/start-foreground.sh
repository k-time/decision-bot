#!/bin/sh

BOT_HOME=$HOME/decision_bot

if ! pgrep -f 'decision_bot.py'
then
	cd $BOT_HOME
	echo 'Started decision bot...'
	python3 ./decision_bot.py -d
fi
