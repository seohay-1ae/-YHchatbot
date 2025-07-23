import os
from dotenv import load_dotenv

load_dotenv()  # 이 줄 추가!
from openai import OpenAI
from dataclasses import dataclass
import pytz
from datetime import datetime, timedelta
import tiktoken
from pymongo import MongoClient


@dataclass(frozen=True)
class Model:
    basic: str = "gpt-4o-mini-2024-07-18"
    advanced: str = "gpt-4o-2024-05-13"


model = Model();
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=30, max_retries=1)


def makeup_response(message, finish_reason="ERROR"):
    return {
        "choices": [
            {
                "finish_reason": finish_reason,
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": message
                }
            }
        ],
        "usage": {"total_tokens": 0},
    }


def gpt_num_tokens(messages, model="gpt-4o"):
    encoding = tiktoken.encoding_for_model(model)
    tokens_per_message = 3  ## 모든 메시지는 다음 형식을 따른다: <|start|>{role/name}\n{content}<|end|>\n
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message  #
        for _, value in message.items():
            num_tokens += len(encoding.encode(value))
    num_tokens += 3  # 모든 메시지는 다음 형식으로 assistant의 응답을 준비한다: <|start|>assistant<|message|>
    return num_tokens


def today():
    korea = pytz.timezone('Asia/Seoul')  # 한국 시간대를 얻습니다.
    now = datetime.now(korea)  # 현재 시각을 얻습니다.
    return (now.strftime("%Y%m%d"))  # 시각을 원하는 형식의 문자열로 변환합니다.


def yesterday():
    korea = pytz.timezone('Asia/Seoul')  # 한국 시간대를 얻습니다.
    now = datetime.now(korea)  # 현재 시각을 얻습니다.
    one_day = timedelta(days=1)  # 하루 (1일)를 나타내는 timedelta 객체를 생성합니다.
    yesterday = now - one_day  # 현재 날짜에서 하루를 빼서 어제의 날짜를 구합니다.
    return yesterday.strftime('%Y%m%d')  # 어제의 날짜를 yyyymmdd 형식으로 변환합니다.


def currTime():
    # 한국 시간대를 얻습니다.
    korea = pytz.timezone('Asia/Seoul')
    # 현재 시각을 얻습니다.
    now = datetime.now(korea)
    # 시각을 원하는 형식의 문자열로 변환합니다.
    formatted_now = now.strftime("%Y.%m.%d %H:%M:%S")
    return (formatted_now)

# MongoDB 연결 및 로그 저장 함수들
def get_mongo_client():
    """MongoDB 클라이언트 반환"""
    return MongoClient(os.getenv("MONGO_CLUSTER_URI"))

def get_chat_collection():
    """채팅 로그 컬렉션 반환"""
    client = get_mongo_client()
    db = client["duri"]
    return db["chat_logs"]

def save_chat_log(user_message, bot_response, mode="qna", user_id="anonymous"):
    """채팅 로그를 MongoDB에 저장"""
    try:
        collection = get_chat_collection()
        
        log_entry = {
            "timestamp": datetime.now(pytz.timezone('Asia/Seoul')),
            "user_id": user_id,
            "mode": mode,
            "user_message": user_message,
            "bot_response": bot_response,
            "created_at": currTime()
        }
        
        result = collection.insert_one(log_entry)
        print(f"[📝 로그 저장 완료] ID: {result.inserted_id}")
        return True
    except Exception as e:
        print(f"[❌ 로그 저장 실패] {e}")
        return False

def get_chat_history(user_id="anonymous", limit=10):
    """사용자의 채팅 히스토리 조회"""
    try:
        collection = get_chat_collection()
        cursor = collection.find(
            {"user_id": user_id},
            {"_id": 0, "user_message": 1, "bot_response": 1, "mode": 1, "created_at": 1}
        ).sort("timestamp", -1).limit(limit)
        
        return list(cursor)
    except Exception as e:
        print(f"[❌ 히스토리 조회 실패] {e}")
        return []
