from celery import Celery
from api.core.config import settings

celery_app = Celery(
    "vidinie",
    broker=settings["redis_uri"],
    backend=settings["redis_uri"],
)