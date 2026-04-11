import os
from dotenv import load_dotenv

load_dotenv()

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "django-cursor-pagination",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "localhost",
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}

INSTALLED_APPS = ["tests"]

SECRET_KEY = "secret"
