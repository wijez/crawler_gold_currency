import asyncio
import json
from datetime import datetime

import requests
from redis import Redis
from celery import Celery, shared_task
from celery import shared_task
from asgiref.sync import async_to_sync

from app.core import get_settings, Config
from app.services import GoldService
from app.utils import send_email

settings = get_settings()
logger = Config.setup_logging()
redis_client = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
celery_app = Celery('crawler_gold_currency', broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_RESULT_BACKEND)


@shared_task(bind=True, queue='emails', routing_key='email.send')
def get_mail_by_id_task(to: str, subject: str, contents: dict):
    send_email(to=to, subject=subject, contents=contents)
    logger.info("task: get_mail_by_id_task called")
    return "Celery and Redis are working!"


@shared_task(bind=True)
def fun(self):
    # operations
    print("You are in Fun function")
    return "done"


@shared_task(bind=True)
def send_email_task_celery(self, user_id: int):
    # mail_subject = "Gold price"
    # message = {
    #     "Gold Data": "data from gold api"
    # }
    # user_email = "viet.info.43@gmail.com"
    # async_to_sync(send_email)(to=user_email, subject=mail_subject, contents=message)
    # print("You are in send_email_task function")
    # return "Task send mail successfully!"
    mail_subject = "Gold price"
    gold_data = async_to_sync(GoldService.get_goldapi)()
    message = {
        "Gold Data": gold_data
    }
    user_email = "viet.info.43@gmail.com"

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        loop.create_task(send_email(to=user_email, subject=mail_subject, contents=message))
    else:
        asyncio.run(send_email(to=user_email, subject=mail_subject, contents=message))

    print("You are in send_email_task function")
    return "Task send mail successfully!"
