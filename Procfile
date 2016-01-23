web: gunicorn djangosite.wsgi -c gunicorn.conf
redis: redis-server
rqworker: DJANGO_SETTINGS_MODULE=djangosite.settings rqworker
