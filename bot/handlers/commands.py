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
from bot.storage.subscription import add_subscription, get_subscription_days_left

router = Router()


@router.message(Command("start"))
async def send_welcome(message: Message):
    await message.answer(
        "Отправьте мне название песни или строчку из неё, и я найду этот трек!\n\n"
        "/subscribe — оформить подписку\n"
        "/status — проверить статус подписки\n\n"
        "Добавьте меня в чат и ищите музыку вместе с друзьями с помощью команды /search _название_",
        parse_mode="Markdown",
    )


@router.message(Command("status"))
async def status_handler(message: Message):
    chat_id = message.chat.id
    days_left = get_subscription_days_left(chat_id)
    text = f"Ваш user_id: {chat_id}\nПодписка: "
    if days_left == -1:
        text += "∞"
    elif days_left > 0:
        text += f"осталось {days_left} дн."
    else:
        text += "отсутствует"
    await message.answer(text)


@router.message(Command("subscribe"))
async def subscribe_handler(message: Message):
    chat_id = message.chat.id
    days_left = get_subscription_days_left(chat_id)
    if days_left > 0:
        await message.answer(
            f"У вас уже есть подписка.\n\nОсталось: {days_left} дней.\n\nПосле оплаты к текущей подписке добавится ещё {SUBSCRIBE_DURATION_DAYS} дней"
        )

    try:
        prices = [LabeledPrice(label="Подписка", amount=SUBSCRIBE_PRICE_STARS)]

        invoice_msg = await ctx.bot.send_invoice(
            chat_id=chat_id,
            title=f"Подписка на {SUBSCRIBE_DURATION_DAYS} дней",
            description=f"Оплата подписки на {SUBSCRIBE_DURATION_DAYS} дней",
            payload="subscribe_30d",
            provider_token="",
            currency="XTR",
            prices=prices,
            start_parameter="subscribe",
        )

        ctx.invoices[chat_id] = invoice_msg.message_id

    except Exception:
        await message.answer(
            "Не удалось создать счёт для оплаты. Пожалуйста, попробуйте позже"
        )


@router.message(Command("addsubscribe"))
async def add_subscribe_handler(message: Message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        await message.answer("<3")
        return

    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Использование: /addsubscribe USER_ID DAYS")
        return

    try:
        target_id = int(parts[1])
        days = int(parts[2])
    except ValueError:
        await message.answer("USER_ID и DAYS должны быть числами.")
        return

    add_subscription(target_id, days)
    display = "∞" if days == -1 else f"{days} дн."
    await message.answer(f"Подписка ({display}) выдана пользователю {target_id}")


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
            await message.answer("Ничего не найдено :(")
            return

        tracks = search_result.tracks.results[:5]
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
                "Выберите трек для загрузки", reply_markup=markup
            )
            ctx.user_states[chat_id] = {"select_msg": select_msg}
        else:
            await message.answer("Найденные треки недоступны для загрузки")

    except Exception:
        await message.answer("Произошла ошибка при поиске. Попробуйте позже")


@router.message(Command("search"))
async def search_command_handler(message: Message):
    query = ""
    if message.text:
        parts = message.text.split(maxsplit=1)
        if len(parts) > 1:
            query = parts[1].strip()

    if not query:
        await message.answer("Использование: /search _название_", parse_mode="Markdown")
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
        await message.answer("Отправьте название трека или используйте /search")
        return

    await _perform_search_and_show(message, query)
