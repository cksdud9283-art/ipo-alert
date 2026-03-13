import requests
import os
import ssl
import urllib3
from datetime import datetime
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class LegacySSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.set_ciphers("DEFAULT:@SECLEVEL=1")
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        kwargs["ssl_context"] = ctx
        super().init_poolmanager(*args, **kwargs)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def fetch_competition_rate() -> list:
    """38커뮤니케이션에서 청약 마감일 경쟁률 스크래핑"""
    today = datetime.today().strftime("%Y-%m-%d")
    url = "https://www.38.co.kr/html/fund/index.htm?o=k"
    headers = {"User-Agent": "Mozilla/5.0"}
    results = []

    try:
        session = requests.Session()
        session.mount("https://", LegacySSLAdapter())
        res = session.get(url, headers=headers, timeout=10)
        res.encoding = "euc-kr"
        soup = BeautifulSoup(res.text, "html.parser")

        tables = soup.find_all("table")
        if len(tables) <= 25:
            print(f"테이블 수 부족: {len(tables)}")
            return results

        rows = tables[25].find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 5:
                continue

            name = cols[0].get_text(strip=True)
            period = cols[1].get_text(strip=True)  # 예: 2026.03.11~03.12

            # 경쟁률 컬럼: cols[4], 주관사: cols[5] (경쟁률 있으면) 또는 cols[4]
            competition = "-"
            underwriter = cols[4].get_text(strip=True) if len(cols) > 4 else "-"
            if len(cols) >= 6:
                comp_raw = cols[4].get_text(strip=True)
                if ":" in comp_raw:
                    competition = comp_raw
                    underwriter = cols[5].get_text(strip=True) if len(cols) > 5 else "-"

            # 경쟁률 없는 경우 스킵 (아직 마감 안 됨)
            if competition == "-":
                continue

            # 청약 종료일 파싱
            subscribe_end = None
            if "~" in period:
                parts = period.split("~")
                start_raw = parts[0].strip()
                end_raw = parts[1].strip()
                try:
                    start_date = datetime.strptime(start_raw, "%Y.%m.%d")
                    year_str = start_raw[:4]
                    if len(end_raw) <= 5:
                        end_dt = datetime.strptime(f"{year_str}.{end_raw}", "%Y.%m.%d")
                    else:
                        end_dt = datetime.strptime(end_raw, "%Y.%m.%d")
                    subscribe_end = end_dt.strftime("%Y-%m-%d")
                except Exception:
                    pass

            if subscribe_end == today:
                results.append({
                    "name": name,
                    "subscribe_end": subscribe_end,
                    "competition": competition,
                    "underwriter": underwriter,
                })
    except Exception as e:
        print(f"경쟁률 스크래핑 오류: {e}")

    return results


def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    res = requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    })
    if res.status_code == 200:
        print("경쟁률 알림 전송 성공")
    else:
        print(f"전송 실패: {res.text}")


def main():
    items = fetch_competition_rate()
    if not items:
        print("오늘 청약 마감 공모주 없음 또는 경쟁률 미공개 - 알림 미발송")
        return

    lines = ["🏆 <b>오늘 공모주 청약 마감 경쟁률</b>\n"]
    for item in items:
        lines.append(
            f"  • {item['name']}\n"
            f"    경쟁률: {item['competition']}\n"
            f"    주관증권사: {item['underwriter']}"
        )
    send_telegram("\n".join(lines))


if __name__ == "__main__":
    main()
