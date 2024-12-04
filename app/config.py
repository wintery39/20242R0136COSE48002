import os
from dotenv import load_dotenv

load_dotenv()

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND")
DATABASE_URL = os.getenv("DATABASE_URL")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
NAVER_ACCESS_KEY = os.getenv("NAVER_ACCESS_KEY")
NAVER_SECRET_KEY = os.getenv("NAVER_SECRET_KEY")