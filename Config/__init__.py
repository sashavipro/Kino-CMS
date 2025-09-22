# Это гарантирует, что приложение Celery будет загружено при запуске Django
from .celery_app import app as celery_app

__all__ = ('celery_app',)

