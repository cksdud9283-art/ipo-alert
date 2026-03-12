# 공모주 텔레그램 알림 봇

매일 오전 10시(KST) 공모주 청약일·상장일을 텔레그램으로 자동 알림합니다.

## GitHub Secrets 설정

GitHub 저장소 → Settings → Secrets and variables → Actions → New repository secret

| Secret 이름 | 값 |
|---|---|
| `DART_API_KEY` | DART 오픈API 인증키 |
| `TELEGRAM_TOKEN` | 텔레그램 봇 토큰 |
| `TELEGRAM_CHAT_ID` | 텔레그램 Chat ID |

## Secrets 값

| Secret 이름 | 값 |
|---|---|
| `DART_API_KEY` | `fb73e43728924dcac03ce2e138393a667cb1cf61` |
| `TELEGRAM_TOKEN` | BotFather에서 발급받은 토큰 |
| `TELEGRAM_CHAT_ID` | `8035972183` |

## 파일 구조

```
src/
  fetch_ipo.py   # 38커뮤니케이션에서 공모주 청약/상장 일정 수집
  notify.py      # 텔레그램 알림 발송
.github/workflows/
  ipo_notify.yml # GitHub Actions 스케줄 (매일 오전 10시 KST)
```
