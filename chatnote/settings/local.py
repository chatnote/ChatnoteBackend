from chatnote.settings.base import *

DEBUG = True
ENV = 'local'
WSGI_APPLICATION = "chatnote.wsgi.local.application"

ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.getenv("LOCAL_AWS_DB_NAME"),
        "USER": os.getenv("LOCAL_AWS_DB_USER"),
        "PASSWORD": os.getenv("LOCAL_AWS_DB_PASSWORD"),
        "HOST": os.getenv("LOCAL_AWS_DB_HOST"),
        "PORT": os.getenv("LOCAL_AWS_DB_PORT"),
    },
}

NOTION_CLIENT_ID = os.getenv("NOTION_CLIENT_ID")
NOTION_SECRET = os.getenv("NOTION_SECRET")

ES_USER = os.getenv("ES_USER")
ES_PASSWORD = os.getenv("ES_PASSWORD")
ES_CLOUD_ID = os.getenv("ES_CLOUD_ID")

ORIGINAL_DOCUMENT_INDEX = os.getenv("LOCAL_ORIGINAL_DOCUMENT_INDEX")
CHUNKED_DOCUMENT_INDEX = os.getenv("LOCAL_CHUNKED_DOCUMENT_INDEX")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
