import asyncio
import os

from aiogram import Bot, Dispatcher
from yandex_music import ClientAsync

from bot import context as ctx
from bot.config import BOT_TOKEN, MAX_CONCURRENT_DOWNLOADS, SUBSCRIPTIONS_DB, YM_TOKEN, ADMIN_IDS
from bot.handlers import callbacks, commands
from bot.services.downloader import DownloadManager
from bot.storage.subscription import init_db, add_subscription, get_subscription_days_left


async def main():
    os.makedirs(os.path.dirname(SUBSCRIPTIONS_DB) or ".", exist_ok=True)
    init_db()
    for admin_id in ADMIN_IDS:
        if get_subscription_days_left(admin_id) == 0:
            add_subscription(admin_id, -1)

    bot = Bot(token=BOT_TOKEN)
    ym_client = ClientAsync(YM_TOKEN)
    await ym_client.init()

    me = await bot.get_me()
    download_manager = DownloadManager(bot, ym_client)

    ctx.bot = bot
    ctx.ym_client = ym_client
    ctx.bot_id = me.id
    ctx.download_manager = download_manager

    dp = Dispatcher()
    dp.include_router(commands.router)
    dp.include_router(callbacks.router)

    await download_manager.start_workers(MAX_CONCURRENT_DOWNLOADS)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
