import requests
import os
from datetime import datetime
from fetch_ipo import get_ipo_schedule

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
        print("텔레그램 월간 요약 전송 성공")
    else:
        print(f"텔레그램 전송 실패: {res.text}")


def build_monthly_message():
    today = datetime.today()
    year = today.year
    month = today.month

    schedule = get_ipo_schedule()

    # 이번 달 데이터만 필터링 (오늘 이후만)
    month_prefix = f"{year}-{month:02d}-"
    today_str = today.strftime("%Y-%m-%d")

    subscribe_list = [
        s for s in schedule
        if s.get("subscribe_start") and s["subscribe_start"].startswith(month_prefix)
        and s["subscribe_start"] >= today_str
    ]
    listing_list = [
        s for s in schedule
        if s.get("listing_date") and s["listing_date"].startswith(month_prefix)
        and s["listing_date"] >= today_str
    ]

    # 날짜순 정렬
    subscribe_list.sort(key=lambda x: x["subscribe_start"])
    listing_list.sort(key=lambda x: x["listing_date"])

    lines = [f"📅 <b>{year}년 {month}월 공모주 일정</b>\n"]

    if subscribe_list:
        lines.append("📋 <b>청약 일정</b>")
        for s in subscribe_list:
            lines.append(
                f"  • {s['name']}\n"
                f"    청약: {s['subscribe_start']} ~ {s['subscribe_end']}\n"
                f"    주관: {s.get('underwriter', '-')}"
            )
    else:
        lines.append("📋 이번 달 청약 일정 없음")

    lines.append("")

    if listing_list:
        lines.append("🚀 <b>상장 일정</b>")
        for s in listing_list:
            lines.append(
                f"  • {s['name']}\n"
                f"    상장일: {s['listing_date']}\n"
                f"    주관: {s.get('underwriter', '-')}"
            )
    else:
        lines.append("🚀 이번 달 상장 일정 없음")

    return "\n".join(lines)


def main():
    message = build_monthly_message()
    send_telegram(message)


if __name__ == "__main__":
    main()
