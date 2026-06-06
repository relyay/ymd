from aiogram import Router
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    Message,
)

from bot import context as ctx
from bot.config import ADMIN_IDS, SUBSCRIBE_DURATION_DAYS, SUBSCRIBE_PRICE_STARS
from bot.i18n import get_text
from bot.storage.subscription import add_subscription, get_subscription_days_left

router = Router()


@router.message(Command("start"))
async def send_welcome(message: Message):
    await message.answer(
        get_text(message.chat.id, "welcome"),
        parse_mode="Markdown",
    )


@router.message(Command("status"))
async def status_handler(message: Message):
    chat_id = message.chat.id
    days_left = get_subscription_days_left(chat_id)
    status_text = ""
    if days_left == -1:
        status_text = get_text(chat_id, "subscription_infinite")
    elif days_left > 0:
        status_text = get_text(chat_id, "subscription_days_left", days=days_left)
    else:
        status_text = get_text(chat_id, "subscription_none")
    text = f"{get_text(chat_id, 'your_user_id', user_id=chat_id)}\n{get_text(chat_id, 'subscription_status')}{status_text}"
    await message.answer(text)


@router.message(Command("subscribe"))
async def subscribe_handler(message: Message):
    chat_id = message.chat.id
    days_left = get_subscription_days_left(chat_id)
    if days_left > 0:
        await message.answer(
            get_text(chat_id, "already_subscribed", days=days_left, duration=SUBSCRIBE_DURATION_DAYS)
        )

    try:
        prices = [LabeledPrice(label="Подписка", amount=SUBSCRIBE_PRICE_STARS)]

        invoice_msg = await ctx.bot.send_invoice(
            chat_id=chat_id,
            title=get_text(chat_id, "invoice_title", days=SUBSCRIBE_DURATION_DAYS),
            description=get_text(chat_id, "invoice_description", days=SUBSCRIBE_DURATION_DAYS),
            payload="subscribe_30d",
            provider_token="",
            currency="XTR",
            prices=prices,
            start_parameter="subscribe",
        )

        ctx.invoices[chat_id] = invoice_msg.message_id

    except Exception:
        await message.answer(
            get_text(chat_id, "invoice_failed")
        )


@router.message(Command("lang"))
async def lang_handler(message: Message):
    inline_keyboard = [
        [InlineKeyboardButton(text="English 🇬🇧", callback_data="lang_en")],
        [InlineKeyboardButton(text="Русский 🇷🇺", callback_data="lang_ru")],
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
    await message.answer(get_text(message.chat.id, "choose_language"), reply_markup=markup)


@router.message(Command("addsubscribe"))
async def add_subscribe_handler(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    if user_id not in ADMIN_IDS:
        await message.answer(get_text(chat_id, "admin_love"))
        return

    parts = message.text.split()
    if len(parts) != 3:
        await message.answer(get_text(chat_id, "addsubscribe_usage"))
        return

    try:
        target_id = int(parts[1])
        days = int(parts[2])
    except ValueError:
        await message.answer(get_text(chat_id, "addsubscribe_invalid"))
        return

    add_subscription(target_id, days)
    display = "∞" if days == -1 else get_text(message.chat.id, "subscription_days_left", days=days)
    await message.answer(get_text(chat_id, "addsubscribe_done", display=display, target_id=target_id))


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
            await message.answer(get_text(chat_id, "nothing_found"))
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
                get_text(chat_id, "select_track"), reply_markup=markup
            )
            ctx.user_states[chat_id] = {"select_msg": select_msg}
        else:
            await message.answer(get_text(chat_id, "tracks_unavailable"))

    except Exception:
        await message.answer(get_text(chat_id, "search_error"))


@router.message(Command("search"))
async def search_command_handler(message: Message):
    query = ""
    if message.text:
        parts = message.text.split(maxsplit=1)
        if len(parts) > 1:
            query = parts[1].strip()

    if not query:
        await message.answer(get_text(message.chat.id, "search_usage"), parse_mode="Markdown")
        return

    await _perform_search_and_show(message, query)


@router.message()
async def search_track_handler(message: Message):
    if message.text and message.text.startswith("/"):
        return

    if message.chat.type != "private":
        return

    query = message.text.strip() if message.text else ""
    if not query:
        await message.answer(get_text(message.chat.id, "send_track_name"))
        return

    await _perform_search_and_show(message, query)
