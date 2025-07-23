import requests
import json

def test_chatbot():
    """농산물 챗봇 테스트"""
    base_url = "http://localhost:5000"
    
    # 테스트 케이스들
    test_cases = [
        {
            "name": "고객센터 - 반품 문의",
            "message": "반품 가능한가요?",
            "expected_type": "customer_service"
        },
        {
            "name": "고객센터 - 배송 문의", 
            "message": "배송 언제되나요?",
            "expected_type": "customer_service"
        },
        {
            "name": "농산물 정보 - 상추",
            "message": "상추 보관 방법 알려주세요",
            "expected_type": "agriculture_info"
        },
        {
            "name": "농산물 정보 - 감자",
            "message": "감자 제철 시기 언제인가요?",
            "expected_type": "agriculture_info"
        },
        {
            "name": "가격 정보 - 상추 시세",
            "message": "오늘 상추 시세는?",
            "expected_type": "price_info"
        },
        {
            "name": "가격 정보 - 감자 시세",
            "message": "감자 가격 얼마인가요?",
            "expected_type": "price_info"
        },
        {
            "name": "웹 검색 - 농업 뉴스",
            "message": "최근 농업 정책 뉴스 알려줘",
            "expected_type": "web_search"
        }
    ]
    
    print("🌾 농산물 챗봇 테스트 시작")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- 테스트 {i}: {test_case['name']} ---")
        print(f"질문: {test_case['message']}")
        
        try:
            response = requests.post(
                f"{base_url}/chat",
                json={
                    "message": test_case['message'],
                    "user_id": "test_user"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 응답 타입: {data.get('type', 'unknown')}")
                print(f"📝 응답 내용:\n{data.get('response', '')}")
                
                if data.get('type') == test_case['expected_type']:
                    print("✅ 예상 타입과 일치")
                else:
                    print(f"⚠️ 예상 타입: {test_case['expected_type']}, 실제 타입: {data.get('type')}")
                    
            else:
                print(f"❌ 오류: {response.status_code}")
                print(f"오류 내용: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ 서버 연결 실패 - 서버가 실행 중인지 확인하세요")
            print("서버 실행 명령어: python agriculture_chatbot.py")
            break
        except Exception as e:
            print(f"❌ 테스트 오류: {str(e)}")
    
    print("\n" + "=" * 50)
    print("✅ 테스트 완료!")

if __name__ == "__main__":
    test_chatbot() 