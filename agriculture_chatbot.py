import os
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from openai import OpenAI
from langchain_community.tools import TavilySearchResults
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI
import requests
import json
from datetime import datetime
import pytz
import re
from collections import deque
from handlers.product_handler import handle_product
from handlers.faq_handler import handle_faq
from handlers.price_handler import handle_price
from handlers.export_handler import handle_export
from handlers.policy_handler import handle_policy
from handlers.search_handler import handle_search
from product_list import PRODUCT_KEYWORDS
from handlers.product_list_handler import handle_product_list
from handlers.product_check_handler import handle_product_check
from pymongo import MongoClient

load_dotenv()
mongo_uri = os.getenv("MONGO_CLUSTER_URI")
client = MongoClient(mongo_uri)
db = client["chatbot_db"]
collection = db["chat_logs"]

app = Flask(__name__)

def save_chat_log(user_id, user_message, bot_message):
    try:
        log = {
            "user_id": user_id,
            "user_message": user_message,
            "bot_message": bot_message,
            "timestamp": datetime.now()
        }
        collection.insert_one(log)
    except Exception as e:
        print(f"[MongoDB 저장 오류] {e}")

# OpenAI 클라이언트 설정
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# LangChain 설정
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

# Tavily 검색 도구 설정
search_tool = TavilySearchResults(api_key=os.getenv("TAVILY_API_KEY"))

# 오늘 날짜/시간을 한글로 반환하는 함수
def get_today_str():
    korea = pytz.timezone('Asia/Seoul')
    now = datetime.now(korea)
    weekday_map = {"Monday": "월요일", "Tuesday": "화요일", "Wednesday": "수요일", "Thursday": "목요일", "Friday": "금요일", "Saturday": "토요일", "Sunday": "일요일"}
    eng_weekday = now.strftime("%A")
    kor_weekday = weekday_map.get(eng_weekday, eng_weekday)
    return now.strftime(f"%Y년 %m월 %d일 ({kor_weekday})")

def get_now_str():
    korea = pytz.timezone('Asia/Seoul')
    now = datetime.now(korea)
    weekday_map = {"Monday": "월요일", "Tuesday": "화요일", "Wednesday": "수요일", "Thursday": "목요일", "Friday": "금요일", "Saturday": "토요일", "Sunday": "일요일"}
    eng_weekday = now.strftime("%A")
    kor_weekday = weekday_map.get(eng_weekday, eng_weekday)
    return now.strftime(f"%Y년 %m월 %d일 {kor_weekday} %H:%M")

