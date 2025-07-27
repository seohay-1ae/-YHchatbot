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

def get_fallback_policy_info():
    """API 오류 시 제공할 기본 정책 정보"""
    return """현재 농업인을 위한 주요 정책 정보를 안내드립니다:

1. **2025년 농업인 직불금**: 소득보전직불금, 경영이전직불금 등 다양한 직불금 지원
2. **농업기계 구입 지원**: 농기계 구입 시 최대 50%까지 지원
3. **스마트팜 지원**: ICT 기술을 활용한 첨단 농업시설 구축 지원
4. **농업인 교육**: 농업기술센터를 통한 전문 교육 프로그램
5. **농산물 브랜드화**: 지역 특산품 브랜드 개발 및 마케팅 지원

더 자세한 정보는 농림축산식품부 홈페이지나 지역 농협을 통해 문의하시기 바랍니다."""

def handle_policy(user_message):
    try:
        tavily_api_key = os.getenv("TAVILY_API_KEY")
        
        # API 키 검증
        if not tavily_api_key:
            print("[DEBUG] Tavily API 키가 설정되지 않음")
            return {"response": get_fallback_policy_info(), "type": "policy"}
        
        tavily_url = "https://api.tavily.com/search"
        headers = {"Content-Type": "application/json"}
        
        # 최신 정책 정보를 우선적으로 검색하도록 쿼리 개선
        current_year = "2025"
        enhanced_query = f"{user_message} {current_year}년 최신 정책"
        
        payload = {
            "api_key": tavily_api_key,
            "query": enhanced_query,
            "search_depth": "advanced",
            "include_answer": False,
            "include_raw_content": False,
            "max_results": 5
        }
        
        print(f"[DEBUG] Tavily API 요청 시작: {enhanced_query}")
        tavily_resp = requests.post(tavily_url, headers=headers, data=json.dumps(payload), timeout=60)
        
        print(f"[DEBUG] Tavily API 응답 상태 코드: {tavily_resp.status_code}")
        print(f"[DEBUG] Tavily API 응답 헤더: {dict(tavily_resp.headers)}")
        
        # HTTP 상태 코드 확인
        if tavily_resp.status_code != 200:
            print(f"[DEBUG] Tavily API HTTP 오류: {tavily_resp.status_code}")
            print(f"[DEBUG] 오류 응답 내용: {tavily_resp.text[:500]}")
            return {"response": get_fallback_policy_info(), "type": "policy"}
        
        # 응답 내용 확인
        response_text = tavily_resp.text.strip()
        print(f"[DEBUG] Tavily API 응답 길이: {len(response_text)}")
        print(f"[DEBUG] Tavily API 응답 내용 (처음 200자): {response_text[:200]}")
        
        if not response_text:
            print("[DEBUG] Tavily API 응답이 비어있음")
            return {"response": get_fallback_policy_info(), "type": "policy"}
        
        # JSON 파싱 시도
        try:
            tavily_data = tavily_resp.json()
        except json.JSONDecodeError as e:
            print(f"[DEBUG] Tavily API JSON 파싱 오류: {e}")
            print(f"[DEBUG] 응답 내용: {response_text[:500]}")
            return {"response": get_fallback_policy_info(), "type": "policy"}
        
        observations = tavily_data.get("results", [])
        print(f"[DEBUG] 검색 결과 수: {len(observations)}")
        
        if not observations:
            print("[DEBUG] Tavily API 검색 결과 없음")
            return {"response": get_fallback_policy_info(), "type": "policy"}
        
        # 최신 정보 우선 필터링
        recent_policies = []
        for obs in observations:
            title = obs.get("title", "")
            content = obs.get("content", "")
            url = obs.get("url", "")
            
            # 2025년, 2024년 정보 우선 선택
            if any(year in title or year in content for year in ["2025", "2024"]):
                recent_policies.append(obs)
        
        # 최신 정보가 없으면 전체 결과 사용
        if not recent_policies:
            recent_policies = observations[:3]
        
        print(f"[DEBUG] 필터링된 최신 정책 수: {len(recent_policies)}")
        
        obs_answer = ""
        for i, obs in enumerate(recent_policies):
            title = obs.get("title", "")
            content = filter_ad_lines(obs.get("content", ""))
            url = obs.get("url", "")
            summary = ""
            if content:
                try:
                    prompt = (
                        "아래 내용을 3~4문장으로, 핵심 정보만 요약해줘. "
                        "2025년, 2024년 최신 정책 정보를 우선적으로 포함하고, "
                        "광고, 예약, 판매, 블로그 안내, 농장명, 브랜드명, 고객 안내, 이벤트, 할인, 후기, 포장, 배송, 주문, 신청, 문의 등은 절대 포함하지 마.\n\n"
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
        
        obs_answer = obs_answer.strip() if obs_answer else get_fallback_policy_info()
        return {"response": obs_answer, "type": "policy"}
        
    except requests.exceptions.RequestException as e:
        print(f"[DEBUG] Tavily API 요청 오류: {e}")
        return {"response": get_fallback_policy_info(), "type": "policy"}
    except Exception as e:
        print(f"[DEBUG] Tavily API 기타 오류: {e}")
        return {"response": get_fallback_policy_info(), "type": "policy"} 