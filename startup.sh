python manage.py migrate
celery -A ESIRecruiter worker --loglevel=INFO --concurrency=10 -n worker1@%h --detach
gunicorn --bind=0.0.0.0 --timeout 1800 --max-requests 500 --max-requests-jitter 10  ESIRecruiter.wsgi
