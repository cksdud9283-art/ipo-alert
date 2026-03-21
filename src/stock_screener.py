"""
주식 스크리닝 알림
- 코스피 200 대표 종목 + 미국 S&P 500 대표 종목
- 기준: PER 낮음 / ROE 15% 이상 / 부채비율 100% 이하 / 매출 성장 양수
- 매일 실행 후 조건 충족 종목을 텔레그램으로 전송
"""

import os
import requests
import yfinance as yf
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# 코스피 200 대표 종목 (Yahoo Finance 심볼)
KR_STOCKS = [
    ("005930.KS", "삼성전자"),
    ("000660.KS", "SK하이닉스"),
    ("035420.KS", "NAVER"),
    ("005380.KS", "현대차"),
    ("000270.KS", "기아"),
    ("051910.KS", "LG화학"),
    ("006400.KS", "삼성SDI"),
    ("035720.KS", "카카오"),
    ("207940.KS", "삼성바이오로직스"),
    ("068270.KS", "셀트리온"),
    ("028260.KS", "삼성물산"),
    ("012330.KS", "현대모비스"),
    ("096770.KS", "SK이노베이션"),
    ("017670.KS", "SK텔레콤"),
    ("030200.KS", "KT"),
    ("003550.KS", "LG"),
    ("066570.KS", "LG전자"),
    ("009150.KS", "삼성전기"),
    ("034730.KS", "SK"),
    ("032830.KS", "삼성생명"),
    ("105560.KS", "KB금융"),
    ("055550.KS", "신한지주"),
    ("086790.KS", "하나금융지주"),
    ("316140.KS", "우리금융지주"),
    ("003490.KS", "대한항공"),
    ("010950.KS", "S-Oil"),
    ("011200.KS", "HMM"),
    ("000810.KS", "삼성화재"),
    ("024110.KS", "기업은행"),
    ("018260.KS", "삼성에스디에스"),
]

# S&P 500 대표 종목
US_STOCKS = [
    ("AAPL",  "애플"),
    ("MSFT",  "마이크로소프트"),
    ("NVDA",  "엔비디아"),
    ("GOOGL", "알파벳"),
    ("AMZN",  "아마존"),
    ("META",  "메타"),
    ("TSLA",  "테슬라"),
    ("BRK-B", "버크셔해서웨이"),
    ("JPM",   "JP모건"),
    ("JNJ",   "존슨앤존슨"),
    ("V",     "비자"),
    ("PG",    "P&G"),
    ("UNH",   "유나이티드헬스"),
    ("HD",    "홈디포"),
    ("MA",    "마스터카드"),
    ("XOM",   "엑손모빌"),
    ("LLY",   "일라이릴리"),
    ("ABBV",  "애브비"),
    ("MRK",   "머크"),
    ("CVX",   "쉐브론"),
    ("PEP",   "펩시코"),
    ("KO",    "코카콜라"),
    ("COST",  "코스트코"),
    ("WMT",   "월마트"),
    ("BAC",   "뱅크오브아메리카"),
    ("DIS",   "월트디즈니"),
    ("NFLX",  "넷플릭스"),
    ("ADBE",  "어도비"),
    ("CRM",   "세일즈포스"),
    ("INTC",  "인텔"),
]


def fetch_financials(symbol: str) -> dict | None:
    """yfinance로 재무 데이터 조회"""
    try:
        info = yf.Ticker(symbol).info
        return {
            "per": info.get("forwardPE"),           # 배수
            "roe": info.get("returnOnEquity"),       # 소수 (0.18 = 18%)
            "debt_ratio": info.get("debtToEquity"),  # % 단위 (ex. 45.2)
            "revenue_growth": info.get("revenueGrowth"),  # 소수 (0.08 = 8%)
        }
    except Exception as e:
        print(f"{symbol} 재무 조회 실패: {e}")
        return None


