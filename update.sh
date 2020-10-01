#!/bin/bash
echo "Updating ESI Recruiter"
echo ""
source ESIRecruiterEnv/bin/activate
echo ""
git pull origin master
echo ""
python manage.py migrate
echo ""
echo "Restarting gunicorn ... "
echo $1 | sudo -S systemctl restart gunicorn
echo ""
deactivate
echo "Done"
