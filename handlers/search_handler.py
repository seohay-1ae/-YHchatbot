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

def extract_keywords(user_message):
    # 한글, 영문, 숫자 단어만 추출 (간단 버전)
    import re
    return [w for w in re.findall(r'[\w가-힣]+', user_message) if len(w) > 1]

def handle_search(user_message):
    try:
        tavily_api_key = os.getenv("TAVILY_API_KEY")
        tavily_url = "https://api.tavily.com/search"
        headers = {"Content-Type": "application/json"}
        user_keywords = extract_keywords(user_message)
        filtered_results = []
        seen_urls = set()
        tries = 0
        max_results_needed = 3
        max_tries = 5
        while len(filtered_results) < max_results_needed and tries < max_tries:
            payload = {
                "api_key": tavily_api_key,
                "query": user_message,
                "search_depth": "advanced",
                "include_answer": False,
                "include_raw_content": False,
                "max_results": max_results_needed * 2  # 한 번에 여러 개 요청
            }
            tavily_resp = requests.post(tavily_url, headers=headers, data=json.dumps(payload))
            tavily_data = tavily_resp.json()
            observations = tavily_data.get("results", [])
            for obs in observations:
                url = obs.get("url", "")
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                title = obs.get("title", "")
                content = filter_ad_lines(obs.get("content", ""))
                summary = ""
                if content:
                    try:
                        prompt = (
                            f"아래 내용을 '{user_message}'와 직접적으로 관련된 부분만 3~4문장으로 요약해줘. 관련 없는 뉴스, 광고, 기타 정보는 절대 포함하지 마.\n\n"
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
                if not any(k in summary for k in user_keywords):
                    continue
                filtered_results.append((title, summary, url))
                if len(filtered_results) == max_results_needed:
                    break
            tries += 1
        obs_answer = ""
        for i, (title, summary, url) in enumerate(filtered_results):
            obs_answer += f"{i+1}. [{title}] {summary}\n출처: <a href='{url}' target='_blank'>{url}</a>\n\n"
        obs_answer = obs_answer.strip() if obs_answer else "관련 정보가 검색되지 않았습니다."
        return {"response": obs_answer, "type": "search"}
    except Exception as e:
        print(f"[DEBUG] Tavily API 파싱 오류: {e}")
        return {"response": "관련 정보가 검색되지 않았습니다.", "type": "search"} 