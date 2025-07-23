#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MongoDB 로그 저장 기능 테스트 스크립트
"""

import requests
import json
from common import get_chat_history, save_chat_log

def test_chat_api():
    """채팅 API 테스트"""
    print("=== 채팅 API 테스트 ===")
    
    # 테스트 메시지들
    test_messages = [
        {"request_message": "안녕하세요!", "mode": "qna", "user_id": "test_user_1"},
        {"request_message": "반품 어떻게 하나요?", "mode": "faq", "user_id": "test_user_1"},
        {"request_message": "비트코인 시세 알려줘", "mode": "price", "user_id": "test_user_2"},
        {"request_message": "파이썬 프로그래밍", "mode": "search", "user_id": "test_user_2"}
    ]
    
    for i, test_data in enumerate(test_messages, 1):
        print(f"\n--- 테스트 {i} ---")
        print(f"메시지: {test_data['request_message']}")
        print(f"모드: {test_data['mode']}")
        print(f"사용자: {test_data['user_id']}")
        
        try:
            response = requests.post(
                "http://localhost:5000/chat-api",
                headers={"Content-Type": "application/json"},
                data=json.dumps(test_data)
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 응답: {result['response_message'][:50]}...")
            else:
                print(f"❌ 오류: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 연결 오류: {e}")

def test_direct_logging():
    """직접 로그 저장 테스트"""
    print("\n=== 직접 로그 저장 테스트 ===")
    
    test_logs = [
        {
            "user_message": "직접 테스트 메시지 1",
            "bot_response": "테스트 응답 1입니다.",
            "mode": "qna",
            "user_id": "direct_test_user"
        },
        {
            "user_message": "직접 테스트 메시지 2", 
            "bot_response": "테스트 응답 2입니다.",
            "mode": "faq",
            "user_id": "direct_test_user"
        }
    ]
    
    for i, log_data in enumerate(test_logs, 1):
        print(f"\n--- 직접 테스트 {i} ---")
        success = save_chat_log(**log_data)
        if success:
            print(f"✅ 로그 저장 성공: {log_data['user_message']}")
        else:
            print(f"❌ 로그 저장 실패: {log_data['user_message']}")

def test_history_retrieval():
    """히스토리 조회 테스트"""
    print("\n=== 히스토리 조회 테스트 ===")
    
    test_users = ["test_user_1", "test_user_2", "direct_test_user"]
    
    for user_id in test_users:
        print(f"\n--- {user_id}의 히스토리 ---")
        history = get_chat_history(user_id=user_id, limit=5)
        
        if history:
            print(f"✅ {len(history)}개의 대화 기록 발견")
            for i, chat in enumerate(history, 1):
                print(f"  {i}. [{chat['mode']}] {chat['user_message'][:30]}...")
        else:
            print(f"❌ {user_id}의 대화 기록이 없습니다.")

def test_chat_history_api():
    """채팅 히스토리 API 테스트"""
    print("\n=== 채팅 히스토리 API 테스트 ===")
    
    test_users = ["test_user_1", "test_user_2"]
    
    for user_id in test_users:
        print(f"\n--- {user_id}의 API 히스토리 ---")
        try:
            response = requests.get(
                f"http://localhost:5000/chat-history?user_id={user_id}&limit=3"
            )
            
            if response.status_code == 200:
                result = response.json()
                history = result.get('history', [])
                print(f"✅ {len(history)}개의 대화 기록 조회 성공")
                for i, chat in enumerate(history, 1):
                    print(f"  {i}. [{chat['mode']}] {chat['user_message'][:30]}...")
            else:
                print(f"❌ API 오류: {response.status_code}")
                
        except Exception as e:
            print(f"❌ API 연결 오류: {e}")

if __name__ == "__main__":
    print("🚀 MongoDB 로그 저장 기능 테스트 시작")
    print("=" * 50)
    
    # 1. 직접 로그 저장 테스트
    test_direct_logging()
    
    # 2. 히스토리 조회 테스트
    test_history_retrieval()
    
    # 3. 채팅 API 테스트 (서버가 실행 중이어야 함)
    print("\n" + "=" * 50)
    print("⚠️  다음 테스트는 서버가 실행 중이어야 합니다.")
    print("서버를 실행하려면: python application.py")
    
    try:
        test_chat_api()
        test_chat_history_api()
    except Exception as e:
        print(f"❌ 서버 연결 실패: {e}")
        print("서버를 먼저 실행해주세요!")
    
    print("\n" + "=" * 50)
    print("✅ 테스트 완료!") 