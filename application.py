from flask import Flask, render_template, request
import sys
from common import model, save_chat_log, get_chat_history
from chatbot import Chatbot
from characters import system_role

# duri 인스턴스 생성
duri = Chatbot(
    model=model.basic,
    system_role=system_role,  # instruction이 포함되어 있으므로 따로 안 줘도 됨
    user="사용자",
    assistant="두리쥐"
)

application = Flask(__name__)

@application.route("/")
def chat_app():
    return render_template("chat.html")

@application.route('/chat-api', methods=['POST'])
def chat_api():
    data = request.json
    request_message = data.get('request_message', '')
    mode = data.get('mode', 'qna')  # 프론트에서 전달된 mode 없으면 'qna'
    user_id = data.get('user_id', 'anonymous')  # 사용자 ID 추가

    print("request_message:", request_message)
    print("mode:", mode)
    print("user_id:", user_id)

    # mode가 없거나 지원하지 않는 경우 에러 처리 또는 기본 동작 금지
    if mode not in ['qna', 'faq', 'search', 'price']:
        return {"response_message": "지원하지 않는 모드입니다. 'qna', 'faq', 'search', 'price' 중 선택해주세요."}

    # 모드 설정
    duri.set_mode(mode)

    duri.add_user_message(request_message)
    response = duri.send_request()
    duri.add_response(response)
    response_message = duri.get_response_content()
    duri.handle_token_limit(response)
    duri.clean_context()
    
    # MongoDB에 로그 저장
    save_chat_log(
        user_message=request_message,
        bot_response=response_message,
        mode=mode,
        user_id=user_id
    )
    
    print("response_message:", response_message)
    return {"response_message": response_message}

@application.route('/chat-history', methods=['GET'])
def get_history():
    """사용자의 채팅 히스토리 조회 API"""
    user_id = request.args.get('user_id', 'anonymous')
    limit = int(request.args.get('limit', 10))
    
    history = get_chat_history(user_id=user_id, limit=limit)
    return {"history": history}

@application.route("/test")
def test():
    return "Test page"

if __name__ == "__main__":
    application.run(host='0.0.0.0', port=5000)
