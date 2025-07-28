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
        
        # API 키 검증
        if not tavily_api_key:
            print("[DEBUG] Tavily API 키가 설정되지 않음")
            return {"response": "검색 서비스를 이용할 수 없습니다. 잠시 후 다시 시도해주세요.", "type": "search"}
        
        tavily_url = "https://api.tavily.com/search"
        headers = {"Content-Type": "application/json"}
        user_keywords = extract_keywords(user_message)
        filtered_results = []
        seen_urls = set()
        tries = 0
        max_results_needed = 3 # 검색 결과 개수 설정
        max_tries = 5  # 검색 시도 횟수
        
        while len(filtered_results) < max_results_needed and tries < max_tries:
            payload = {
                "api_key": tavily_api_key,
                "query": user_message,
                "search_depth": "advanced",
                "include_answer": False,
                "include_raw_content": False,
                "max_results": max_results_needed * 2 
            }
            
            print(f"[DEBUG] Tavily API 요청 시작 (시도 {tries + 1}): {user_message}")
            tavily_resp = requests.post(tavily_url, headers=headers, data=json.dumps(payload), timeout=60)
            
            print(f"[DEBUG] Tavily API 응답 상태 코드: {tavily_resp.status_code}")
            
            # HTTP 상태 코드 확인
            if tavily_resp.status_code != 200:
                print(f"[DEBUG] Tavily API HTTP 오류: {tavily_resp.status_code}")
                print(f"[DEBUG] 오류 응답 내용: {tavily_resp.text[:500]}")
                tries += 1
                continue
            
            # 응답 내용 확인
            response_text = tavily_resp.text.strip()
            if not response_text:
                print("[DEBUG] Tavily API 응답이 비어있음")
                tries += 1
                continue
            
            # JSON 파싱 시도
            try:
                tavily_data = tavily_resp.json()
            except json.JSONDecodeError as e:
                print(f"[DEBUG] Tavily API JSON 파싱 오류: {e}")
                print(f"[DEBUG] 응답 내용: {response_text[:500]}")
                tries += 1
                continue
            
            observations = tavily_data.get("results", [])
            print(f"[DEBUG] 검색 결과 수: {len(observations)}")
            
            if not observations:
                print("[DEBUG] Tavily API 검색 결과 없음")
                tries += 1
                continue
            
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
        
    except requests.exceptions.RequestException as e:
        print(f"[DEBUG] Tavily API 요청 오류: {e}")
        return {"response": "검색 서비스를 이용할 수 없습니다. 잠시 후 다시 시도해주세요.", "type": "search"}
    except Exception as e:
        print(f"[DEBUG] Tavily API 기타 오류: {e}")
        return {"response": "관련 정보가 검색되지 않았습니다.", "type": "search"} 