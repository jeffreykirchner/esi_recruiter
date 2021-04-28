python manage.py migrate
celery -A ESIRecruiter worker --loglevel=INFO -n worker1@%h --logfile /home/site/logs/chapman-experiments-dev/celery_worker.log --detach
celery -A ESIRecruiter beat -l INFO -S django --logfile /home/site/logs/chapman-experiments-dev/celery_beat.log -s /home/site/logs/chapman-experiments-dev/celerybeat-schedule --detach
gunicorn --bind=0.0.0.0 --timeout 1800 --max-requests 500 --max-requests-jitter 10  ESIRecruiter.wsgi