python manage.py migrate
celery -A ESIRecruiter worker --loglevel=INFO --concurrency=10 -n worker1@%h --detach
celery -A ESIRecruiter beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler --logfile /home/site/logs/chapman-experiments-dev/celery_log.log --detach
gunicorn --bind=0.0.0.0 --timeout 1800 --max-requests 500 --max-requests-jitter 10  ESIRecruiter.wsgi