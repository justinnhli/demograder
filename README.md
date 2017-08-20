# Demograder

> The best answer to the question, "What is the most effective method of teaching?" is that it depends on the goal, the student, the content, and the teacher. But the next best answer is, "students teaching other students". - Wilbert J. McKeachie

For a description of the general idea, read [this blog post](https://howtostartacsdept.wordpress.com/2015/12/02/step-29-design-an-autograder/).

## Requirements

Demograder uses an all-Python stack:

* Python 3.5+ (for [subprocess.run](https://docs.python.org/dev/library/subprocess.html#subprocess.run))
* [Django](https://www.djangoproject.com/) as the web framework
* [RQ](http://python-rq.org/) as the job queue
* [Honcho](https://github.com/nickstenning/honcho/) as the process manager
* [pytz](http://pytz.sourceforge.net/) for timezone data

## Running

1. Go to the root of this repository

		cd demograder

1. Set up a virtual environment with the necessary packages

		python3 -m venv /PATH/TO/VENV/demograder
		source /PATH/TO/VENV/demograder/bin/activation
		pip install -r requirements.txt

1. Change directory paths in `Procfile`, `gunicorn.conf`, and `nginx.conf`

1. Copy/link the nginx configuration `nginx.conf` to `/etc/nginx/sites-enabled/`

1. Create `demograder/secrets.json`

1. Set up django by running:

		./manage.py migrate
		./manage.py createsuperuser
		./manage.py makemigrations demograder
		./manage.py migrate
		./manage.py collectstatic

1. Load fixtures in `demograder/fixtures`:

		./manage.py loaddata demograder/fixtures/$FIXTURE

1. (Re-)Start nginx:

		sudo service nginx restart

1. Start the services with `honcho start`, or to specific the number of workers, `honcho start -c rqworker=4`

## Known Issues

* Project dependencies cannot be concurrent - no new submissions are expected from the dependent project
* A number of settings (datetime format, timezones, etc.) are not yet configurable in settings.py
