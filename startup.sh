echo "*** Startup.sh ***"
echo "Run Migrations:"
python manage.py migrate
echo "Start gunicorn:"
gunicorn --bind=0.0.0.0 --timeout 1800 --max-requests 500 --workers=2 --max-requests-jitter 10  ESIRecruiter.wsgi --access-logfile '-' --error-logfile '-'