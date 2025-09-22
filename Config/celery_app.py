import os
from celery import Celery

# Устанавливаем переменную окружения, чтобы Celery знал, где найти настройки Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Config.settings')

# Создаем экземпляр приложения Celery
app = Celery('Config')

# Загружаем конфигурацию из настроек Django.
# namespace='CELERY' означает, что все настройки Celery в settings.py должны начинаться с CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически обнаруживаем и регистрируем задачи из всех файлов tasks.py в приложениях Django
app.autodiscover_tasks()