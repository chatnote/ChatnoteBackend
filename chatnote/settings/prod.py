from chatnote.settings.base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
ENV = 'prod'
WSGI_APPLICATION = "chatnote.wsgi.prod.application"

ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.getenv("DEV_AWS_DB_NAME"),
        "USER": os.getenv("DEV_AWS_DB_USER"),
        "PASSWORD": os.getenv("DEV_AWS_DB_PASSWORD"),
        "HOST": os.getenv("DEV_AWS_DB_HOST"),
        "PORT": os.getenv("DEV_AWS_DB_PORT"),
    },
}

ES_USER = os.getenv("DEV_ES_USER")
ES_PASSWORD = os.getenv("DEV_ES_PASSWORD")
ES_CLOUD_ID = os.getenv("DEV_ES_CLOUD_ID")

CHUNKED_DOCUMENT_INDEX = os.getenv("DEV_CHUNKED_DOCUMENT_INDEX")

NOTION_CLIENT_ID = os.getenv("DEV_NOTION_CLIENT_ID")
NOTION_SECRET = os.getenv("DEV_NOTION_SECRET")
NOTION_REDIRECT_URL = os.getenv("DEV_NOTION_REDIRECT_URL")
NOTION_AUTH_URL = os.getenv("DEV_NOTION_AUTH_URL")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_CALLBACK_URI = os.getenv("GOOGLE_REDIRECT_URL")
