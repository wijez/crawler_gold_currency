from fastapi import status, Depends, APIRouter, HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core import get_settings, Config
from app.apis.depends import get_session
from app.apis.depends.check_auth import check_auth
from app.services.gold_service import GoldService
from app.constant import CurrencyCode, MetalSymbol

logger = Config.setup_logging()
settings = get_settings()

router = APIRouter(prefix="/price", tags=["currency"])


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
