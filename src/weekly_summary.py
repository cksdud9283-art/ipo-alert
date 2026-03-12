import requests
import os
from datetime import datetime, timedelta
from fetch_ipo import get_ipo_schedule

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def fetch_us_economic_calendar() -> list:
    """이번 주 미국 주요 경제지표 일정 (고정 키워드 기반 Google News)"""
    keywords = ["CPI", "FOMC", "GDP", "NFP", "Payrolls", "PPI", "retail sales"]
    url = f"https://news.google.com/rss/search?q={'|'.join(keywords)}+this+week+economic+calendar&hl=en-US&gl=US&ceid=US:en"
    headers = {"User-Agent": "Mozilla/5.0"}
    news = []
    try:
        import xml.etree.ElementTree as ET
        res = requests.get(url, headers=headers, timeout=10)
        root = ET.fromstring(res.content)
        items = root.findall(".//item")[:3]
        for item in items:
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            if " - " in title:
                title = title.rsplit(" - ", 1)[0].strip()
            news.append({"title": title, "link": link})
    except Exception as e:
        print(f"경제지표 뉴스 조회 실패: {e}")
    return news


def get_week_ipo_schedule() -> tuple:
    """이번 주 공모주 청약/상장 일정"""
    today = datetime.today()
    # 이번 주 월~금
    monday = today - timedelta(days=today.weekday())
    week_dates = [(monday + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(5)]

    schedule = get_ipo_schedule()
    subscribe_week = [s for s in schedule if s.get("subscribe_start") in week_dates]
    listing_week = [s for s in schedule if s.get("listing_date") in week_dates]

    subscribe_week.sort(key=lambda x: x["subscribe_start"])
    listing_week.sort(key=lambda x: x["listing_date"])
    return subscribe_week, listing_week


def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    res = requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    })
    if res.status_code == 200:
        print("주간 요약 알림 전송 성공")
    else:
        print(f"전송 실패: {res.text}")


def build_weekly_message() -> str:
    today = datetime.today()
    monday = today - timedelta(days=today.weekday())
    friday = monday + timedelta(days=4)

    lines = [
        f"📅 <b>이번 주 투자 일정 요약</b>\n"
        f"({monday.strftime('%m/%d')} ~ {friday.strftime('%m/%d')})\n"
    ]

    # 공모주 일정
    subscribe_week, listing_week = get_week_ipo_schedule()

    if subscribe_week:
        lines.append("📋 <b>이번 주 공모주 청약</b>")
        for s in subscribe_week:
            lines.append(
                f"  • {s['name']}\n"
                f"    청약: {s['subscribe_start']} ~ {s['subscribe_end']}\n"
                f"    주관: {s.get('underwriter', '-')}"
            )
    else:
        lines.append("📋 이번 주 공모주 청약 없음")

    lines.append("")

    if listing_week:
        lines.append("🚀 <b>이번 주 공모주 상장</b>")
        for s in listing_week:
            lines.append(
                f"  • {s['name']}\n"
                f"    상장일: {s['listing_date']}\n"
                f"    주관: {s.get('underwriter', '-')}"
            )
    else:
        lines.append("🚀 이번 주 공모주 상장 없음")

    lines.append("")

    # 미국 경제지표 일정
    lines.append("🏦 <b>이번 주 미국 경제지표 관련 뉴스</b>")
    news = fetch_us_economic_calendar()
    if news:
        for i, n in enumerate(news, 1):
            lines.append(f"  {i}. <a href=\"{n['link']}\">{n['title']}</a>")
    else:
        lines.append("  일정 정보를 불러오지 못했습니다.")

    return "\n".join(lines)


def main():
    message = build_weekly_message()
    send_telegram(message)


if __name__ == "__main__":
    main()
