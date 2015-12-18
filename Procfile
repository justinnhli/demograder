web: gunicorn djangosite.wsgi --bind 127.0.0.1:8000
redis: redis-server
rqworker: DJANGO_SETTINGS_MODULE=djangosite.settings rqworker
