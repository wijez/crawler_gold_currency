from datetime import datetime

from celery import Celery
from celery.result import AsyncResult

from app.crud import crud_user
from app.tasks.task import get_mail_by_id_task, send_email_task_celery
from fastapi import status, Depends, APIRouter, HTTPException, BackgroundTasks
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from starlette.responses import JSONResponse

from app.core import get_settings, Config
from app.apis.depends import get_session
from app.apis.depends.check_auth import check_auth
from app.services.gold_service import GoldService
from app.constant import CurrencyCode, MetalSymbol

logger = Config.setup_logging()
settings = get_settings()

router = APIRouter(prefix="/price", tags=["currency"])
celery_app = Celery('gold_service', broker=settings.REDIS_URL, backend=settings.REDIS_URL)


@router.get('')
async def make_gapi_request(symbol: MetalSymbol, curr: CurrencyCode, date: str, session: get_session):
    gold_service = GoldService(session=session)
    result = await gold_service.get_goldapi_request(symbol, curr, date)
    return result


@router.post('')
async def send_gold_currency(symbol: MetalSymbol,
                             curr: CurrencyCode,
                             date: str,
                             session: get_session,
                             user_decode: HTTPAuthorizationCredentials = Depends(check_auth)):
    gold_service = GoldService(session=session)
    result = await gold_service.get_mail_by_id(user_id=user_decode["user_id"], symbol=symbol, curr=curr, date=date)
    return result


@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)
    if task_result.state == 'PENDING':
        response = {
            "task_status": task_result.state,
            "task_result": None
        }
    elif task_result.state != 'FAILURE':
        response = {
            "task_status": task_result.state,
            "task_result": task_result.result
        }
    else:
        response = {
            "task_status": task_result.state,
            "task_result": str(task_result.info),
        }
    return JSONResponse(response)


@router.post("send/email")
async def send_email_task(user_decode: HTTPAuthorizationCredentials = Depends(check_auth)):
    task = send_email_task_celery.delay()
    return {"task_id": task.id}

