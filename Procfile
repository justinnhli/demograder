web: gunicorn -c /home/justinnhli/git/demograder/gunicorn.conf demograder.wsgi:application
redis: redis-server
evaluation_rqworker: DJANGO_SETTINGS_MODULE=demograder.settings rqworker evaluation
dispatch_rqworker: DJANGO_SETTINGS_MODULE=demograder.settings rqworker dispatch
