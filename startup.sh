\#!/bin/bash
python manage.py migrate
apt-get -y install htop
apt-get -y install systemd
/etc/init.d/dbus start
cp celery.service /etc/systemd/system/
systemctl daemon-reload
mkdir /etc/conf.d/
mkdir /var/run/celery/
mkdir /var/log/celery/
gunicorn --bind=0.0.0.0 --timeout 1800 --max-requests 500 --max-requests-jitter 10  ESIRecruiter.wsgi