from bot import context as ctx

TRANSLATIONS = {
    "ru": {
        "welcome": (
            "Отправьте мне название песни или строчку из неё, и я найду этот трек!\n\n"
            "/subscribe — оформить подписку\n"
            "/status — проверить статус подписки\n\n"
            "Добавьте меня в чат и ищите музыку вместе с друзьями с помощью команды /search _название_"
        ),
        "your_user_id": "Ваш user_id: {user_id}",
        "subscription_status": "Подписка: ",
        "subscription_infinite": "∞",
        "subscription_days_left": "осталось {days} дн.",
        "subscription_none": "отсутствует",
        "already_subscribed": "У вас уже есть подписка.\n\nОсталось: {days} дней.\n\nПосле оплаты к текущей подписке добавится ещё {duration} дней",
        "invoice_title": "Подписка на {days} дней",
        "invoice_description": "Оплата подписки на {days} дней",
        "invoice_failed": "Не удалось создать счёт для оплаты. Пожалуйста, попробуйте позже",
        "admin_love": "<3",
        "addsubscribe_usage": "Использование: /addsubscribe USER_ID DAYS",
        "addsubscribe_invalid": "USER_ID и DAYS должны быть числами.",
        "addsubscribe_done": "Подписка ({display}) выдана пользователю {target_id}",
        "nothing_found": "Ничего не найдено :(",
        "select_track": "Выберите трек для загрузки",
        "tracks_unavailable": "Найденные треки недоступны для загрузки",
        "search_error": "Произошла ошибка при поиске. Попробуйте позже",
        "search_usage": "Использование: /search _название_",
        "send_track_name": "Отправьте название трека или используйте /search",
        "queued": "Ваш запрос добавлен в очередь...",
        "priority_download": "Приоритетная загрузка началась",
        "download_started": "Загрузка началась",
        "downloading_info": "Получение информации о треке...",
        "downloading_progress": "Загрузка {progress}%\nСкачано: {downloaded:.2f}MB / {total:.2f}MB\nСкорость: {speed:.2f} MB/s",
        "download_error": "Ошибка при загрузке файла",
        "mp3_unavailable": "MP3 формат недоступен для этого трека. Попробуйте другой трек",
        "file_too_large": "Файл слишком большой для отправки как аудио (>50MB)",
        "sending_track": "Отправка трека...",
        "send_error": "Ошибка при отправке трека",
        "general_error": "Общая ошибка",
        "payment_thanks": "Спасибо за оплату! Ваша подписка оформлена.\n\nОсталось {days} дней",
        "payment_unknown": "Оплата прошла, но не удалось активировать подписку из-за технической ошибки. Пожалуйста, обратитесь в поддержку",
        "delete": "Удалить",
        "delete_done": "Трек удалён",
        "delete_error": "Не удалось удалить трек (возможно, он уже удалён)",
        "choose_language": "Choose language / Выберите язык:",
    },
    "en": {
        "welcome": (
            "Send me a song name or a lyric line, and I'll find that track!\n\n"
            "/subscribe — get a subscription\n"
            "/status — check subscription status\n\n"
            "Add me to a chat and search music together with friends using /search _name_"
        ),
        "your_user_id": "Your user_id: {user_id}",
        "subscription_status": "Subscription: ",
        "subscription_infinite": "∞",
        "subscription_days_left": "{days} days left",
        "subscription_none": "none",
        "already_subscribed": "You already have a subscription.\n\nDays left: {days}.\n\nAfter payment, {duration} more days will be added to your current subscription",
        "invoice_title": "Subscription for {days} days",
        "invoice_description": "Payment for {days} day subscription",
        "invoice_failed": "Failed to create an invoice. Please try again later",
        "admin_love": "<3",
        "addsubscribe_usage": "Usage: /addsubscribe USER_ID DAYS",
        "addsubscribe_invalid": "USER_ID and DAYS must be numbers.",
        "addsubscribe_done": "Subscription ({display}) granted to user {target_id}",
        "nothing_found": "Nothing found :(",
        "select_track": "Select a track to download",
        "tracks_unavailable": "Found tracks are not available for download",
        "search_error": "An error occurred while searching. Please try again later",
        "search_usage": "Usage: /search _name_",
        "send_track_name": "Send a track name or use /search",
        "queued": "Your request has been queued...",
        "priority_download": "Priority download started",
        "download_started": "Download started",
        "downloading_info": "Getting track info...",
        "downloading_progress": "Downloading {progress}%\nDownloaded: {downloaded:.2f}MB / {total:.2f}MB\nSpeed: {speed:.2f} MB/s",
        "download_error": "Error downloading file",
        "mp3_unavailable": "MP3 format is not available for this track. Try another track",
        "file_too_large": "File is too large to send as audio (>50MB)",
        "sending_track": "Sending track...",
        "send_error": "Error sending track",
        "general_error": "General error",
        "payment_thanks": "Thank you for your payment! Your subscription is active.\n\n{days} days left",
        "payment_unknown": "Payment was successful, but the subscription could not be activated due to a technical error. Please contact support",
        "delete": "Delete",
        "delete_done": "Track deleted",
        "delete_error": "Could not delete track (maybe it's already deleted)",
        "choose_language": "Choose language / Выберите язык:",
    },
}


def get_text(chat_id: int, key: str, **kwargs) -> str:
    lang = ctx.user_states.get(chat_id, {}).get("lang", "ru")
    text = TRANSLATIONS.get(lang, TRANSLATIONS["ru"]).get(key, key)
    return text.format(**kwargs) if kwargs else text
