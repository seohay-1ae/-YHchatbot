from langchain_tavily.tavily_search import TavilySearch
import os
from dotenv import load_dotenv
import math
from common import client, makeup_response, gpt_num_tokens, today, currTime

load_dotenv()

class Chatbot:
    def __init__(self, model, system_role, instruction=None, **kwargs):
        # 오늘 날짜와 현재 시각
        self.today = today()  # 예: "2025년 07월 08일"
        self.current_time = currTime()  # 예: "2025.07.08 01:45:22"

        # 기본 시스템 역할 메시지 (모든 모드에 공통)
        self.system_role_template = (
                system_role
                + (instruction or "")
                + f"\n[참고: 오늘 날짜는 {self.today} 입니다. 현재 시각은 {self.current_time} 입니다.]"
        )

        # 모드별 context 저장용 딕셔너리
        self.contexts = {}

        self.model = model
        self.instruction = instruction
        self.max_token_size = 16 * 1024
        self.kwargs = kwargs
        self.user = kwargs.get("user", "user")
        self.assistant = kwargs.get("assistant", "assistant")

        # 기본 모드: qna (기본 질문응답 모드)
        self.mode = kwargs.get("mode", "qna")

        # TavilySearch 초기화 (검색 시 사용)
        self.tavily = TavilySearch(
            tavily_api_key=os.getenv("TAVILY_API_KEY"),
            k=3
        )

    def _get_context(self):
        # 현재 모드 context가 없으면 초기화
        if self.mode not in self.contexts:
            self.contexts[self.mode] = [{"role": "system", "content": self.system_role_template}]
        return self.contexts[self.mode]

    def set_mode(self, mode):
        # 허용된 모드만 설정 가능
        if mode not in ["qna", "faq", "search", "price"]:
            raise ValueError("지원하지 않는 모드입니다.")
        self.mode = mode  # 무조건 갱신

    def add_user_message(self, user_message):
        context = self._get_context()
        user_message_with_time = f"{user_message}\n(오늘 날짜: {self.today}, 현재 시각: {self.current_time})"
        context.append({"role": "user", "content": user_message_with_time})

        if self.mode == "search":
            try:
                data = self.tavily.run(user_message)
                print(f"[🔍 Tavily 검색 결과] {data}")

                summary = data.get("answer")
                summary = summary.strip() if summary else None

                search_results = data.get("results", [])[:3]

                if search_results:
                    # 링크 포맷팅 (최대 2개만)
                    links = "\n".join(
                        f"- [{item['title']}]({item['url']})" for item in search_results[:2]
                    )
                else:
                    links = ""

                # 결과 메시지 생성 (두리쥐 말투)
                if summary:
                    response_message = f"""고객님! 찾아봤더니 이런 정보가 있더라구요!

        📌 {summary}
        자세한 내용은 여기서 볼 수 있어요:
        {links}

        C • ᚐ • Ɔ • ᚐ • Ɔ ᡣ𐭩"""
                elif links:
                    response_message = f"""고객님! 직접 찾아봤는데 이런 정보들이 나왔어요:

        {links}

        C • ᚐ • Ɔ • ᚐ • Ɔ ᡣ𐭩"""
                else:
                    response_message = f"""죄송하지만, 고객님! 관련된 정보를 못 찾았어요.
        다른 질문 있으시면 또 도와드릴게요!

        C • ᚐ • Ɔ • ᚐ • Ɔ ᡣ𐭩"""

                return response_message

            except Exception as e:
                print(f"[Search 처리 오류]: {e}")
                return "죄송해요, 고객님! 검색 중 문제가 발생했어요.\n잠시 뒤 다시 시도해주세요.\nC • ᚐ • Ɔ • ᚐ • Ɔ ᡣ𐭩"

        elif self.mode == "faq":
            answer = self.get_faq_answer(user_message)
            context.append({"role": "system", "content": f"[FAQ 답변]\n{answer}"})
            context.append({"role": "assistant", "content": f"고객님! 알려드릴게요!\n{answer}\nC • ᚐ • Ɔ • ᚐ • Ɔ ᡣ𐭩"})

        elif self.mode == "price":
            price_info = self.get_price_info(user_message)
            context.append({"role": "system", "content": f"[시세 정보]\n{price_info}"})
            context.append({"role": "assistant", "content": f"고객님! 지금 가격 정보예요!\n{price_info}\nC • ᚐ • Ɔ • ᚐ • Ɔ ᡣ𐭩"})

        # qna는 context만 쌓고 나중에 LLM 호출
        else:
            # qna 등 기본 모드는 별도 사전 처리 없음
            pass

    def _send_request(self):
        context = self._get_context()

        # 토큰 제한 초과 시 마지막 메시지 제거 후 오류 메시지 반환
        if gpt_num_tokens(context) > self.max_token_size:
            context.pop()
            return makeup_response("이해하기 어려워요! 메시지를 조금 짧게 보내주세요!")

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=context,
                temperature=0.5,
                top_p=1,
                max_tokens=256,
                frequency_penalty=0,
                presence_penalty=0
            ).model_dump()
        except Exception as e:
            print(f"Exception 오류({type(e)}) 발생:{e}")
            return makeup_response("[두리쥐가 혼란에 빠졌습니다! 잠시 뒤 이용해주세요]")

        return response

    def handle_token_limit(self, response):
        # 토큰 사용량이 제한을 초과하면 context 일부 삭제해서 관리
        try:
            if response.get('usage', {}).get('total_tokens', 0) > self.max_token_size:
                remove_size = math.ceil(len(self._get_context()) / 10)
                context = self._get_context()
                # 초기 시스템 메시지는 유지하며 일부 메시지 삭제
                self.contexts[self.mode] = [context[0]] + context[remove_size + 1:]
        except Exception as e:
            print(f"handle_token_limit exception: {e}")

    def clean_context(self):
        # 사용자 메시지에서 instruction 이후 내용 제거 (필요시 호출)
        context = self._get_context()
        for idx in reversed(range(len(context))):
            if context[idx]["role"] == "user":
                # 예: instruction 이후 내용 삭제
                context[idx]["content"] = context[idx]["content"].split("instruction:\n")[0].strip()
                break

    def send_request(self):
        context = self._get_context()

        if self.mode == "search":
            # 🔍 Tavily 결과로 직접 메시지 만들기
            summary = None
            links = []

            for msg in context:
                if msg["role"] == "system":
                    if msg["content"].startswith("[요약된 검색 답변]"):
                        summary = msg["content"].replace("[요약된 검색 답변]", "").strip()
                    elif msg["content"].startswith("[인터넷 검색 결과]"):
                        lines = msg["content"].split("\n")[1:]
                        links = [line.split(":")[0] for line in lines[:2]]

            if summary:
                return makeup_response(
                    f"""고객님! 찾아봤더니 이런 정보가 있더라구요!  
    📌 {summary}  
    자세한 내용은 아래에서 볼 수 있어요:  
    """ + "\n".join(f"- {link}" for link in links) + "\n\nC • ᚐ • Ɔ • ᚐ • Ɔ ᡣ𐭩", "search"
                )
            elif links:
                return makeup_response(
                    f"""고객님! 아래 정보들을 참고해보세요:  
    """ + "\n".join(f"- {link}" for link in links) + "\n\nC • ᚐ • Ɔ • ᚐ • Ɔ ᡣ𐭩", "search"
                )
            else:
                return makeup_response(
                    "죄송하지만, 고객님! 관련된 정보를 못 찾았어요. 다른 질문도 언제든지 환영이에요!\nC • ᚐ • Ɔ • ᚐ • Ɔ ᡣ𐭩",
                    "search"
                )

        if self.mode == "price":
            # price 모드는 AI 호출 없이 시세 정보 바로 리턴
            price_info = None
            for msg in context:
                if msg["role"] == "system" and msg["content"].startswith("[시세 정보]"):
                    price_info = msg["content"]
                    break
            if price_info:
                return makeup_response(price_info, "price")

        if self.mode == "faq":
            # FAQ 모드도 AI 호출 없이 사전 정의 답변을 리턴
            for msg in context:
                if msg["role"] == "system" and msg["content"].startswith("[FAQ 답변]"):
                    faq_answer = msg["content"]
                    return makeup_response(faq_answer, "faq")

            # 나머지 모드는 기존대로 AI 호출
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=context,
                temperature=0.5,
                top_p=1,
                max_tokens=256,
                frequency_penalty=0,
                presence_penalty=0
            ).model_dump()
        except Exception as e:
            print(f"Exception 오류({type(e)}) 발생:{e}")
            return makeup_response("[두리쥐가 혼란에 빠졌습니다! 잠시 뒤 이용해주세요]")

        return response

    def add_response(self, response):
        context = self._get_context()
        context.append({
            "role": response['choices'][0]['message']["role"],
            "content": response['choices'][0]['message']["content"],
        })

    def get_response_content(self):
        context = self._get_context()
        return context[-1]['content']

    def get_faq_answer(self, question):
        # 간단한 FAQ 사전 정의
        faq_db = {
            "반품": "제품 수령 후 7일 이내 반품 가능합니다.",
            "배송": "배송은 2~3일 소요됩니다.",
            "환불": "환불은 영업일 기준 3일 이내 처리됩니다.",
            # --- 사용자 요청 추가 FAQ ---
            "가입 승인": "회원 가입 승인까지 영업일 기준 1~2일 소요됩니다. 승인 완료 시 문자 메세지를 보내드립니다.",
            "상품 등록 제한": "등록이 제한되는 상품은 다음과 같습니다.\n- 유통기한이 지난 농산물\n- 가공식품, 반찬류, 탕류 등\n- 씨앗, 묘목, 농약, 비료\n- 고기, 생선, 계란, 유제품\n- 그 외 농산물에 해당하지 않는 기타 상품",
            "판매자 구매": "판매자로 가입하신 경우, 상품 구매를 원하시면 구매자로 따로 가입하셔야 합니다.",
            "상품 등록 유의사항": "상품명은 중복 없이 명확하게 작성해 주세요.\n상품 이미지는 1장 이상 등록해야 하며, 실제 상품과 동일해야 합니다.\n상품 단위, 규격, 수량, 가격을 정확히 입력해 주세요.\n유통기한이 지난 상품이나 플랫폼에서 금지한 품목은 등록할 수 없습니다.\n욕설, 비방, 광고성 문구, 외부 링크는 작성할 수 없습니다.\n개인정보(연락처, 계좌번호 등)를 상품 설명에 포함하지 마세요.\n도배, 중복 등록된 상품은 관리자에 의해 삭제될 수 있습니다.\n타인의 이미지나 글을 무단으로 사용하는 경우 제재를 받을 수 있습니다.\n등록된 상품 정보가 사실과 다를 경우, 거래 제한 및 판매 중지 조치가 있을 수 있습니다.\n예약상품의 경우 예약금의 비율은 기본 50%입니다."
        }
        for keyword, answer in faq_db.items():
            if keyword in question:
                return answer
        return "죄송합니다. 해당 질문은 등록되어 있지 않습니다."

    def get_price_info(self, query):
        # 시세 정보 모킹 예시
        if "금" in query:
            return "오늘 금 시세는 g당 87,500원입니다."
        elif "비트코인" in query:
            return "비트코인 현재가는 57,200,000원입니다."
        return "요청하신 상품의 시세 정보를 찾을 수 없습니다."
