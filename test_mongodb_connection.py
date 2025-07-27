#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MongoDB 연결 테스트 스크립트
"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient
import ssl

load_dotenv()

def test_mongodb_connection():
    """MongoDB 연결을 테스트합니다."""
    print("=== MongoDB 연결 테스트 ===")
    
    # 환경 변수 확인
    mongo_uri = os.getenv("MONGO_CLUSTER_URI")
    if not mongo_uri:
        print("❌ MONGO_CLUSTER_URI 환경 변수가 설정되지 않았습니다.")
        return False
    
    print(f"📋 연결 문자열: {mongo_uri[:50]}...")
    
    # 방법 1: 기본 연결 시도
    print("\n--- 방법 1: 기본 연결 ---")
    try:
        client = MongoClient(mongo_uri)
        client.admin.command('ping')
        print("✅ 기본 연결 성공!")
        client.close()
        return True
    except Exception as e:
        print(f"❌ 기본 연결 실패: {e}")
    
    # 방법 2: SSL 설정 추가
    print("\n--- 방법 2: SSL 설정 추가 ---")
    try:
        client = MongoClient(
            mongo_uri,
            ssl=True,
            ssl_cert_reqs='CERT_NONE',
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=30000,
            socketTimeoutMS=30000
        )
        client.admin.command('ping')
        print("✅ SSL 설정 연결 성공!")
        client.close()
        return True
    except Exception as e:
        print(f"❌ SSL 설정 연결 실패: {e}")
    
    # 방법 3: TLS 설정
    print("\n--- 방법 3: TLS 설정 ---")
    try:
        client = MongoClient(
            mongo_uri,
            tls=True,
            tlsAllowInvalidCertificates=True,
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=30000,
            socketTimeoutMS=30000
        )
        client.admin.command('ping')
        print("✅ TLS 설정 연결 성공!")
        client.close()
        return True
    except Exception as e:
        print(f"❌ TLS 설정 연결 실패: {e}")
    
    # 방법 4: 연결 문자열 수정
    print("\n--- 방법 4: 연결 문자열 수정 ---")
    try:
        # 연결 문자열에 SSL 설정 추가
        modified_uri = mongo_uri + "&ssl=true&ssl_cert_reqs=CERT_NONE"
        client = MongoClient(modified_uri)
        client.admin.command('ping')
        print("✅ 수정된 연결 문자열 성공!")
        client.close()
        return True
    except Exception as e:
        print(f"❌ 수정된 연결 문자열 실패: {e}")
    
    return False

def test_database_operations():
    """데이터베이스 작업을 테스트합니다."""
    print("\n=== 데이터베이스 작업 테스트 ===")
    
    try:
        # 성공한 연결 방법으로 테스트
        client = MongoClient(
            os.getenv("MONGO_CLUSTER_URI"),
            ssl=True,
            ssl_cert_reqs='CERT_NONE',
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=30000,
            socketTimeoutMS=30000
        )
        
        db = client["duri"]
        collection = db["chat_logs"]
        
        # 테스트 데이터 삽입
        test_data = {
            "test": True,
            "message": "연결 테스트",
            "timestamp": "2025-01-21"
        }
        
        result = collection.insert_one(test_data)
        print(f"✅ 테스트 데이터 삽입 성공: {result.inserted_id}")
        
        # 테스트 데이터 삭제
        collection.delete_one({"_id": result.inserted_id})
        print("✅ 테스트 데이터 삭제 성공")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ 데이터베이스 작업 실패: {e}")
        return False

if __name__ == "__main__":
    print("🚀 MongoDB 연결 테스트 시작")
    print("=" * 50)
    
    # 연결 테스트
    connection_success = test_mongodb_connection()
    
    if connection_success:
        # 데이터베이스 작업 테스트
        db_success = test_database_operations()
        
        if db_success:
            print("\n🎉 모든 테스트 통과!")
        else:
            print("\n⚠️ 연결은 성공했지만 데이터베이스 작업에 실패했습니다.")
    else:
        print("\n❌ 모든 연결 방법이 실패했습니다.")
        print("\n💡 해결 방법:")
        print("1. 네트워크 연결 확인")
        print("2. MongoDB Atlas 설정 확인")
        print("3. IP 화이트리스트 확인")
        print("4. 사용자명/비밀번호 확인")
    
    print("\n" + "=" * 50)
    print("✅ 테스트 완료!") 