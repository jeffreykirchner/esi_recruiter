python manage.py migrate
celery -A ESIRecruiter purge -f
celery -A ESIRecruiter worker -E -l INFO --time-limit 120 &
celery -A ESIRecruiter beat -l INFO -S django_celery_beat.schedulers:DatabaseScheduler &
gunicorn --bind=0.0.0.0 --timeout 1800 --max-requests 500 --max-requests-jitter 10  ESIRecruiter.wsgi