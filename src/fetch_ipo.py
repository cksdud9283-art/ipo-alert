import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import os
import ssl
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 38커뮤니케이션 구형 SSL 대응용 어댑터
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

class LegacySSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.set_ciphers("DEFAULT:@SECLEVEL=1")
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        kwargs["ssl_context"] = ctx
        super().init_poolmanager(*args, **kwargs)

DART_API_KEY = os.environ.get("DART_API_KEY")


def get_ipo_list():
    """DART API에서 공모주 공시 목록 조회"""
    today = datetime.today()
    start_date = today.strftime("%Y%m%d")
    end_date = (today + timedelta(days=30)).strftime("%Y%m%d")

    url = "https://opendart.fss.or.kr/api/list.json"
    params = {
        "crtfc_key": DART_API_KEY,
        "pblntf_ty": "I",  # 증권신고서 (공모)
        "bgn_de": start_date,
        "end_de": end_date,
        "page_count": 100,
    }

    res = requests.get(url, params=params)
    data = res.json()

    if data.get("status") != "000":
        print(f"DART API 오류: {data.get('message')}")
        return []

    return data.get("list", [])


def get_ipo_schedule():
    """38커뮤니케이션에서 공모주 청약일/상장일 스크래핑"""
    import re
    from bs4 import BeautifulSoup

    today = datetime.today()
    today_str = today.strftime("%Y-%m-%d")
    results = []

    url = "https://www.38.co.kr/html/fund/index.htm?o=k"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        session = requests.Session()
        session.mount("https://", LegacySSLAdapter())
        res = session.get(url, headers=headers, timeout=10)
        res.encoding = "euc-kr"
        soup = BeautifulSoup(res.text, "html.parser")

        rows = soup.select('table[bgcolor="E6E9ED"] tr')
        for row in rows:
            cols = row.select("td")
            if len(cols) < 7:
                continue

            name = cols[0].get_text(strip=True)
            subscribe_start = cols[2].get_text(strip=True)
            subscribe_end = cols[3].get_text(strip=True)
            listing_date = cols[6].get_text(strip=True)
            underwriter = cols[7].get_text(strip=True) if len(cols) > 7 else "-"

            # 날짜 형식 정규화 (예: 03/12 → 2026-03-12)
            def normalize_date(d):
                d = d.strip()
                if not d or d == "-":
                    return None
                try:
                    month, day = d.split("/")
                    year = today.year
                    dt = datetime(year, int(month), int(day))
                    # 이미 지난 날짜면 내년으로
                    if dt < today - timedelta(days=1):
                        dt = datetime(year + 1, int(month), int(day))
                    return dt.strftime("%Y-%m-%d")
                except Exception:
                    return None

            results.append(
                {
                    "name": name,
                    "subscribe_start": normalize_date(subscribe_start),
                    "subscribe_end": normalize_date(subscribe_end),
                    "listing_date": normalize_date(listing_date),
                    "underwriter": underwriter,
                }
            )
    except Exception as e:
        print(f"스크래핑 오류: {e}")

    return results


def get_today_events():
    """오늘 청약 시작일 또는 상장일에 해당하는 공모주 반환"""
    today = datetime.today().strftime("%Y-%m-%d")
    schedule = get_ipo_schedule()

    subscribe_today = [
        s for s in schedule if s.get("subscribe_start") == today
    ]
    listing_today = [
        s for s in schedule if s.get("listing_date") == today
    ]

    return subscribe_today, listing_today


if __name__ == "__main__":
    sub, listing = get_today_events()
    print("=== 오늘 청약 시작 ===")
    for s in sub:
        print(f"  {s['name']} (청약: {s['subscribe_start']} ~ {s['subscribe_end']}, 주관: {s['underwriter']})")
    print("=== 오늘 상장 ===")
    for s in listing:
        print(f"  {s['name']} (상장일: {s['listing_date']}, 주관: {s['underwriter']})")
