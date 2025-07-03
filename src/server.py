import asyncio
import logging
import os
from collections.abc import AsyncIterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import AsyncExitStack, asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.requests import Request
from starlette.responses import Response
from telethon import TelegramClient
from telethon.errors.rpcerrorlist import ApiIdInvalidError

from src.api import router
from src.db.db_manager.manager_factory import db_manager
from src.scheduler.notification.http_notification_service import HTTPNotificationService
from src.scheduler.scheduler_service import Scheduler
from src.settings import TGBotSettings, settings

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger(__name__)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> Response:
    logger.exception("Invalid request data: %s", exc)
    return await request_validation_exception_handler(request, exc)


@asynccontextmanager
async def default_lifespan(application: FastAPI) -> AsyncIterator[None]:

    logger.debug("Running application lifespan ...")

    try:
        await db_manager.start()
    except Exception:
        logger.exception("Ошибка при инициализации базы данных: %s")
        raise

    notifier = HTTPNotificationService(settings.bot_api_url)
    scheduler = Scheduler(notification_service=notifier)
    scheduler_task = asyncio.create_task(scheduler.send_digest())

    loop = asyncio.get_event_loop()
    loop.set_default_executor(
        ThreadPoolExecutor(
            max_workers=4,
        ),
    )
    application.settings = TGBotSettings()  # type: ignore[attr-defined,call-arg]

    client = TelegramClient(
        "fastapi_bot_session",
        application.settings.api_id,  # type: ignore[attr-defined]
        application.settings.api_hash,  # type: ignore[attr-defined]
    ).start(
        bot_token=application.settings.token,  # type: ignore[attr-defined]
    )

    async with AsyncExitStack() as stack:
        try:
            application.tg_client = await stack.enter_async_context(await client)  # type: ignore[attr-defined]
        except ApiIdInvalidError:
            logger.info("Working without telegram client inside.")
        yield
        await db_manager.close()
        await stack.aclose()

    await loop.shutdown_default_executor()
    scheduler_task.cancel()


app = FastAPI(
    title="telegram_bot_app",
    lifespan=default_lifespan,
)

app.exception_handler(RequestValidationError)(validation_exception_handler)

app.include_router(router=router, prefix="/api/v1")

app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.info("serving app on port: %d", 7777)
    logger.info("http://0.0.0.0:7777/docs")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=7777,
        log_level=os.getenv("LOGGING_LEVEL", "info").lower(),
    )
