# 공모주 텔레그램 알림 봇 - 구축 요약

## 개요
국내 공모주 청약일·상장일을 매일 오전 10시(KST)에 텔레그램으로 자동 알림하는 시스템

---

## 구성

| 항목 | 내용 |
|------|------|
| 데이터 소스 | 38커뮤니케이션 (공모주 일정 스크래핑) |
| 알림 수단 | 텔레그램 봇 |
| 실행 환경 | GitHub Actions (클라우드, 무료) |
| 스케줄 | 매일 오전 10시 KST (UTC 01:00) |

---

## 파일 구조

```
Project/
├── src/
│   ├── fetch_ipo.py       # 38커뮤니케이션에서 청약일/상장일 수집
│   └── notify.py          # 텔레그램 알림 발송
├── .github/
│   └── workflows/
│       └── ipo_notify.yml # GitHub Actions 스케줄 워크플로우
├── requirements.txt       # Python 패키지 (requests, beautifulsoup4)
└── README.md
```

---

## 동작 방식

1. GitHub Actions가 매일 오전 10시(KST) 자동 실행
2. `fetch_ipo.py` → 38커뮤니케이션 크롤링으로 오늘 청약 시작·상장 공모주 조회
3. `notify.py` → 해당 종목이 있으면 텔레그램으로 알림 발송
4. 오늘 해당 공모주가 없으면 알림 미발송

---

## 알림 메시지 예시

```
📋 오늘 공모주 청약 시작
  • 삼성바이오로직스
    청약기간: 2026-03-12 ~ 2026-03-13

🚀 오늘 공모주 상장
  • LG에너지솔루션  (상장일: 2026-03-12)
```

---

## GitHub 저장소 정보

| 항목 | 값 |
|------|------|
| 저장소 URL | https://github.com/cksdud9283-art/ipo-alert |
| 소유자 | cksdud9283-art |
| 공개 여부 | Public |

---

## GitHub Secrets 설정 목록

| Secret 이름 | 용도 |
|-------------|------|
| `DART_API_KEY` | 금융감독원 DART API 인증키 |
| `TELEGRAM_TOKEN` | 텔레그램 봇 토큰 |
| `TELEGRAM_CHAT_ID` | 텔레그램 수신 Chat ID |

---

## 사용된 외부 서비스

| 서비스 | 용도 | 비용 |
|--------|------|------|
| GitHub Actions | 자동 스케줄 실행 | 무료 |
| 텔레그램 봇 | 휴대폰 알림 수신 | 무료 |
| DART 오픈API | 공모주 공시 데이터 | 무료 |
| 38커뮤니케이션 | 청약일/상장일 일정 | 무료 (스크래핑) |

---

## 수동 실행 방법

GitHub 저장소 → **Actions** → `공모주 알림` → **Run workflow** 버튼 클릭

---

## 구축일

2026년 3월 12일
