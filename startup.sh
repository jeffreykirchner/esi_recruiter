echo "*** Startup.sh ***"
echo "Run Migrations:"
python manage.py migrate
echo "Start gunicorn:"
gunicorn --bind=0.0.0.0 --timeout 600 --workers=2 ESIRecruiter.wsgi --access-logfile '-' --error-logfile '-'