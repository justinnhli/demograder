#!/bin/sh

rm -f db.sqlite3 &&
	rm -f dump.rdb &&
	rm -f demograder/migrations/*.py &&
	rm -rf $(find . -maxdepth 2 -name __pycache__) &&
	./manage.py migrate &&
	./manage.py createsuperuser &&
	./manage.py makemigrations demograder &&
	./manage.py migrate &&
	for fixture in demograder/fixtures/*.json; do
		./manage.py loaddata "$fixture"
	done
