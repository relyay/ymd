from typing import Any, Optional
from aiogram import Bot
from yandex_music import ClientAsync
from bot.services.downloader import DownloadManager

bot: Optional[Bot] = None
ym_client: Optional[ClientAsync] = None
download_manager: Optional[DownloadManager] = None
bot_id: int = 0
user_states: dict[int, dict[str, Any]] = {}
invoices: dict[int, int] = {}
