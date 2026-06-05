# Yandex Music Download Bot

Telegram bot for searching and downloading tracks from Yandex Music
https://YandexUBot.t.me

### Local run

```bash
cp .env.example .env
# fill BOT_TOKEN, YM_TOKEN, and other variables
pip install -r requirements.txt
python -m bot
```

### Docker or Podman

```bash
cp .env.example .env
# fill BOT_TOKEN, YM_TOKEN, and other variables
docker compose up -d --build # or podman compose up -d --build
```
