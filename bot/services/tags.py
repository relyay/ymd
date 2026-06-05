import io
import os
import re
import tempfile
import asyncio

from mutagen.id3 import ID3, TPE1, TIT2, APIC
from PIL import Image


def sanitize_filename(filename: str) -> str:
    return re.sub(r'[\/*?:"<>|]', "", filename)


def save_jpeg_thumb(cover_data: bytes) -> str:
    fd, path = tempfile.mkstemp(suffix=".jpg", prefix="thumb_")
    os.close(fd)
    try:
        img = Image.open(io.BytesIO(cover_data))
        img = img.convert("RGB")
        img.thumbnail((320, 320), Image.LANCZOS)

        for quality in (95, 85, 75, 65, 50):
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=quality, optimize=True)
            size = buf.tell()
            if size <= 200 * 1024 or quality == 50:
                with open(path, "wb") as f:
                    f.write(buf.getvalue())
                return path
    except Exception:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
        raise


def add_tags_to_audio_blocking(filename: str, title: str, artists: str, cover_data: bytes) -> None:
    audio = ID3()
    audio.add(TPE1(encoding=3, text=artists))
    audio.add(TIT2(encoding=3, text=title))
    audio.add(APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=cover_data))
    audio.save(filename)


async def add_tags_to_audio(filename: str, title: str, artists: str, cover_data: bytes) -> None:
    await asyncio.to_thread(add_tags_to_audio_blocking, filename, title, artists, cover_data)
