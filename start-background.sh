#!/bin/sh

if ! pgrep -f 'decision_bot.py'
then
	nohup python3 /home/ubuntu/decision_bot/decision_bot.py &
	echo 'Started bot at' `date` >> /home/ubuntu/decision_bot/log.txt
	echo '-------------' >> /home/ubuntu/decision_bot/log.txt
	ps ax | grep decision_bot
fi
