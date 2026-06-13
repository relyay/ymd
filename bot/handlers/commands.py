from aiogram import Router
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultAudio,
    LabeledPrice,
    Message,
)

from bot import context as ctx
from bot.config import ADMIN_IDS, SUBSCRIBE_DURATION_DAYS, SUBSCRIBE_PRICE_STARS
from bot.i18n import _
from bot.storage.users import (
    add_subscription,
    ban_user,
    get_subscription_days_left,
    is_banned,
    register_user,
    remove_subscription,
    set_user_lang,
)

router = Router()


@router.message.middleware()
async def banned_check_middleware(handler, event: Message, data):
    user_id = event.from_user.id
    if user_id not in ADMIN_IDS and is_banned(user_id):
        await event.answer(_(event.chat.id, "banned_message"))
        return
    return await handler(event, data)


@router.message(Command("start"))
async def send_welcome(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    register_user(user_id)

    code = message.from_user.language_code
    if code and code.startswith("en"):
        detected = "en"
    else:
        detected = "ru"
    set_user_lang(user_id, detected)
    ctx.user_states.setdefault(chat_id, {})["lang"] = detected

    await message.answer(
        _(chat_id, "welcome"),
        parse_mode="Markdown",
    )


@router.message(Command("status"))
async def status_handler(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    parts = message.text.split()

    if len(parts) == 2 and user_id in ADMIN_IDS:
        try:
            target_id = int(parts[1])
        except ValueError:
            await message.answer(_(chat_id, "addsub_invalid"))
            return

        if is_banned(target_id):
            text = f"{_(chat_id, 'status_user_header', target_id=target_id)}\n{_(chat_id, 'subscription_status')}{_(chat_id, 'status_banned')}"
        else:
            days_left = get_subscription_days_left(target_id)
            if days_left == -1:
                status_text = _(chat_id, "subscription_infinite")
            elif days_left > 0:
                status_text = _(chat_id, "subscription_days_left", days=days_left)
            else:
                status_text = _(chat_id, "subscription_none")
            text = f"{_(chat_id, 'status_user_header', target_id=target_id)}\n{_(chat_id, 'subscription_status')}{status_text}"
        await message.answer(text)
        return

    days_left = get_subscription_days_left(chat_id)
    status_text = ""
    if days_left == -1:
        status_text = _(chat_id, "subscription_infinite")
    elif days_left > 0:
        status_text = _(chat_id, "subscription_days_left", days=days_left)
    else:
        status_text = _(chat_id, "subscription_none")
    text = f"{_(chat_id, 'your_user_id', user_id=chat_id)}\n{_(chat_id, 'subscription_status')}{status_text}"
    await message.answer(text)


@router.message(Command("subscribe"))
async def subscribe_handler(message: Message):
    chat_id = message.chat.id
    days_left = get_subscription_days_left(chat_id)
    if days_left > 0:
        await message.answer(
            _(
                chat_id,
                "already_subscribed",
                days=days_left,
                duration=SUBSCRIBE_DURATION_DAYS,
            )
        )

    try:
        prices = [LabeledPrice(label="Подписка", amount=SUBSCRIBE_PRICE_STARS)]

        invoice_msg = await ctx.bot.send_invoice(
            chat_id=chat_id,
            title=_(chat_id, "invoice_title", days=SUBSCRIBE_DURATION_DAYS),
            description=_(
                chat_id, "invoice_description", days=SUBSCRIBE_DURATION_DAYS
            ),
            payload="subscribe_30d",
            provider_token="",
            currency="XTR",
            prices=prices,
            start_parameter="subscribe",
        )

        ctx.invoices[chat_id] = invoice_msg.message_id

    except Exception:
        await message.answer(_(chat_id, "invoice_failed"))


@router.message(Command("lang"))
async def lang_handler(message: Message):
    inline_keyboard = [
        [InlineKeyboardButton(text="English", callback_data="lang_en")],
        [InlineKeyboardButton(text="Русский", callback_data="lang_ru")],
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
    await message.answer(
        _(message.chat.id, "choose_language"), reply_markup=markup
    )


@router.message(Command("addsub"))
async def add_sub_handler(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    if user_id not in ADMIN_IDS:
        await message.answer(_(chat_id, "admin_love"))
        return

    parts = message.text.split()
    if len(parts) != 3:
        await message.answer(_(chat_id, "addsub_usage"))
        return

    try:
        target_id = int(parts[1])
        days = int(parts[2])
    except ValueError:
        await message.answer(_(chat_id, "addsub_invalid"))
        return

    add_subscription(target_id, days)
    display = (
        "∞"
        if days == -1
        else _(message.chat.id, "subscription_days_left", days=days)
    )
    await message.answer(
        _(chat_id, "addsub_done", display=display, target_id=target_id)
    )


@router.message(Command("delsub"))
async def del_sub_handler(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    if user_id not in ADMIN_IDS:
        await message.answer(_(chat_id, "admin_love"))
        return

    parts = message.text.split()
    if len(parts) != 2:
        await message.answer(_(chat_id, "delsub_usage"))
        return

    try:
        target_id = int(parts[1])
    except ValueError:
        await message.answer(_(chat_id, "delsub_invalid"))
        return

    remove_subscription(target_id)
    await message.answer(
        _(chat_id, "delsub_done", target_id=target_id)
    )


@router.message(Command("ban"))
async def ban_handler(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    if user_id not in ADMIN_IDS:
        await message.answer(_(chat_id, "admin_love"))
        return

    parts = message.text.split()
    if len(parts) != 2:
        await message.answer(_(chat_id, "ban_usage"))
        return

    try:
        target_id = int(parts[1])
    except ValueError:
        await message.answer(_(chat_id, "ban_invalid"))
        return

    if target_id == user_id:
        await message.answer(_(chat_id, "ban_self"))
        return

    ban_user(target_id)
    await message.answer(
        _(chat_id, "ban_done", target_id=target_id)
    )


async def _perform_search_and_show(message: Message, query: str):
    chat_id = message.chat.id

    try:
        if chat_id in ctx.user_states and "select_msg" in ctx.user_states[chat_id]:
            try:
                await ctx.bot.delete_message(
                    chat_id, ctx.user_states[chat_id]["select_msg"].message_id
                )
            except Exception:
                pass

        search_result = await ctx.ym_client.search(query, type_="track")

        if not getattr(search_result, "tracks", None) or not getattr(
            search_result.tracks, "results", None
        ):
            await message.answer(_(chat_id, "nothing_found"))
            return

        tracks = search_result.tracks.results[:6]
        inline_keyboard = []
        for track in tracks:
            if not getattr(track, "available", True):
                continue
            title = (
                f"{track.title} - {', '.join(artist.name for artist in track.artists)}"
            )
            callback_data = f"download_{track.id}"
            inline_keyboard.append(
                [InlineKeyboardButton(text=title, callback_data=callback_data)]
            )

        if inline_keyboard:
            markup = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
            select_msg = await message.answer(
                _(chat_id, "select_track"), reply_markup=markup
            )
            ctx.user_states.setdefault(chat_id, {})["select_msg"] = select_msg
        else:
            await message.answer(_(chat_id, "tracks_unavailable"))

    except Exception:
        await message.answer(_(chat_id, "search_error"))


@router.message(Command("search"))
async def search_command_handler(message: Message):
    query = ""
    if message.text:
        parts = message.text.split(maxsplit=1)
        if len(parts) > 1:
            query = parts[1].strip()

    if not query:
        await message.answer(
            _(message.chat.id, "search_usage"), parse_mode="Markdown"
        )
        return

    await _perform_search_and_show(message, query)


@router.inline_query()
async def inline_search(inline_query: InlineQuery):
    query = inline_query.query.strip()
    if not query:
        return

    search_result = await ctx.ym_client.search(query, type_="track")

    if not getattr(search_result, "tracks", None) or not getattr(
        search_result.tracks, "results", None
    ):
        return

    raw_tracks = [
        t for t in search_result.tracks.results[:15] if getattr(t, "available", True)
    ]

    async def _resolve(track):
        try:
            info = (await ctx.ym_client.tracks(track.id))[0]
            artists = ", ".join(a.name for a in info.artists)
            di = await info.get_download_info_async(get_direct_links=True)
            mp3 = sorted(
                [d for d in di if d.codec == "mp3" and d.direct_link],
                key=lambda x: x.bitrate_in_kbps,
                reverse=True,
            )
            if not mp3:
                return None
            return InlineQueryResultAudio(
                id=str(track.id),
                audio_url=mp3[0].direct_link,
                title=info.title,
                performer=artists,
                audio_duration=info.duration_ms // 1000 if info.duration_ms else 0,
            )
        except Exception:
            return None

    import asyncio

    resolved = await asyncio.gather(*[_resolve(t) for t in raw_tracks])
    results = [r for r in resolved if r is not None]

    if results:
        await inline_query.answer(results, cache_time=300, is_personal=True)


@router.message()
async def search_track_handler(message: Message):
    if message.text and message.text.startswith("/"):
        return

    if message.chat.type != "private":
        return

    query = message.text.strip() if message.text else ""
    if not query:
        await message.answer(_(message.chat.id, "send_track_name"))
        return

    await _perform_search_and_show(message, query)
