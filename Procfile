web: gunicorn -c /home/justinnhli/git/demograder/gunicorn.conf demograder.wsgi:application
redis: redis-server
rqworker: DJANGO_SETTINGS_MODULE=demograder.settings rqworker dispatch evaluation
