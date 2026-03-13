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


def get_underwriter_from_dart(company_name: str) -> str:
    """DART API로 종목명 기준 주관사 조회"""
    if not DART_API_KEY:
        return "-"
    try:
        # 최근 1년 증권신고서(공모) 검색
        today = datetime.today()
        url = "https://opendart.fss.or.kr/api/list.json"
        params = {
            "crtfc_key": DART_API_KEY,
            "corp_name": company_name,
            "pblntf_ty": "I",
            "bgn_de": (today - timedelta(days=365)).strftime("%Y%m%d"),
            "end_de": today.strftime("%Y%m%d"),
            "page_count": 5,
        }
        res = requests.get(url, params=params, timeout=10)
        data = res.json()
        if data.get("status") != "000":
            return "-"
        items = data.get("list", [])
        if not items:
            return "-"
        # 첫 번째 공시의 rcept_no로 상세 조회
        rcept_no = items[0].get("rcept_no")
        detail_url = "https://opendart.fss.or.kr/api/irdsSttus.json"
        detail_res = requests.get(detail_url, params={
            "crtfc_key": DART_API_KEY,
            "rcept_no": rcept_no,
        }, timeout=10)
        detail = detail_res.json()
        if detail.get("status") != "000":
            return "-"
        detail_list = detail.get("list", [])
        underwriters = [
            d.get("lead_mng_nm", "") for d in detail_list
            if d.get("lead_mng_nm")
        ]
        if underwriters:
            return ", ".join(dict.fromkeys(underwriters))  # 중복 제거
    except Exception as e:
        print(f"DART 주관사 조회 실패 ({company_name}): {e}")
    return "-"


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
    results = []

    url = "https://www.38.co.kr/html/fund/index.htm?o=k"
    headers = {"User-Agent": "Mozilla/5.0"}

    def parse_date(d):
        """2026.03.11 형식 → 2026-03-11"""
        d = d.strip()
        if not d or d == "-":
            return None
        try:
            return datetime.strptime(d, "%Y.%m.%d").strftime("%Y-%m-%d")
        except Exception:
            return None

    try:
        session = requests.Session()
        session.mount("https://", LegacySSLAdapter())
        res = session.get(url, headers=headers, timeout=10)
        res.encoding = "euc-kr"
        soup = BeautifulSoup(res.text, "html.parser")

        tables = soup.find_all("table")
        # 테이블25: 종목명 | 청약기간(2026.MM.DD~MM.DD) | 확정공모가 | 희망공모가 | [경쟁률] | 주관사
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
            underwriter = cols[4].get_text(strip=True) if len(cols) > 4 else "-"

            # 경쟁률 있으면 컬럼 밀림 (col[4]=경쟁률, col[5]=주관사)
            if len(cols) >= 6:
                comp = cols[4].get_text(strip=True)
                if ":" in comp:  # 경쟁률 형식
                    underwriter = cols[5].get_text(strip=True) if len(cols) > 5 else "-"

            # 청약기간 파싱: 2026.03.11~03.12
            subscribe_start = None
            subscribe_end = None
            if "~" in period:
                parts = period.split("~")
                start_raw = parts[0].strip()  # 2026.03.11
                end_raw = parts[1].strip()    # 03.12
                subscribe_start = parse_date(start_raw)
                # 끝날짜는 연도 없으면 시작 연도+월 조합
                if subscribe_start and len(end_raw) <= 5:
                    year = subscribe_start[:4]
                    month = subscribe_start[5:7]
                    # 월이 넘어갈 수 있으므로 시작 날짜 기준 월 사용
                    try:
                        subscribe_end = parse_date(f"{year}.{end_raw}")
                    except Exception:
                        subscribe_end = subscribe_start
                else:
                    subscribe_end = parse_date(end_raw)

            if not name or not subscribe_start:
                continue

            results.append({
                "name": name,
                "subscribe_start": subscribe_start,
                "subscribe_end": subscribe_end,
                "listing_date": None,  # 별도 테이블에서 가져옴
                "underwriter": underwriter,
            })

        # 상장일은 테이블40에서 파싱: '03/20 아이엠바이오로직스' 형식
        if len(tables) > 40:
            listing_rows = tables[40].find_all("tr")
            for row in listing_rows:
                cols = row.find_all("td")
                for col in cols:
                    text = col.get_text(strip=True)
                    m = re.match(r"(\d{2}/\d{2})\s+(.+)", text)
                    if m:
                        date_str, lname = m.group(1), m.group(2).strip()
                        try:
                            month, day = date_str.split("/")
                            ldate = datetime(today.year, int(month), int(day))
                            if ldate < today - timedelta(days=1):
                                ldate = datetime(today.year + 1, int(month), int(day))
                            listing_date = ldate.strftime("%Y-%m-%d")
                        except Exception:
                            continue
                        # 매칭되는 종목에 상장일 추가
                        for r in results:
                            if lname[:5] in r["name"] or r["name"][:5] in lname:
                                r["listing_date"] = listing_date
                                break
                        else:
                            underwriter = get_underwriter_from_dart(lname)
                            results.append({
                                "name": lname,
                                "subscribe_start": None,
                                "subscribe_end": None,
                                "listing_date": listing_date,
                                "underwriter": underwriter,
                            })

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
