import json
from datetime import datetime
from typing import Dict, Union

import httpx
from fastapi import BackgroundTasks, FastAPI
from pydantic_settings import BaseSettings
from redis.asyncio import Redis

API_URL = 'https://www.goldapi.io/api/XAU/USD'
API_KEY = "goldapi-bub5hnslxsfbdwf-io"
MINUTES = 60 * 10


class Keys:
    gold_price = "gold:price"


class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379"
    email_sender: str = "viet.info.43@gmail.com"
    email_recipient: str = "buiviet432003@gmail.com"
    smtp_server: str = "viet_2151220253@dau.edu.vn"
    smtp_port: int = 587
    smtp_user: str = "viet.info.43@gmail.com"
    smtp_password: str = "Luckyroo14"


settings = Settings()
app = FastAPI()
redis: Redis = None

    
@app.on_event("startup")
async def startup_event():
    global redis
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    await initialize_redis(Keys())


async def initialize_redis(keys: Keys):
    await redis.set(keys.gold_price, json.dumps({"price": 0, "timestamp": datetime.now().isoformat()}))


async def get_gold_price() -> Dict[str, Union[float, str]]:
    headers = {"x-access-token": API_KEY}
    async with httpx.AsyncClient() as client:
        response = await client.get(API_URL, headers=headers)
        data = response.json()
        return {"price": data["price"], "timestamp": data["timestamp"]}


async def store_gold_price(price: float, timestamp: str):
    await redis.set(Keys.gold_price, json.dumps({"price": price, "timestamp": timestamp}))


async def compare_prices(new_price: float, new_timestamp: str) -> str:
    old_data = await redis.get(Keys.gold_price)
    if old_data:
        old_data = json.loads(old_data)
        old_price = old_data["price"]
        if new_price > old_price:
            return f"{new_price} USD - tăng"
        elif new_price < old_price:
            return f"{new_price} USD - giảm"
        else:
            return f"{new_price} USD - giữ nguyên"
    return f"{new_price} USD - lần đầu"


def send_email(body: str):
    import smtplib
    from email.mime.text import MIMEText

    msg = MIMEText(body)
    msg["Subject"] = "Cập nhật giá vàng"
    msg["From"] = settings.email_sender
    msg["To"] = settings.email_recipient

    with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)


@app.get("/update_gold_price")
async def update_gold_price(background_tasks: BackgroundTasks):
    new_data = await get_gold_price()
    price = new_data["price"]
    timestamp = new_data["timestamp"]
    result = await compare_prices(price, timestamp)
    await store_gold_price(price, timestamp)
    background_tasks.add_task(send_email, result)
    return {"result": result}


@app.on_event("startup")
async def schedule_tasks():
    import asyncio

    async def periodic():
        while True:
            await update_gold_price(BackgroundTasks())
            await asyncio.sleep(MINUTES)

    asyncio.create_task(periodic())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
