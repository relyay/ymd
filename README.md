# Yandex Music Download Bot

Telegram bot for searching and downloading tracks from Yandex Music

### Local run

```bash
cp .env.example .env
# fill BOT_TOKEN and YM_TOKEN
pip install -r requirements.txt
python -m bot
```

### Docker or Podman

```bash
cp .env.example .env
# fill BOT_TOKEN and YM_TOKEN
docker compose up -d --build # or podman compose up -d --build
```
