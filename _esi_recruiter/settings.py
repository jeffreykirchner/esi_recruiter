"""
Django settings for _esi_recruiter project.
"""

import os

try:
    from .local_settings import *
except ImportError:

    #import azure settings
    try:
        from .prod_settings import *
    except ImportError:
        pass

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/


# Application definition

INSTALLED_APPS = [    
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',    
    'django.contrib.humanize',
    'django.contrib.sites',  
    'django.contrib.sitemaps',
    'main',
    'crispy_forms',
    'crispy_bootstrap5',
    'django.contrib.admin',
    'tinymce',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',    
]

ROOT_URLCONF = '_esi_recruiter.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                '_esi_recruiter.context_processors.get_debug',
            ],
        },
    },
]

WSGI_APPLICATION = '_esi_recruiter.wsgi.application'


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

#head text of admin site
ADMIN_SITE_HEADER = 'ESI Recruiter Administration'

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

#boot stramp applied to form templates
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

#tiny MCE
TINYMCE_DEFAULT_CONFIG = {
    "height" : 600,
    "menubar": False,
    "convert_urls": False,
    "promotion": False,
    "menubar": "file edit view insert format tools table help",
    "plugins": "advlist autolink lists link image charmap anchor searchreplace visualblocks code fullscreen insertdatetime media table paste code help wordcount",
    "toolbar": "undo redo | bold italic underline strikethrough | fontselect fontsizeselect formatselect | alignleft aligncenter alignright alignjustify | outdent indent |  numlist bullist checklist | forecolor backcolor casechange permanentpen formatpainter removeformat | pagebreak | charmap emoticons | fullscreen  preview save | insertfile image media pageembed template link anchor codesample | a11ycheck ltr rtl | showcomments addcomment code",
    "custom_undo_redo_levels": 10,
}

AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.AllowAllUsersModelBackend']

#cookies
#CSRF_COOKIE_SECURE = True
#SESSION_COOKIE_SECURE = True

#site framework
SITE_ID = 1

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'
