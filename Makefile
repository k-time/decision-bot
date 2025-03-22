run-foreground:
	docker start -a dbot-container
	# TODO: app doesn't handle SIGINT, so you have to docker stop it after you interrupt

run-background:
	echo 'Started bot at' `date` >> ./log.txt
	python notify_account.py
	docker start dbot-container

stop:
	docker stop dbot-container

restart:
	docker stop dbot-container
	echo 'Started bot at' `date` >> ./log.txt
	python notify_account.py
	docker start dbot-container

build:
	docker rm dbot-container
	docker build -t dbot-app .
	docker create --name dbot-container dbot-app

check:
	docker ps
