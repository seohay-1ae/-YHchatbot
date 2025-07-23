from dotenv import load_dotenv
load_dotenv()
import os
import requests
import json
from openai import OpenAI

def filter_ad_lines(text):
    ad_keywords = [
        "예약", "안전", "판매", "주문", "농부", "고객님", "화학비료", "유기물",
        "배송", "구매", "블로그", "프로필", "문의", "상담", "신청", "이벤트", "할인", "특가", "무료", "배송비", "포장", "직거래", "도화농부"
    ]
    lines = text.split('\n')
    filtered = [line for line in lines if not any(k in line for k in ad_keywords)]
    return '\n'.join(filtered)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def handle_export(user_message):
    try:
        tavily_api_key = os.getenv("TAVILY_API_KEY")
        tavily_url = "https://api.tavily.com/search"
        headers = {"Content-Type": "application/json"}
        payload = {
            "api_key": tavily_api_key,
            "query": user_message,
            "search_depth": "advanced",
            "include_answer": False,
            "include_raw_content": False,
            "max_results": 3
        }
        tavily_resp = requests.post(tavily_url, headers=headers, data=json.dumps(payload))
        tavily_data = tavily_resp.json()
        observations = tavily_data.get("results", [])
        obs_answer = ""
        for i, obs in enumerate(observations):
            title = obs.get("title", "")
            content = filter_ad_lines(obs.get("content", ""))
            url = obs.get("url", "")
            summary = ""
            if content:
                try:
                    prompt = (
                        "아래 내용을 3~4문장으로, 핵심 정보만 요약해줘. 광고, 예약, 판매, 블로그 안내, 농장명, 브랜드명, 고객 안내, 이벤트, 할인, 후기, 포장, 배송, 주문, 신청, 문의 등은 절대 포함하지 마.\n\n"
                        f"{content}"
                    )
                    completion = client.chat.completions.create(
                        model="gpt-4o-2024-05-13",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=400,
                        temperature=0.5
                    )
                    summary = completion.choices[0].message.content.strip()
                    summary = filter_ad_lines(summary)
                except Exception as e:
                    print(f"[DEBUG] LLM 요약 오류: {e}")
                    summary = content[:400]
            obs_answer += f"{i+1}. [{title}] {summary}\n출처: <a href='{url}' target='_blank'>{url}</a>\n\n"
        obs_answer = obs_answer.strip() if obs_answer else "관련 정보가 검색되지 않았습니다."
        return {"response": obs_answer, "type": "export"}
    except Exception as e:
        print(f"[DEBUG] Tavily API 파싱 오류: {e}")
        return {"response": "관련 정보가 검색되지 않았습니다.", "type": "export"} 