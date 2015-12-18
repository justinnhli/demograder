# Demograder #

> The best answer to the question, "What is the most effective method of teaching?" is that it depends on the goal, the student, the content, and the teacher. But the next best answer is, "students teaching other students". - Wilbert J. McKeachie

For a description of the general idea, read [this blog post](https://howtostartacsdept.wordpress.com/2015/12/02/step-29-design-an-autograder/).

## Requirements ##

Demograder uses an all-Python stack:

* Python 3.5+ (for [subprocess.run](https://docs.python.org/dev/library/subprocess.html#subprocess.run))
* [Django](https://www.djangoproject.com/) as the web framework
* [RQ](http://python-rq.org/) as the job queue
* [Honcho](https://github.com/nickstenning/honcho/) as the process manager

## Running ##

0. Go to the root of this repository

		cd demograder

1. Set up a virtual environment with the necessary packages

		virtualenv venv
		source venv/bin/activation
		pip install -r requirements.txt

2. Start the services

		honcho start
