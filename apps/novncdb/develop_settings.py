import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        "NAME": os.environ.get("POSTGRES_DB", "externaldb"),
        "USER": os.environ.get("POSTGRES_USER", "novncserver"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "novncserver"),
    }
}

REDIS_CONF = {
    "host": os.environ.get("REDIS_HOST", "127.0.0.1"),
    "port": os.environ.get("REDIS_PORT", "6379"),
}

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]

DATA_DIR = os.environ.get("NOVNC_DATA_DIR", "{}/data".format(BASE_DIR))
