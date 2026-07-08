import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "12377"),
        "NAME": os.environ.get("POSTGRES_DB", "vncserverdb"),
        "USER": os.environ.get("POSTGRES_USER", "novncserver"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "novncserver"),
    }
}

REDIS_CONF = {
    "host": os.environ.get("REDIS_HOST", "127.0.0.1"),
    "port": os.environ.get("REDIS_PORT", "55555"),
}

DEBUG = False

ALLOWED_HOSTS = ["*"]

DATA_DIR = os.environ.get("NOVNC_DATA_DIR", "/data")
