from celery import Celery

BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
capp = Celery('tasks', broker=BROKER_URL, backend=CELERY_RESULT_BACKEND)