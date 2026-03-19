import requests
import os
import json
from datetime import datetime, timezone, timedelta

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# 주제 풀 (날짜 기반으로 순환)
TOPICS = [
    "일상 대화 (카페, 식당 주문)",
    "직장 회의 및 업무 영어",
    "여행 및 공항/호텔",
    "감정 표현 및 공감",
    "쇼핑 및 가격 흥정",
    "친구와의 일상 대화",
    "전화 및 이메일 영어",
    "건강 및 병원",
    "길 묻기 및 교통",
    "취미 및 주말 계획",
    "뉴스 및 시사 토론",
    "집 및 생활 영어",
    "날씨 및 계절 대화",
    "음식 및 요리 영어",
    "학교 및 학습",
]


def get_today_topic() -> str:
    kst = timezone(timedelta(hours=9))
    today = datetime.now(kst)
    idx = today.timetuple().tm_yday % len(TOPICS)
    return TOPICS[idx]


def generate_sentences(topic: str) -> list[dict]:
    """Claude API로 영어회화 문장 10개 생성"""
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    prompt = f"""주제: {topic}

위 주제로 실생활에서 바로 쓸 수 있는 영어회화 문장 10개를 만들어주세요.

반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트 없이 JSON만 출력하세요:
[
  {{"en": "영어 문장", "ko": "한국어 뜻"}},
  ...
]

조건:
- 실제 원어민이 자주 쓰는 자연스러운 표현
- 너무 쉽지도 너무 어렵지도 않은 중급 수준
- 다양한 상황과 표현 방식 포함"""

    payload = {
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=30)
        res.raise_for_status()
        content = res.json()["content"][0]["text"].strip()
        # JSON 파싱
        sentences = json.loads(content)
        return sentences[:10]
    except Exception as e:
        print(f"Claude API 오류: {e}")
        return []


def build_message(topic: str, sentences: list[dict]) -> str:
    kst = timezone(timedelta(hours=9))
    today = datetime.now(kst).strftime("%Y-%m-%d")

    lines = [
        f"📚 <b>오늘의 영어회화 10문장</b>  ({today})",
        f"🎯 오늘의 주제: <b>{topic}</b>",
        "",
    ]

    for i, s in enumerate(sentences, 1):
        lines.append(f"{i}. {s['en']}")
        lines.append(f"   💬 {s['ko']}")
        lines.append("")

    lines.append("✏️ 하루에 한 번씩 소리 내어 읽어보세요!")

    return "\n".join(lines)


def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    res = requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    })
    if res.status_code == 200:
        print("영어회화 알림 전송 성공")
    else:
        print(f"전송 실패: {res.text}")


def main():
    topic = get_today_topic()
    print(f"오늘의 주제: {topic}")

    sentences = generate_sentences(topic)
    if not sentences:
        print("문장 생성 실패")
        return

    message = build_message(topic, sentences)
    send_telegram(message)


if __name__ == "__main__":
    main()
