import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

DEBUG = False

ALLOWED_HOSTS = [
    '158.160.11.226',
    'localhost',
    '127.0.0.1',
    '[::1]',
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'api.apps.ApiConfig',
    'users.apps.UsersConfig',
    'rest_framework',
    'drf_yasg',
    'rest_framework.authtoken',
    'djoser',
    'debug_toolbar',
    'django_filters',
    'corsheaders',
    'v1',
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'foodgram.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'foodgram.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': os.getenv(
            key='DB_ENGINE',
            default='django.db.backends.postgresql'
        ),
        'NAME': os.getenv(
            key='DB_NAME',
            default='postgres'
        ),
        'USER': os.getenv(
            key='POSTGRES_USER',
            default='postgres'
        ),
        'PASSWORD': os.getenv(
            key='POSTGRES_PASSWORD',
            default='29051994'
        ),
        'HOST': os.getenv(
            key='DB_HOST',
            default='database_container'
        ),
        'PORT': os.getenv(
            key='DB_PORT',
            default='5432'
        )
    }
}
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.'
                'password_validation.'
                'UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.'
                'password_validation.'
                'MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.'
                'password_validation.'
                'CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.'
                'password_validation.'
                'NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'ru'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_ROOT = BASE_DIR / 'static'

STATIC_URL = '/static/'

MEDIA_ROOT = BASE_DIR / 'media'

MEDIA_URL = '/media/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MIN_COOKING_TIME = 1

MAX_CHARFIELD_LENGTH = 200

MAX_PASSWORD_LENGTH = 150

MAX_NAMES_LENGTH = 150

MAX_EMAIL_LENGTH = 254

COLORFIELD_LENGTH = 7

AUTH_USER_MODEL = 'users.User'

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'api.v1.paginations.PageLimitPagination',
    'PAGE_SIZE': 6,
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
}

DJOSER = {
    'PERMISSIONS': {
        'set_password': ['djoser.permissions.CurrentUserOrAdmin'],
        'user_create': ['rest_framework.permissions.AllowAny'],
        'user': ['api.v1.permissions.ReadOnly'],
        'token_create': ['rest_framework.permissions.AllowAny'],
        'token_destroy': ['rest_framework.permissions.IsAuthenticated'],
        'user_list': ['rest_framework.permissions.AllowAny'],

        'username_reset_confirm': ['api.v1.permissions.BlockedAccess'],
        'password_reset': ['api.v1.permissions.BlockedAccess'],
        'password_reset_confirm': ['api.v1.permissions.BlockedAccess'],
        'set_username': ['api.v1.permissions.BlockedAccess'],
        'user_delete': ['api.v1.permissions.BlockedAccess'],
        'username_reset': ['api.v1.permissions.BlockedAccess'],
        'activation': ['api.v1.permissions.BlockedAccess'],

    },
    'SERIALIZERS': {
        'set_password': 'djoser.serializers.SetPasswordSerializer',
        'user': 'api.v1.serializers.UserSerializer',
        'user_create': 'djoser.serializers.UserCreateSerializer',
        'current_user': 'api.v1.serializers.UserSerializer',
        'token': 'djoser.serializers.TokenSerializer',
        'token_create': 'djoser.serializers.TokenCreateSerializer',
    },
    'HIDE_USERS': False  # allow anonymous user to get list of users
}

CORS_URLS_REGEXES = [
    r'^/api/.*$',
    r'^/admin/.*$',
    r'^/swagger/.*$'
]
