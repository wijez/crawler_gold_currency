import json
from datetime import datetime

import redis.asyncio as aioredis
import requests
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.constant import MetalSymbol, CurrencyCode
from app.crud import crud_user
from app.core import get_settings, Config
from app.utils import send_email
from app.utils.format_util import convert_to_yyyymmdd

settings = get_settings()

logger = Config.setup_logging()
r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)


class GoldService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_goldapi_request(self, symbol: MetalSymbol, curr: CurrencyCode, date: str):
        api_key = settings.API_KEY
        date = convert_to_yyyymmdd(date)
        cache_key = f"{symbol.value}-{curr.value}-{date}"

        # Check if data exists in cache
        cached_data = await r.get(cache_key)
        if cached_data:
            logger.info("Retrieving from cache...")
            return json.loads(cached_data)

        url = f"https://www.goldapi.io/api/{symbol.value}/{curr.value}/{date}"
        headers = {
            "x-access-token": api_key,
            "Content-Type": "application/json"
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            result = response.json()
            await r.setex(cache_key, 3600, json.dumps(result))
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching data from Gold API"
            )

    async def get_mail_by_id(self, user_id: int, symbol: MetalSymbol, curr: CurrencyCode, date: str):
        logger.info("Service: get_mail_by_id called")
        user = await crud_user.find_one_by_id(session=self.session, id=user_id)
        if not user:
            logger.error("Service: get_mail_by_id error user id not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User ID not found"
            )
        contents = await self.get_goldapi_request(symbol=symbol, curr=curr, date=date)

        await send_email(to=user.email, subject="Gold Price Data", contents=contents)
        logger.info("Service: get_mail_by_id completed successfully!")
        return contents

    async def get_mail(self, user_id: int):
        logger.info("Service: get_mail called")
        user = await crud_user.find_one_by_id(session=self.session, id=user_id)
        if not user:
            logger.error("Service: get_mail error user id not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User ID not found"
            )

        logger.info("Service: get_mail completed successfully!")
        return user.email

    async def get_goldapi():
        api_key = settings.API_KEY
        date = datetime.now().strftime("%d-%m-%Y")
        date = convert_to_yyyymmdd(date)
        cache_key = f"XAU-USD-{date}"

        cached_data = await r.get(cache_key)
        if cached_data:
            logger.info("Retrieving from cache...")
            return json.loads(cached_data)

        url = f"https://www.goldapi.io/api/XAU/USD/{date}"
        headers = {
            "x-access-token": api_key,
            "Content-Type": "application/json"
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            result = response.json()
            await r.setex(cache_key, 3600, json.dumps(result))
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching data from Gold API"
            )
