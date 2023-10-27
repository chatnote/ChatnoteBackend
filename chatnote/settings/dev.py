import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from chatnote.settings.base import *

sentry_sdk.init(
    dsn="https://d5e9648a5ed89933e97dc6ebb4ad2ec9@o4505662187569152.ingest.sentry.io/4505991435911168",
    integrations=[DjangoIntegration()],
    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    send_default_pii=True,
    environment="dev",
)


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
ENV = 'dev'
WSGI_APPLICATION = "chatnote.wsgi.dev.application"

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

ES_USER = os.getenv("ES_USER")
ES_PASSWORD = os.getenv("ES_PASSWORD")
ES_CLOUD_ID = os.getenv("ES_CLOUD_ID")

CHUNKED_DOCUMENT_INDEX = os.getenv("DEV_CHUNKED_DOCUMENT_INDEX")

NOTION_CLIENT_ID = os.getenv("DEV_NOTION_CLIENT_ID")
NOTION_SECRET = os.getenv("DEV_NOTION_SECRET")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
