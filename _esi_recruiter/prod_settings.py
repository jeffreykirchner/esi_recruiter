import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['SECRET_KEY']

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS').split()
CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS').split()

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG',False)

#STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
# STATICFILES_STORAGE = '_esi_recruiter.custom_azure.AzureStaticStorage'
# STATIC_ROOT = os.environ['STATIC_ROOT']
# STATIC_URL = os.environ['STATIC_URL']

# MEDIA_ROOT = os.environ['MEDIA_ROOT']
# DEFAULT_FILE_STORAGE = '_esi_recruiter.custom_azure.AzureMediaStorage'
# AZURE_CONTAINER =  os.environ['AZURE_CONTAINER']
# AZURE_ACCOUNT_NAME = os.environ['AZURE_ACCOUNT_NAME']
# AZURE_ACCOUNT_KEY = os.environ['AZURE_ACCOUNT_KEY']
# AZURE_CUSTOM_DOMAIN = os.environ['AZURE_CUSTOM_DOMAIN']
# AZURE_OVERWRITE_FILES = True

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.azure_storage.AzureStorage",
        "OPTIONS": {
            "account_key": os.environ['AZURE_ACCOUNT_KEY'],
            "custom_domain": os.environ['AZURE_CUSTOM_DOMAIN'],
            "account_name": os.environ['AZURE_ACCOUNT_NAME'],
            "azure_container": os.environ['AZURE_CONTAINER'],
            "overwrite_files": True,
            "location": "media",
        },
    },
    "staticfiles": {
        "BACKEND": "storages.backends.azure_storage.AzureStorage",
        "OPTIONS": {
            "account_key": os.environ['AZURE_ACCOUNT_KEY'],
            "custom_domain": os.environ['AZURE_CUSTOM_DOMAIN'],
            "account_name": os.environ['AZURE_ACCOUNT_NAME'],
            "azure_container": os.environ['AZURE_CONTAINER'],
            "overwrite_files": True,  
            "location": "static",         
        },       
    },
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ['DBNAME'],
        'HOST': os.environ['DBHOST'],
        'USER': os.environ['DBUSER'],
        'PASSWORD': os.environ['DBPASS'],
        'OPTIONS': {'sslmode': 'prefer'},
        'CONN_MAX_AGE' : 60,
    },
}

#logging, log both to console and to file log at the INFO level
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'info_format': {
            'format': '%(levelname)s %(asctime)s %(module)s: %(message)s'
            }
        },
    'handlers': {
        'console': {
            'level':'INFO',
            'class': 'logging.StreamHandler',
        },
       'logfile': {        
           'level':'INFO', 
           'class': 'logging.handlers.RotatingFileHandler',
           'filename': os.environ['LOG_LOCATION'],
           'maxBytes': 10485760,           #10 mb
           'backupCount' : 5,
           'formatter' : 'info_format',
           'delay': True,
       },
    },
    'loggers': {
        'django': {
            'handlers':['console','logfile'],
            'propagate': True,
            'level':'INFO',
        },
        'django.db.backends': {
            'handlers': ['console','logfile'],
            'level': 'INFO',
            'propagate': False,
        },
        'main': {
            'handlers': ['console', 'logfile'],
            'level': 'INFO',           
        },
        'django_cron': {
            'handlers': ['console', 'logfile'],
            'level': 'INFO',           
        },
    },
}

PPMS_HOST = os.environ['PPMS_HOST']
PPMS_USER_NAME = os.environ['PPMS_USER_NAME']
PPMS_PASSWORD = os.environ['PPMS_PASSWORD']

#email service
EMAIL_MS_HOST = os.environ['EMAIL_MS_HOST']
EMAIL_MS_USER_NAME = os.environ['EMAIL_MS_USER_NAME']
EMAIL_MS_PASSWORD = os.environ['EMAIL_MS_PASSWORD']
