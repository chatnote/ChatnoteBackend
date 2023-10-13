from chatnote.settings.base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
ENV = 'prod'
WSGI_APPLICATION = "chatnote.wsgi.prod.application"

ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.getenv("PROD_AWS_DB_NAME"),
        "USER": os.getenv("PROD_AWS_DB_USER"),
        "PASSWORD": os.getenv("PROD_AWS_DB_PASSWORD"),
        "HOST": os.getenv("PROD_AWS_DB_HOST"),
        "PORT": os.getenv("PROD_AWS_DB_PORT"),
    },
}
