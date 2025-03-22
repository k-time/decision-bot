run-background:
	@if docker ps | grep 'dbot-container'; then \
		echo 'DecisionBot is already running'; \
	else \
		python notify_account.py; \
		docker start dbot-container; \
		echo 'Started bot at' `date` | tee ./log.txt; \
	fi

stop:
	docker stop dbot-container

restart:
	docker stop dbot-container
	python notify_account.py
	docker start dbot-container
	echo 'Restarted bot at' `date` | tee ./log.txt

build:
	docker rm dbot-container
	docker build -t dbot-app .
	docker create --name dbot-container dbot-app

check:
	docker ps
