import os

from .settings import *  # noqa: F403

if os.getenv("USE_POSTGRES_FOR_TESTS") != "1":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.getenv("SQLITE_DB_NAME", BASE_DIR / "test_db.sqlite3"),  # noqa: F405
            "TEST": {
                "NAME": os.getenv("SQLITE_DB_NAME", BASE_DIR / "test_db.sqlite3"),  # noqa: F405
            },
        }
    }
