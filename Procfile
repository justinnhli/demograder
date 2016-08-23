web: gunicorn -c /home/justinnhli/git/demograder/gunicorn.conf djangosite.wsgi:application
redis: redis-server
rqworker: DJANGO_SETTINGS_MODULE=djangosite.settings rqworker dispatch evaluation
