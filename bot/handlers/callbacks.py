from aiogram import Router
from aiogram.types import CallbackQuery, LabeledPrice, Message

from bot import context as ctx
from bot.config import SUBSCRIBE_DURATION_DAYS
from bot.i18n import get_text
from bot.storage.subscription import (
    add_subscription,
    get_subscription_days_left,
    is_subscribed,
)

router = Router()


@router.callback_query(lambda c: c.data and c.data.startswith("download_"))
async def download_callback_handler(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    try:
        track_id = int(callback.data.split("_")[1])

        priority = 0 if is_subscribed(chat_id) else 1

        try:
            await ctx.bot.delete_message(chat_id, callback.message.message_id)
        except Exception:
            pass

        progress_msg = await ctx.bot.send_message(chat_id, get_text(chat_id, "queued"))

        ctx.download_manager.enqueue(
            chat_id, track_id, progress_msg.message_id, priority
        )

        if priority == 0:
            await callback.answer(get_text(chat_id, "priority_download"))
        else:
            await callback.answer(get_text(chat_id, "download_started"))

    except Exception:
        await callback.answer(get_text(chat_id, "download_error"))


@router.callback_query(lambda c: c.data and c.data.startswith("lang_"))
async def lang_callback_handler(callback: CallbackQuery):
    lang = callback.data.split("_")[1]
    ctx.user_states.setdefault(callback.message.chat.id, {})["lang"] = lang
    await callback.answer()
    await callback.message.delete()


@router.callback_query(lambda c: c.data and c.data.startswith("delete_"))
async def delete_track_handler(callback: CallbackQuery):
    try:
        message_id_to_delete = int(callback.data.split("_")[1])
        await ctx.bot.delete_message(callback.message.chat.id, message_id_to_delete)
        await callback.answer(get_text(callback.message.chat.id, "delete_done"))
    except Exception:
        await callback.answer(get_text(callback.message.chat.id, "delete_error"))


@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query):
    await pre_checkout_query.answer(True)


@router.message(lambda m: getattr(m, "successful_payment", None) is not None)
async def successful_payment_handler(message: Message):
    chat_id = message.chat.id
    if chat_id in ctx.invoices:
        try:
            await ctx.bot.delete_message(chat_id, ctx.invoices[chat_id])
        except Exception:
            pass
        finally:
            ctx.invoices.pop(chat_id, None)

    if (
        message.successful_payment
        and message.successful_payment.invoice_payload == "subscribe_30d"
    ):
        add_subscription(chat_id, days=SUBSCRIBE_DURATION_DAYS)
        days_left = get_subscription_days_left(chat_id)
        await message.answer(get_text(chat_id, "payment_thanks", days=days_left))
    else:
        await message.answer(get_text(chat_id, "payment_unknown"))