def passes_screening(f: dict, sector_avg_per: float | None = None) -> bool:
    """스크리닝 기준 통과 여부"""
    if f is None:
        return False

    per = f.get("per")
    roe = f.get("roe")
    debt = f.get("debt_ratio")
    growth = f.get("revenue_growth")

    # PER: 양수이고 40 이하 (업종 평균 데이터 없을 때 절대 기준 사용)
    per_limit = sector_avg_per if sector_avg_per else 40
    if per is None or per <= 0 or per > per_limit:
        return False

    # ROE: 15% 이상
    if roe is None or roe < 0.15:
        return False

    # 부채비율: 100% 이하 (Yahoo Finance는 % 단위로 반환)
    if debt is None or debt > 100:
        return False

    # 매출 성장률: 양수 (소수 단위 — 데이터 없으면 패스)
    if growth is not None and growth < 0:
        return False

    return True


def format_value(val, multiplier=1, suffix="", fmt=".1f", none_str="-"):
    if val is None:
        return none_str
    return f"{val * multiplier:{fmt}}{suffix}"


def screen_stocks(stock_list: list[tuple]) -> list[dict]:
    """종목 리스트를 스크리닝하고 통과한 종목 반환"""
    passed = []
    for symbol, name in stock_list:
        print(f"  조회 중: {name} ({symbol})")
        f = fetch_financials(symbol)
        if f and passes_screening(f):
            passed.append({
                "symbol": symbol,
                "name": name,
                "per": f["per"],
                "roe": f["roe"],
                "debt_ratio": f["debt_ratio"],
                "revenue_growth": f["revenue_growth"],
            })
    return passed


def build_message(kr_passed: list[dict], us_passed: list[dict]) -> str:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    lines = [f"📊 <b>주식 스크리닝 결과</b>  ({today} 기준)\n"]
    lines.append("<b>스크리닝 기준</b>")
    lines.append("  • PER ≤ 40 (양수)")
    lines.append("  • ROE ≥ 15%")
    lines.append("  • 부채비율 ≤ 100%")
    lines.append("  • 매출 성장률 ≥ 0%\n")

    # 국내 결과
    lines.append(f"🇰🇷 <b>코스피 200 — {len(kr_passed)}종목 통과</b>")
    if kr_passed:
        for s in kr_passed:
            roe_str = format_value(s["roe"], 100, "%")
            per_str = format_value(s["per"], suffix="", fmt=".1f")
            debt_str = format_value(s["debt_ratio"], suffix="%")
            growth_str = format_value(s["revenue_growth"], 100, "%")
            lines.append(
                f"  ✅ <b>{s['name']}</b> ({s['symbol']})\n"
                f"    PER {per_str} | ROE {roe_str} | 부채 {debt_str} | 매출성장 {growth_str}"
            )
    else:
        lines.append("  해당 종목 없음")

    lines.append("")

    # 미국 결과
    lines.append(f"🇺🇸 <b>S&P 500 — {len(us_passed)}종목 통과</b>")
    if us_passed:
        for s in us_passed:
            roe_str = format_value(s["roe"], 100, "%")
            per_str = format_value(s["per"], suffix="", fmt=".1f")
            debt_str = format_value(s["debt_ratio"], suffix="%")
            growth_str = format_value(s["revenue_growth"], 100, "%")
            lines.append(
                f"  ✅ <b>{s['name']}</b> ({s['symbol']})\n"
                f"    PER {per_str} | ROE {roe_str} | 부채 {debt_str} | 매출성장 {growth_str}"
            )
    else:
        lines.append("  해당 종목 없음")

    return "\n".join(lines)


def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    res = requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    })
    if res.status_code == 200:
        print("스크리닝 알림 전송 성공")
    else:
        print(f"전송 실패: {res.text}")


def main():
    print("=== 국내 종목 스크리닝 ===")
    kr_passed = screen_stocks(KR_STOCKS)

    print("\n=== 미국 종목 스크리닝 ===")
    us_passed = screen_stocks(US_STOCKS)

    print(f"\n결과: 국내 {len(kr_passed)}개 / 미국 {len(us_passed)}개 통과")

    message = build_message(kr_passed, us_passed)
    send_telegram(message)


if __name__ == "__main__":
    main()
