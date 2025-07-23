from product_list import PRODUCT_KEYWORDS
import re

def extract_item_name(user_message):
    """
    사용자 메시지에서 '고추도 팔아?', '망고도 있나요?', '감자 팔아?', '배추는 안팔아?' 등에서 품목명을 추출하는 함수
    - '도'가 있는 경우: '고추도 팔아?' → '고추'
    - '도'가 없는 경우: '감자 팔아?' → '감자'
    - '는/은/이/가' 등 조사 + '안' 부정형도 지원: '배추는 안팔아?' → '배추'
    - 다양한 동사(팔, 있, 판매, 취급, 구입, 구매) 패턴 지원
    """
    # 1. '도 ' 앞에 오는 단어 + 동사(팔/있/판매/취급/구입/구매) 패턴
    m = re.search(r'([가-힣]+)도[ ]?(팔|있|판매|취급|구입|구매)', user_message)
    if m:
        return m.group(1)
    # 2. '는/은/이/가' 등 조사 + '안' 부정형 + 동사 패턴
    # 예: '배추는 안팔아?', '감자는 안있나요?'
    m_neg = re.search(r'([가-힣]+)[는은이가][ ]?안[ ]?(팔|있|판매|취급|구입|구매)', user_message)
    if m_neg:
        return m_neg.group(1)
    # 3. '도' 없이 '품목명+동사' 패턴도 대응
    m2 = re.search(r'([가-힣]+)[ ]?(팔|있|판매|취급|구입|구매)', user_message)
    if m2:
        return m2.group(1)
    return None

def handle_product_check(user_message):
    item = extract_item_name(user_message)
    if not item:
        return {"response": "확인할 품목명을 찾지 못했습니다.", "type": "product_check"}
    # 부정형 질문 여부 확인
    is_negative = bool(re.search(r'안[ ]?(팔|있|판매|취급|구입|구매)', user_message))
    # 정확 일치
    if item in PRODUCT_KEYWORDS:
        if is_negative:
            return {"response": f"아니오, {item}는(은) 판매하고 있습니다.", "type": "product_check"}
        else:
            return {"response": f"네, {item} 판매중입니다.", "type": "product_check"}
    # 부분 일치(포함) 품목 안내
    related = [p for p in PRODUCT_KEYWORDS if item in p]
    if related:
        related_str = ", ".join(related)
        if is_negative:
            return {"response": f"아니오, {item} 관련 품목({related_str})을 판매하고 있습니다.", "type": "product_check"}
        else:
            return {"response": f"네, {item} 관련 품목({related_str})을 판매중입니다.", "type": "product_check"}
    else:
        if is_negative:
            return {"response": f"네, {item}는(은) 판매하지 않습니다.", "type": "product_check"}
        else:
            return {"response": f"아니오, {item}는(은) 판매하지 않습니다.", "type": "product_check"} 