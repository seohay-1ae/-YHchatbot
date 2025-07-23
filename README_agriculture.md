# 🌾 농산물 도매 챗봇

농산물 도매 사이트를 위한 AI 챗봇입니다. 고객센터, 시세 정보, 농산물 정보, 웹 검색 기능을 제공합니다.

## 🚀 기능

### 1. 고객센터 기능

- **반품/교환**: 반품 정책, 조건, 절차 안내
- **배송**: 배송 기간, 배송사, 추적 방법 안내
- **결제**: 결제 방법, 안전성 정보
- **회원가입**: 가입 절차, 혜택 안내

### 2. 시세 정보

- 실시간 농산물 가격 조회
- 가격 변동 정보
- 지역별 시세 비교 (예정)

### 3. 농산물 정보

- 제철 정보
- 보관 방법
- 영양 정보
- 주요 산지 정보

### 4. 웹 검색

- Tavily을 통한 실시간 웹 검색
- 농업 관련 뉴스 및 정보 검색

## 🛠️ 기술 스택

- **Backend**: Flask
- **Database**: MongoDB (Atlas)
- **AI**: OpenAI GPT-4o-mini
- **Search**: Tavily
- **Framework**: LangChain

## 📦 설치 및 실행

### 1. 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 추가하세요:

```env
# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Tavily API Key (웹 검색용)
TAVILY_API_KEY=your_tavily_api_key_here

# MongoDB Atlas URI
MONGO_CLUSTER_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
```

### 2. 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. 서버 실행

```bash
python agriculture_chatbot.py
```

### 4. 웹 UI 접속

브라우저에서 `http://localhost:5000` 접속

## 🧪 테스트

### API 테스트

```bash
python test_agriculture_chatbot.py
```

### 수동 테스트 예시

```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "반품 가능한가요?", "user_id": "test_user"}'
```

## 📋 API 엔드포인트

### POST /chat

챗봇과 대화하는 메인 엔드포인트

**Request:**

```json
{
  "message": "질문 내용",
  "user_id": "사용자 ID"
}
```

**Response:**

```json
{
  "response": "답변 내용",
  "type": "응답 타입 (customer_service|agriculture_info|price_info|web_search)"
}
```

### GET /health

서버 상태 확인

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2025-01-21T10:30:00"
}
```

## 🎯 사용 예시

### 고객센터 질문 (faq)

- "반품 가능한가요?"
- "배송 언제되나요?"
- "결제 방법 알려주세요"
- "회원가입 어떻게 하나요?"

### 시세 질문 (price)

- "오늘 상추 시세는?"
- "감자 가격 얼마인가요?"
- "복숭아 시세 알려줘"
- "수박 가격 알려줘"

### 농산물 정보 (product)

- "상추 보관 방법 알려주세요"
- "감자 제철 시기 언제인가요?"
- "복숭아 영양 정보 알려줘"
- "땅콩 어느 지역이 제일 맛있나요?"
- "파인애플은 언제가 제철이야?"
- "망고 보관법 알려줘"

### 정책/제도 (policy)

- "최근 시행된 농업 정책 알려줘"
- "농업 지원 제도 뭐가 있어?"
- "2024년 농업 정책 변화 알려줘"
- "농민을 위한 정부 지원 정책이 궁금해"

### 수출/통계 (export)

- "2023년 우리나라 농산물 수출액이 얼마야?"
- "농산물 수출 통계 알려줘"
- "최근 5년간 농산물 수출 증감률은?"
- "주요 수출 품목과 금액이 궁금해"

### 웹 검색 (search)

- "최근 농업 정책 뉴스 알려줘"
- "농산물 수출 동향 검색해줘"
- "유기농 인증 방법 알려줘"
- "농업 관련 최신 이슈 알려줘"

### 전체 품목 안내 (product_list)

- "판매하는 품목이 뭐야?"
- "전체 품목 리스트 보여줘"
- "사이트에서 파는 상품 종류 알려줘"
- "모든 상품 목록 알려줘"

### 품목 판매 여부 확인 (product_check)

- "고추도 팔아?"
- "망고도 있나요?"
- "수박도 판매해?"
- "파프리카도 취급하나요?"
- "아보카도도 구입할 수 있어?"

### 기타 (simple_info)

- "오늘 날짜 알려줘"
- "지금 몇시야?"
- "안녕"

## 🔄 향후 개발 계획

### 1단계 (현재)

- ✅ 기본 고객센터 기능
- ✅ 기본 농산물 정보
- ✅ 임시 가격 정보
- ✅ 웹 검색 기능

### 2단계 (예정)

- 🔄 Spring Boot API 연동
- 🔄 실시간 시세 데이터 연동
- 🔄 사용자별 대화 히스토리
- 🔄 개인화 추천 기능

### 3단계 (예정)

- 🔄 데이터 시각화 (가격 그래프)
- 🔄 지역별 시세 지도
- 🔄 가격 예측 기능
- 🔄 알림 서비스

## 🐛 문제 해결

### 서버 연결 오류

1. 서버가 실행 중인지 확인: `python agriculture_chatbot.py`
2. 포트 5000이 사용 가능한지 확인
3. 환경 변수가 올바르게 설정되었는지 확인

### API 키 오류

1. OpenAI API 키가 유효한지 확인
2. Tavily API 키가 설정되었는지 확인
3. API 사용량 한도를 확인

### MongoDB 연결 오류

1. Atlas 클러스터가 활성 상태인지 확인
2. IP 화이트리스트에 현재 IP가 추가되었는지 확인
3. 연결 문자열이 올바른지 확인

## 📞 지원

문제가 발생하면 다음을 확인해주세요:

1. 로그 확인
2. 환경 변수 설정
3. API 키 유효성
4. 네트워크 연결 상태
