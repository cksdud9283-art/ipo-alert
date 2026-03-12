import requests
import os
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def fetch_quote(symbol: str) -> dict:
    """Yahoo Finance API로 종목/지수 시세 조회"""
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
        return {
            "symbol": symbol,
            "price": price,
            "change": change,
            "change_pct": change_pct,
        }
    except Exception as e:
        print(f"{symbol} 조회 실패: {e}")
        return None


def fetch_us_news(count: int = 3) -> list:
    """Google News RSS에서 미국 주요 뉴스 가져오기"""
    url = "https://news.google.com/rss/search?q=US+economy+stock+market&hl=en-US&gl=US&ceid=US:en"
    headers = {"User-Agent": "Mozilla/5.0"}
    news = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        import xml.etree.ElementTree as ET
        root = ET.fromstring(res.content)
        items = root.findall(".//item")[:count]
        for item in items:
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            # 출처 제거 (제목 끝 " - 매체명" 형식)
            if " - " in title:
                title = title.rsplit(" - ", 1)[0].strip()
            news.append({"title": title, "link": link})
    except Exception as e:
        print(f"뉴스 조회 실패: {e}")
    return news


def arrow(change: float) -> str:
    return "🔺" if change >= 0 else "🔻"


def fmt(change: float, change_pct: float) -> str:
    sign = "+" if change >= 0 else ""
    return f"{sign}{change:.2f} ({sign}{change_pct:.2f}%)"


def build_us_market_message() -> str:
    # 주요 지수
    indices = [
        ("^GSPC",  "S&P 500"),
        ("^IXIC",  "나스닥"),
        ("^DJI",   "다우존스"),
        ("^VIX",   "VIX 공포지수"),
    ]
    # 주요 종목
    stocks = [
        ("AAPL",  "애플"),
        ("MSFT",  "마이크로소프트"),
        ("NVDA",  "엔비디아"),
        ("TSLA",  "테슬라"),
        ("AMZN",  "아마존"),
    ]
    # 환율/원자재/가상자산
    others = [
        ("KRW=X",  "달러/원",   "₩"),
        ("JPY=X",  "달러/엔",   "¥"),
        ("EURUSD=X","유로/달러", "$"),
        ("GC=F",   "금 선물",   "$"),
        ("CL=F",   "WTI 원유",  "$"),
        ("BTC-USD","비트코인",  "$"),
    ]

    now = datetime.utcnow()
    lines = [f"🌏 <b>미국 증시 마감 요약</b>  ({now.strftime('%Y-%m-%d')} 기준)\n"]

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
                f"  {arrow(q['change'])} {name} ({symbol})\n"
                f"    ${q['price']:,.2f}  {fmt(q['change'], q['change_pct'])}"
            )

    lines.append("")
    lines.append("💱 <b>환율 / 원자재 / 가상자산</b>")
    for symbol, name, prefix in others:
        q = fetch_quote(symbol)
        if q:
            lines.append(
                f"  {arrow(q['change'])} {name}\n"
                f"    {prefix}{q['price']:,.2f}  {fmt(q['change'], q['change_pct'])}"
            )

    lines.append("")
    lines.append("📰 <b>미국 주요 뉴스</b>")
    news_list = fetch_us_news(3)
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
        print("미국 증시 알림 전송 성공")
    else:
        print(f"전송 실패: {res.text}")


def main():
    message = build_us_market_message()
    send_telegram(message)


if __name__ == "__main__":
    main()
