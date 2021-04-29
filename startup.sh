\#!/bin/bash
python manage.py migrate
apt-get -y install htop
apt-get -y install supervisor
mkdir /var/log/celery/
mkdir /var/log/supervisord/
cp supervisord.conf /etc/supervisor/conf.d/
supervisorctl reread
supervisorctl update
supervisord -c celeryd.conf
gunicorn --bind=0.0.0.0 --timeout 1800 --max-requests 500 --max-requests-jitter 10  ESIRecruiter.wsgi