import os
import sys

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
YM_TOKEN = os.getenv("YM_TOKEN", "")

if not BOT_TOKEN:
    sys.exit("BOT_TOKEN is required")
if not YM_TOKEN:
    sys.exit("YM_TOKEN is required")

SUBSCRIPTIONS_DB = os.getenv("SUBSCRIPTIONS_DB", "data/subscriptions.db")
SUBSCRIBE_PRICE_STARS = 50
SUBSCRIBE_DURATION_DAYS = 30
MAX_CONCURRENT_DOWNLOADS = 10
ADMIN_IDS = [7459991544]
