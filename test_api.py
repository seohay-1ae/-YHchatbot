import os
from dotenv import load_dotenv
from openai import OpenAI

# 환경 변수 로드
load_dotenv()

# OpenAI API 키 가져오기
api_key = os.getenv("OPENAI_API_KEY")
print(f"API 키 확인: {api_key[:20]}..." if api_key else "API 키가 없습니다")

if api_key:
    try:
        # OpenAI 클라이언트 생성
        client = OpenAI(api_key=api_key)
        
        # 간단한 API 호출 테스트
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "안녕하세요"}],
            max_tokens=10
        )
        
        print("✅ API 키가 유효합니다!")
        print(f"응답: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"❌ API 키 오류: {e}")
else:
    print("❌ API 키가 설정되지 않았습니다") 