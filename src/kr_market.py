import requests
import os
from datetime import datetime
from bs4 import BeautifulSoup

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def fetch_quote(symbol: str) -> dict:
    """Yahoo Finance API로 지수 시세 조회"""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()
        meta = data["chart"]["result"][0]["meta"]
        price = meta.get("regularMarketPrice", 0)
        prev_close = meta.get("chartPreviousClose") or meta.get("previousClose", 0)
        change = price - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0
        return {"price": price, "change": change, "change_pct": change_pct}
    except Exception as e:
        print(f"{symbol} 조회 실패: {e}")
        return None


def fetch_kr_news(count: int = 3) -> list:
    """Google News RSS에서 국내 증시 관련 뉴스"""
    url = "https://news.google.com/rss/search?q=%EC%BD%94%EC%8A%A4%ED%94%BC+%EC%BD%94%EC%8A%A4%EB%8B%A5+%EC%A6%9D%EC%8B%9C&hl=ko&gl=KR&ceid=KR:ko"
    headers = {"User-Agent": "Mozilla/5.0"}
    news = []
    try:
        import xml.etree.ElementTree as ET
        res = requests.get(url, headers=headers, timeout=10)
        root = ET.fromstring(res.content)
        items = root.findall(".//item")[:count]
        for item in items:
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            if " - " in title:
                title = title.rsplit(" - ", 1)[0].strip()
            news.append({"title": title, "link": link})
    except Exception as e:
        print(f"뉴스 조회 실패: {e}")
    return news


def arrow(change: float) -> str:
    return "🔴▲" if change >= 0 else "🔵▼"


def fmt(change: float, change_pct: float) -> str:
    sign = "+" if change >= 0 else ""
    return f"{sign}{change:.2f} ({sign}{change_pct:.2f}%)"


def build_kr_market_message() -> str:
    indices = [
        ("^KS11", "코스피"),
        ("^KQ11", "코스닥"),
        ("^KS200", "코스피 200"),
    ]
    # 국내 주요 종목
    stocks = [
        ("005930.KS", "삼성전자"),
        ("000660.KS", "SK하이닉스"),
        ("035420.KS", "NAVER"),
        ("005380.KS", "현대차"),
        ("051910.KS", "LG화학"),
    ]

    now_kst = datetime.utcnow()
    lines = [f"🇰🇷 <b>국내 증시 마감 요약</b>  ({now_kst.strftime('%Y-%m-%d')} 기준)\n"]

    lines.append("📊 <b>주요 지수</b>")
    for symbol, name in indices:
        q = fetch_quote(symbol)
        if q:
            lines.append(
                f"  {arrow(q['change'])} {name}\n"
                f"    {q['price']:,.2f}  {fmt(q['change'], q['change_pct'])}"
            )

    lines.append("")
    lines.append("💹 <b>주요 종목</b>")
    for symbol, name in stocks:
        q = fetch_quote(symbol)
        if q:
            lines.append(
                f"  {arrow(q['change'])} {name}\n"
                f"    ₩{q['price']:,.0f}  {fmt(q['change'], q['change_pct'])}"
            )

    lines.append("")
    lines.append("📰 <b>국내 증시 주요 뉴스</b>")
    news_list = fetch_kr_news(3)
    if news_list:
        for i, n in enumerate(news_list, 1):
            lines.append(f"  {i}. <a href=\"{n['link']}\">{n['title']}</a>")
    else:
        lines.append("  뉴스를 불러오지 못했습니다.")

    return "\n".join(lines)


def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    res = requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    })
    if res.status_code == 200:
        print("국내 증시 알림 전송 성공")
    else:
        print(f"전송 실패: {res.text}")


def main():
    message = build_kr_market_message()
    send_telegram(message)


if __name__ == "__main__":
    main()
