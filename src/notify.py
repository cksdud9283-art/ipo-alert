import requests
import os
from fetch_ipo import get_today_events

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }
    res = requests.post(url, json=payload)
    if res.status_code == 200:
        print("텔레그램 알림 전송 성공")
    else:
        print(f"텔레그램 알림 실패: {res.text}")


def build_message(subscribe_today, listing_today):
    lines = []

    if subscribe_today:
        lines.append("📋 <b>오늘 공모주 청약 시작</b>")
        for s in subscribe_today:
            lines.append(
                f"  • {s['name']}\n"
                f"    청약기간: {s['subscribe_start']} ~ {s['subscribe_end']}"
            )

    if listing_today:
        if lines:
            lines.append("")
        lines.append("🚀 <b>오늘 공모주 상장</b>")
        for s in listing_today:
            lines.append(f"  • {s['name']}  (상장일: {s['listing_date']})")

    if not subscribe_today and not listing_today:
        return None  # 오늘 해당 없으면 알림 안 보냄

    return "\n".join(lines)


def main():
    subscribe_today, listing_today = get_today_events()
    message = build_message(subscribe_today, listing_today)

    if message:
        send_telegram(message)
    else:
        print("오늘 청약/상장 공모주 없음 - 알림 미발송")


if __name__ == "__main__":
    main()
