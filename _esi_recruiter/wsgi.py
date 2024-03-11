"""
WSGI config for _esi_recruiter project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '_esi_recruiter.settings')

application = get_wsgi_application()
