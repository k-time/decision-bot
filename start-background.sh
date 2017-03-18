#!/bin/sh

BOT_HOME=$HOME/decision_bot

if ! pgrep -f 'decision_bot.py'
then
	nohup python3 $BOT_HOME/decision_bot.py &
	echo 'Started bot at' `date` >> $BOT_HOME/log.txt
	echo '-------------' >> $BOT_HOME/log.txt
	$BOT_HOME/check.sh
fi
