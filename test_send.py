import requests
import os

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

message = (
    "📋 <b>오늘 공모주 청약 시작</b>\n"
    "  • 테스트종목\n"
    "    청약기간: 2026-03-12 ~ 2026-03-13\n"
    "    주관증권사: 미래에셋증권\n"
    "\n"
    "🚀 <b>오늘 공모주 상장</b>\n"
    "  • 테스트종목2\n"
    "    상장일: 2026-03-12\n"
    "    주관증권사: KB증권"
)

res = requests.post(
    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
    json={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"},
)
print(res.json())
