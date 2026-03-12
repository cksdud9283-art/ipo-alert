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
    # 환율/원자재
    others = [
        ("KRW=X",  "달러/원 환율"),
        ("GC=F",   "금 선물"),
        ("CL=F",   "WTI 원유"),
        ("BTC-USD", "비트코인"),
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
    for symbol, name in others:
        q = fetch_quote(symbol)
        if q:
            prefix = "$" if symbol != "KRW=X" else "₩"
            lines.append(
                f"  {arrow(q['change'])} {name}\n"
                f"    {prefix}{q['price']:,.2f}  {fmt(q['change'], q['change_pct'])}"
            )

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
