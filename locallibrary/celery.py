import os
from celery import Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'locallibrary.settings')
celery_app = Celery('locallibrary')
celery_app.config_from_object('django.conf:settings', namespace='CELERY')
celery_app.autodiscover_tasks()

# celery -A locallibrary worker --loglevel=info --pool=solo