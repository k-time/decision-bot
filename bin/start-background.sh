#!/bin/sh

BOT_HOME=$HOME/decision_bot

if ! pgrep -f 'decision_bot.py'
then
	cd $BOT_HOME
	nohup python3.6 ./notify_account.py &
	nohup python3.6 ./decision_bot.py &
	echo 'Started bot at' `date` >> ./log.txt
	echo '-------------' >> ./log.txt
	./bin/check.sh
fi
