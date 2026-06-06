import asyncio
import io
import os
import tempfile
import time

import aiohttp
from aiogram import Bot
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup
from yandex_music import ClientAsync

from bot.i18n import get_text
from bot.services.tags import add_tags_to_audio, save_jpeg_thumb


class DownloadManager:
    def __init__(self, bot: Bot, ym_client: ClientAsync):
        self.bot = bot
        self.ym_client = ym_client
        self.queue: asyncio.PriorityQueue = asyncio.PriorityQueue()

    async def start_workers(self, count: int = 10):
        for _ in range(count):
            asyncio.create_task(self._worker())

    async def _worker(self):
        while True:
            priority, task = await self.queue.get()
            try:
                await self._download_and_send_track(*task)
            except Exception:
                pass
            finally:
                self.queue.task_done()

    def enqueue(
        self, chat_id: int, track_id: int, progress_msg_id: int, priority: int = 1
    ):
        self.queue.put_nowait((priority, (chat_id, track_id, progress_msg_id)))

    async def _edit_progress_message(
        self, chat_id: int, message_id: int, text: str
    ) -> None:
        try:
            await self.bot.edit_message_text(
                chat_id=chat_id, message_id=message_id, text=text
            )
        except Exception:
            pass

    async def _add_action_buttons(
        self, chat_id: int, message_id: int, title: str
    ) -> None:
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=get_text(chat_id, "delete"), callback_data=f"delete_{message_id}"
                    )
                ]
            ]
        )
        try:
            await self.bot.edit_message_reply_markup(
                chat_id=chat_id, message_id=message_id, reply_markup=markup
            )
        except Exception:
            pass

    async def _download_file(
        self, url: str, filename: str, chat_id: int, progress_msg_id: int
    ) -> None:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    resp.raise_for_status()
                    total_size = int(resp.headers.get("Content-Length", 0) or 0)
                    downloaded = 0
                    start_time = time.time()
                    last_update = 0.0
                    with open(filename, "wb") as f:
                        async for chunk in resp.content.iter_chunked(8192):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                current_time = time.time()

                                if total_size > 0 and (
                                    current_time - last_update >= 1
                                    or downloaded == total_size
                                ):
                                    last_update = current_time
                                    progress = (
                                        int(downloaded / total_size * 100)
                                        if total_size > 0
                                        else 0
                                    )
                                    elapsed = current_time - start_time
                                    speed = (
                                        (downloaded / (1024 * 1024)) / elapsed
                                        if elapsed > 0
                                        else 0
                                    )
                                    progress_text = get_text(
                                        chat_id, "downloading_progress",
                                        progress=progress,
                                        downloaded=downloaded / (1024 * 1024),
                                        total=(total_size / (1024 * 1024)) if total_size > 0 else 0,
                                        speed=speed,
                                    )
                                    await self._edit_progress_message(
                                        chat_id, progress_msg_id, progress_text
                                    )
        except Exception:
            await self._edit_progress_message(
                chat_id, progress_msg_id, get_text(chat_id, "download_error")
            )

    async def _download_and_send_track(
        self, chat_id: int, track_id: int, progress_msg_id: int
    ) -> None:
        temp_file = None
        temp_thumb = None
        try:
            track_info = (await self.ym_client.tracks(track_id))[0]
            artists = ", ".join(artist.name for artist in track_info.artists)
            title = track_info.title

            await self._edit_progress_message(
                chat_id, progress_msg_id, get_text(chat_id, "downloading_info")
            )

            cover_url = f"https://{track_info.cover_uri.replace('%%', '400x400')}"

            async with aiohttp.ClientSession() as session:
                async with session.get(cover_url) as resp:
                    resp.raise_for_status()
                    cover_data = await resp.read()

            try:
                temp_thumb = save_jpeg_thumb(cover_data)
            except Exception:
                temp_thumb = None

            if hasattr(track_info, "get_download_info_async"):
                download_info = await track_info.get_download_info_async(
                    get_direct_links=True
                )
            else:
                download_info = await asyncio.to_thread(
                    lambda: track_info.get_download_info(get_direct_links=True)
                )

            if not download_info:
                return
            mp3_infos = [
                di for di in download_info if di.codec == "mp3" and di.direct_link
            ]
            if not mp3_infos:
                await self._edit_progress_message(
                    chat_id,
                    progress_msg_id,
                    get_text(chat_id, "mp3_unavailable"),
                )
                return

            mp3_infos.sort(key=lambda x: x.bitrate_in_kbps, reverse=True)
            direct_link = mp3_infos[0].direct_link

            fd, temp_path = tempfile.mkstemp(suffix=".mp3", prefix=f"ym_{chat_id}_")
            os.close(fd)
            temp_file = temp_path

            await self._download_file(direct_link, temp_path, chat_id, progress_msg_id)

            file_size = os.path.getsize(temp_path)
            if file_size > 50 * 1024 * 1024:
                await self._edit_progress_message(
                    chat_id,
                    progress_msg_id,
                    get_text(chat_id, "file_too_large"),
                )
                return

            await add_tags_to_audio(temp_path, title, artists, cover_data)

            await self._edit_progress_message(
                chat_id, progress_msg_id, get_text(chat_id, "sending_track")
            )

            try:
                if temp_thumb:
                    sent_audio = await self.bot.send_audio(
                        chat_id=chat_id,
                        audio=FSInputFile(temp_path),
                        title=title,
                        performer=artists,
                        thumbnail=FSInputFile(temp_thumb),
                    )
                else:
                    sent_audio = await self.bot.send_audio(
                        chat_id=chat_id,
                        audio=FSInputFile(temp_path),
                        title=title,
                        performer=artists,
                    )

                await self._add_action_buttons(chat_id, sent_audio.message_id, title)
            except Exception:
                await self._edit_progress_message(
                    chat_id, progress_msg_id, get_text(chat_id, "send_error")
                )
                return

            try:
                await self.bot.delete_message(chat_id, progress_msg_id)
            except Exception:
                pass

        except Exception:
            await self._edit_progress_message(chat_id, progress_msg_id, get_text(chat_id, "general_error"))
        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass
            if temp_thumb and os.path.exists(temp_thumb):
                try:
                    os.remove(temp_thumb)
                except Exception:
                    pass