# 에이전트 초기화
agent = initialize_agent(
    tools=[search_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    agent_kwargs={
        "system_message": (
            f"너는 농업, 농산물, 정책, 시세, 유통, 인증 등 농산물 도매와 관련된 전문 AI 챗봇이야. "
            f"참고: 오늘 날짜는 {get_today_str()}이고, 현재 시간은 {get_now_str()}이야. "
            "검색 결과가 영어로 제공되어도 반드시 한국어로 번역하여 답변하라."
            "모든 답변, 요약, 출처 안내까지 반드시 한국어로 작성하라."
            "웹 검색 결과의 주요 내용을 빠짐없이 포함해서, 각 결과의 제목, 요약, 출처, 링크를 모두 명시해 풍부하게 답변해. "
            "특히, 사용자가 원하는 정보가 여러 검색 결과에 나올 경우, 각 결과를 항목별로 정리해서 보여주고, 반드시 실제 링크와 출처를 포함해. "
            "답변은 친절하고, 구체적이며, 신뢰할 수 있게 작성해."
        )
    }
)


# 대화 히스토리 저장 (간단한 메모리)
user_histories = {}

def is_product_list_query(msg):
    """
    사용자의 질문이 '전체 품목 안내' 의도(예: 판매 품목, 상품 리스트 등)인지 판별하는 함수.
    - '판매/취급/파는/전체/모든/전부' + '품목/상품/리스트/목록/종류' 조합이 포함된 경우 True 반환
    - 또는 자주 쓰는 단일 패턴(전체 품목, 상품 리스트 등)이 포함된 경우 True 반환
    - 그 외에는 False
    """
    patterns = [
        ("판매", ["품목", "상품", "리스트", "목록", "종류"]),  # 예: '판매 품목', '판매 상품', ...
        ("취급", ["품목", "상품", "리스트", "목록", "종류"]),  # 예: '취급 품목', ...
        ("파는", ["품목", "상품", "리스트", "목록", "종류"]),  # 예: '파는 품목', ...
        ("전체", ["품목", "상품", "리스트", "목록", "종류"]),  # 예: '전체 품목', ...
        ("모든", ["품목", "상품", "리스트", "목록", "종류"]),  # 예: '모든 상품', ...
        ("전부", ["품목", "상품", "리스트", "목록", "종류"]),  # 예: '전부 품목', ...
    ]
    for first, seconds in patterns:
        # 두 그룹(예: '판매' + '품목')이 모두 포함된 경우 True
        if first in msg and any(s in msg for s in seconds):
            return True
    # 자주 쓰는 단일 패턴(조합이 아니어도 바로 인식)
    single_patterns = [
        "상품 리스트", "품목 목록", "전부 뭐야", "무엇을 판매", "뭐 팔아"
    ]
    if any(p in msg for p in single_patterns):
        return True
    return False

def is_product_check_query(msg):
    """
    사용자의 질문이 '고추도 팔아?', '망고도 있나요?', '감자 팔아?' 등 품목 판매 여부 확인 의도인지 판별하는 함수
    - '도 팔', '도 있', ... 기존 패턴
    - 품목명 + 동사(팔아, 있, 판매, 취급, 구입, 구매) 조합이 메시지에 포함되어 있으면 True
    """
    patterns = ["도 팔", "도 있", "도 판매", "도 취급", "도 구입", "도 구매"]
    if any(p in msg for p in patterns):
        return True
    # '도'가 없는 품목+동사 패턴도 인식
    tokens = re.findall(r'[\w가-힣]+', msg)
    verbs = ["팔아", "있", "판매", "취급", "구입", "구매"]
    for t in tokens:
        for v in verbs:
            if t.endswith(v):
                return True
    return False

def classify_category_llm(user_message):
    prompt = f"""
아래 질문을 가장 적합한 카테고리로 분류해줘.
- simple_info: 오늘 날짜, 현재 시간, 인사(안녕, 반가워 등), 오늘 기분이 어때? 등
- product_list: 전체 품목 안내, 판매 품목, 상품 리스트, 모든 상품, 취급 품목 등
- product_check: 품목 판매 여부 확인(고추도 팔아?, 망고도 있나요?, 고등어는 안팔아? 등)
- faq: 고객센터, 반품, 배송, 결제, 등록 제한, 판매자 구매, 상품 등록 유의사항, 금지된 상품, 판매자인데 구매 가능해? 등
- price: 시세, 가격, 금액, 단가 등
- product: 농산물 정보, 제철, 보관법, 재배법, 요즘 딸기가 나와?, 요즘 딸기가 수확돼? 등
- policy: 정책, 제도, 지원, 법령, 수출입 등
- 기타: 위에 해당하지 않는 경우

질문: \"{user_message}\"
카테고리(영어 소문자만, 예: simple_info/product_list/product_check/faq/price/product/policy/other)로만 답해줘:
"""
    completion = client.chat.completions.create(
        model="gpt-4o-2024-05-13",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=10,
        temperature=0
    )
    category = completion.choices[0].message.content.strip().lower()
    if category not in ["simple_info", "product_list", "product_check", "faq", "price", "product", "policy"]:
        return "search"
    return category

# LLM 기반 분류를 실제 분기에서 사용
classify_category = classify_category_llm

@app.route('/chat', methods=['POST'])
def chat():
    """챗봇 메인 엔드포인트"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        user_id = data.get('user_id', 'anonymous')

        if not user_message:
            return jsonify({"error": "메시지가 필요합니다."}), 400

        # 대화 히스토리 가져오기 (최대 3턴)
        history = user_histories.get(user_id, deque(maxlen=3))
        
        # 이전 대화 컨텍스트 확인
        context_category = None
        if len(history) >= 1:
            prev_bot_message = history[-1][1] if history else None
            if prev_bot_message:
                # 모든 공백, 줄바꿈, 문장부호 제거 후 비교
                normalized = re.sub(r'[\s\?\!\.]', '', prev_bot_message)
                if "취급중인상품목록을알려드릴까요" in normalized:
                    if any(word in user_message.lower() for word in ["응", "네", "좋아", "알려줘", "보여줘", "그래", "좋다", "어", "좋아요", "네요", "알려주세요", "보여주세요"]):
                        context_category = "product_list"
        
        # 컨텍스트가 없으면 일반 분류 수행
        if not context_category:
            category = classify_category(user_message)
        else:
            category = context_category
            
        print(f"[DEBUG] 분류된 카테고리: {category}")

        if category == "simple_info":
            korea = pytz.timezone('Asia/Seoul')
            now = datetime.now(korea)
            weekday_map = {"Monday": "월요일", "Tuesday": "화요일", "Wednesday": "수요일", "Thursday": "목요일", "Friday": "금요일", "Saturday": "토요일", "Sunday": "일요일"}
            eng_weekday = now.strftime("%A")
            kor_weekday = weekday_map.get(eng_weekday, eng_weekday)
            today_str = now.strftime(f"%Y년 %m월 %d일 ({kor_weekday})")
            time_str = now.strftime(f"%Y년 %m월 %d일 {kor_weekday} %H:%M")
            prompt = f'''
아래 사용자의 질문에 대해 친절하고 자연스럽게 답변해줘. 
만약 날짜가 필요하면 {{date}}, 시간이 필요하면 {{time}} 토큰을 답변에 포함해. 실제 값은 시스템이 자동으로 채워줄 거야.
질문: "{user_message}"
'''
            completion = client.chat.completions.create(
                model="gpt-4o-2024-05-13",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.5
            )
            response_text = completion.choices[0].message.content.strip()
            # 토큰 치환
            response_text = response_text.replace("{date}", today_str).replace("{time}", time_str)
            save_chat_log(user_id, user_message, response_text)
            # 히스토리 저장
            history.append((user_message, response_text))
            user_histories[user_id] = history
            return jsonify({
                "response": response_text,
                "type": "simple_info"
            })

        # 카테고리별 핸들러 함수로 위임
        if category == "export":
            result = handle_export(user_message)
        elif category == "policy":
            result = handle_policy(user_message)
        elif category == "product":
            result = handle_product(user_message)
        elif category == "price":
            # 대화 히스토리를 price 핸들러에 전달
            conversation_history = []
            for user_msg, bot_msg in history:
                conversation_history.append({"role": "user", "content": user_msg})
                conversation_history.append({"role": "assistant", "content": bot_msg})
            result = handle_price(user_message, conversation_history)
        elif category == "faq":
            result = handle_faq(user_message)
        elif category == "search":
            result = handle_search(user_message)
        elif category == "product_list":
            result = handle_product_list(user_message)
        elif category == "product_check":
            result = handle_product_check(user_message)
        else:
            result = handle_search(user_message)
        
        save_chat_log(user_id, user_message, result.get("response", str(result)))
        # 히스토리 저장 (모든 분기에서 공통)
        history.append((user_message, result.get("response", str(result))))
        user_histories[user_id] = history
        return jsonify(result)
    except Exception as e:
        print(f"[API 오류] {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """헬스 체크 엔드포인트"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/')
def chat_ui():
    """챗봇 웹 UI"""
    return render_template('agriculture_chat.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 