import oracledb
import re
from datetime import datetime, timedelta
import os
from openai import OpenAI
from product_list import PRODUCT_KEYWORDS

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def format_date(date_str):
    y = int(date_str[:4])
    m = int(date_str[4:6])
    d = int(date_str[6:8])
    return f"{y}년 {m}월 {d}일"

def parse_korean_date(text):
    today = datetime.now()
    weekday_map = {
        "월요일": 0, "화요일": 1, "수요일": 2, "목요일": 3, "금요일": 4, "토요일": 5, "일요일": 6
    }
    # 오늘, 어제, 그제
    if "오늘" in text:
        return today.strftime("%Y%m%d")
    if "어제" in text:
        return (today - timedelta(days=1)).strftime("%Y%m%d")
    if "그제" in text:
        return (today - timedelta(days=2)).strftime("%Y%m%d")
    # 이번주 요일 (공백/비공백 모두 지원)
    for k, v in weekday_map.items():
        if f"이번주 {k}" in text or f"이번주{k}" in text:
            this_monday = today - timedelta(days=today.weekday())
            target = this_monday + timedelta(days=v)
            return target.strftime("%Y%m%d")
    # 저번주/지난주 요일 (공백/비공백 모두 지원)
    for k, v in weekday_map.items():
        if f"저번주 {k}" in text or f"지난주 {k}" in text or f"저번주{k}" in text or f"지난주{k}" in text:
            this_monday = today - timedelta(days=today.weekday())
            last_monday = this_monday - timedelta(days=7)
            target = last_monday + timedelta(days=v)
            return target.strftime("%Y%m%d")
    # 저번달/지난달/이전달
    if "저번달" in text or "지난달" in text or "이전달" in text:
        last_month = today.replace(day=1) - timedelta(days=1)
        m = re.search(r"(?:저번달|지난달|이전달)[ ]*([0-9]{1,2})[일]", text)
        if m:
            day = int(m.group(1))
            return f"{last_month.year}{last_month.month:02d}{day:02d}"
        else:
            return f"{last_month.year}{last_month.month:02d}{min(today.day, last_month.day):02d}"
    m = re.search(r"([0-9]{1,2})월[ ]*([0-9]{1,2})일", text)
    if m:
        month, day = m.groups()
        year = today.year
        m2 = re.search(r"([0-9]{4})년", text)
        if m2:
            year = int(m2.group(1))
        return f"{year}{int(month):02d}{int(day):02d}"
    m = re.search(r"(20\d{2})[년\-/\. ]?(\d{1,2})[월\-/\. ]?(\d{1,2})[일]?", text)
    if m:
        y, mo, d = m.groups()
        return f"{int(y):04d}{int(mo):02d}{int(d):02d}"
    return None

def test_oracle_connection():
    conn = oracledb.connect(
        user="YH",
        password="0000",
        dsn="116.36.205.25:1521/XEPDB1" 
    )
    cur = conn.cursor()
    cur.execute("SELECT * FROM TB_PRICE_API_HISTORY")  
    rows = cur.fetchall()
    for row in rows:
        print(row)
    cur.close()
    conn.close()

def get_today_price(product_name):
    """
    주어진 품목명(product_name)에 대해 오늘 날짜의 가격을 오라클 DB에서 조인하여 조회합니다.
    """
    today = datetime.now().strftime('%Y%m%d')
    try:
        conn = oracledb.connect(
            user="YH",
            password="0000",
            dsn="116.36.205.25:1521/XEPDB1"
        )
        cur = conn.cursor()
        sql = """
            SELECT h.price
            FROM tb_price_api_history h
            JOIN tb_code_detail d ON h.low_code_value = d.low_code_value
            WHERE d.low_code_name = :product_name
              AND h.date = :today
        """
        cur.execute(sql, product_name=product_name, today=today)
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return f"오늘 {product_name} 가격은 {row[0]}원입니다."
        else:
            return f"{product_name}의 오늘 가격 정보를 찾을 수 없습니다."
    except Exception as e:
        print(f"[DEBUG] DB 조회 오류: {e}")
        return f"{product_name}의 오늘 가격 정보를 조회하는 중 오류가 발생했습니다."

def extract_date_phrases(text):
    # 날짜 표현 패턴 (ex. 저번주 금요일, 이번주 월요일, 6월 30일, 오늘, 어제, 그제 등)
    date_pattern = r'((?:저번주|지난주|이번주)?\s*(?:[0-9]{4}년)?\s*(?:[0-9]{1,2}월)?\s*(?:[0-9]{1,2}일)?\s*(?:월요일|화요일|수요일|목요일|금요일|토요일|일요일)?|오늘|어제|그제)'
    candidates = re.findall(date_pattern, text)
    candidates = [c.strip() for c in candidates if c.strip() and len(c.strip()) > 1]
    return candidates

def parse_price_query(user_message, conversation_history=None):
    today = datetime.now().strftime('%Y%m%d')
    
    # 사용자 메시지에서 직접 품목 찾기 (LLM 의존성 제거)
    product = None
    message_no_space = user_message.replace(' ', '')
    
    # 1. 공백 제거된 메시지에서 정확히 일치하는 품목 찾기
    for p in PRODUCT_KEYWORDS:
        if p == message_no_space:
            product = p
            break
    
    # 2. 원본 메시지에서 정확히 일치하는 품목 찾기
    if not product:
        for p in PRODUCT_KEYWORDS:
            if p == user_message:
                product = p
                break
    
    # 3. 공백 제거된 메시지에서 정확히 일치하는 품목 찾기 (방울 토마토 → 방울토마토)
    if not product:
        # 가장 긴 품목부터 매칭하여 정확한 품목 우선 선택
        sorted_products = sorted(PRODUCT_KEYWORDS, key=len, reverse=True)
        for p in sorted_products:
            if p in message_no_space:
                # 특별한 경우 처리: 옥수수와 수수 구분
                if p == "수수" and "옥수수" in message_no_space:
                    continue  # 옥수수가 있으면 수수는 건너뛰기
                product = p
                break
    
    # 4. 한글 단어들을 추출해서 정확히 일치하는 품목 찾기
    if not product:
        import re
        korean_words = re.findall(r'[가-힣]+', user_message)
        for word in korean_words:
            for p in PRODUCT_KEYWORDS:
                if p == word:
                    product = p
                    break
            if product:
                break
    
    # 5. 대화 맥락에서 품목 찾기 (새로 추가)
    if not product and conversation_history:
        # 이전 대화에서 언급된 품목 찾기
        for prev_message in reversed(conversation_history):
            if isinstance(prev_message, dict) and prev_message.get('role') == 'user':
                prev_text = prev_message.get('content', '')
                # 이전 메시지에서 품목 찾기
                for p in PRODUCT_KEYWORDS:
                    if p in prev_text:
                        product = p
                        break
                if product:
                    break
    
    # 날짜 후보 추출
    date_candidates = extract_date_phrases(user_message)
    print(f"[DEBUG] 추출된 날짜 후보: {date_candidates}")
    if len(date_candidates) >= 2:
        date1 = parse_korean_date(date_candidates[0])
        date2 = parse_korean_date(date_candidates[1])
    elif len(date_candidates) == 1:
        date1 = parse_korean_date(date_candidates[0])
        date2 = date1
    else:
        date1 = date2 = today
    print(f"[DEBUG] 변환된 date1: {date1}, date2: {date2}")
    # 날짜 파싱 실패 시 None 반환
    if date1 is None or date2 is None:
        return product, None, None, False
    compare = (date1 != date2)
    return product, date1, date2, compare

def handle_price(user_message, conversation_history=None):
    result = parse_price_query(user_message, conversation_history)
    # 구버전 fallback 호환
    if len(result) == 3:
        product, date, compare = result
        date1 = date2 = date
    else:
        product, date1, date2, compare = result
    # 날짜 파싱 실패 안내
    if date1 is None or date2 is None:
        return {
            "response": "날짜를 인식하지 못했습니다. 입력하신 날짜 표현을 다시 확인해 주세요.",
            "type": "price"
        }
    if not product:
        import re
        # 사용자 메시지에서 한글 단어들을 추출
        korean_words = re.findall(r'[가-힣]+', user_message)
        
        # 공백을 제거한 전체 메시지도 확인
        full_message_no_space = user_message.replace(' ', '')
        
        # 1. 먼저 공백 제거된 전체 메시지로 정확히 매칭되는 품목 찾기
        for p in PRODUCT_KEYWORDS:
            if p == full_message_no_space:
                product = p
                break
        
        # 2. 공백 제거된 메시지에서 정확히 일치하는 품목 찾기 (방울 토마토 → 방울토마토)
        if not product:
            # 가장 긴 품목부터 매칭하여 정확한 품목 우선 선택
            sorted_products = sorted(PRODUCT_KEYWORDS, key=len, reverse=True)
            for p in sorted_products:
                if p in full_message_no_space:
                    # 특별한 경우 처리: 옥수수와 수수 구분
                    if p == "수수" and "옥수수" in full_message_no_space:
                        continue  # 옥수수가 있으면 수수는 건너뛰기
                    product = p
                    break
        
        # 3. 여전히 찾지 못했다면 개별 단어로 매칭 시도
        if not product:
            for word in korean_words:
                for p in PRODUCT_KEYWORDS:
                    if p == word:
                        product = p
                        break
                if product:
                    break
        
        # 3. 여전히 찾지 못했다면 취급하지 않는 품목으로 처리
        if not product:
            not_found = korean_words[0] if korean_words else user_message
            
            # 상품을 카테고리별로 분류
            categories = {
                "식량작물": ["쌀","찹쌀","혼합곡","기장","콩","팥","녹두","메밀","고구마","감자","귀리","보리","수수","율무"],
                "채소류": ["배추","양배추","시금치","상추","얼갈이배추","갓","연근","우엉","수박","참외","오이","호박","토마토","딸기","무","당근","열무","건고추","풋고추","붉은고추","피마늘","양파","파","생강","고춧가루","가지","미나리","깻잎","부추","피망","파프리카","멜론","깐마늘(국산)","깐마늘(수입)","브로콜리","양상추","청경채","케일","콩나물","절임배추","쑥","달래","두릅","로메인 상추","취나물","쥬키니호박","청양고추","대파","고사리","쪽파","다발무","겨울 배추","알배기배추","방울토마토"],
                "특용작물": ["참깨","들깨","땅콩","느타리버섯","팽이버섯","새송이버섯","호두","아몬드","양송이버섯","표고버섯","더덕"],
                "과일류": ["바나나","참다래","파인애플","오렌지","자몽","레몬","체리","건포도","건블루베리","망고","블루베리","아보카도","레드향","매실","무화과","복분자","샤인머스켓","곶감","골드키위","사과","배","복숭아","포도","감귤","단감"]
            }
            
            response = f"{not_found}는 사이트에서 취급하지 않습니다.\n저희 사이트에서 취급하는 주요 상품 목록입니다:\n\n"
            
            for category, items in categories.items():
                response += f"📦 {category} ({len(items)}종)\n"
                response += f"   {', '.join(items)}"
                response += "\n\n"
            
            response += f"총 {len(PRODUCT_KEYWORDS)}가지의 농산물을 취급하고 있습니다.\n"
            response += "특정 상품에 대한 자세한 정보가 필요하시면 언제든 말씀해 주세요!"
            
            return {
                "response": response,
                "type": "price"
            }
    # 날짜 비교 로직 개선
    if compare:
        # 날짜를 datetime 객체로 변환
        try:
            d1 = datetime.strptime(date1, "%Y%m%d")
            d2 = datetime.strptime(date2, "%Y%m%d")
        except Exception as e:
            return {"response": f"날짜 형식이 올바르지 않습니다. (date1: {date1}, date2: {date2})", "type": "price"}
        # 두 날짜가 같으면 변동 없음 안내
        if d1 == d2:
            v = get_avg_unit_price(product, date1)
            if v is None:
                return {"response": f"{format_date(date1)} 기준 {product} 가격 정보를 찾을 수 없습니다.", "type": "price"}
            return {"response": f"{format_date(date1)} 기준 {product} 평균가는 {v:.2f}원입니다. (동일 날짜 비교, 변동 없음)", "type": "price"}
        # 과거, 최근 순서로 정렬
        if d1 > d2:
            d1, d2 = d2, d1
            date1, date2 = date2, date1
        v1 = get_avg_unit_price(product, date1)
        v2 = get_avg_unit_price(product, date2)
        if v1 is None or v2 is None:
            return {"response": f"{product}의 가격 정보가 없는 날짜가 있어 비교 정보를 출력 할 수 없습니다.", "type": "price"}
        diff = v2 - v1
        if diff > 0:
            updown = "올랐습니다."
        elif diff < 0:
            updown = "내렸습니다."
        else:
            updown = "변동이 없습니다."
        return {"response": f"{format_date(date1)} 기준 {product} 평균가는 {v1:.2f}원, {format_date(date2)} 기준 {product} 평균가는 {v2:.2f}원으로 {abs(diff):.2f}원 {updown}\n(해당 날짜의 모든 데이터 평균가 기준)", "type": "price"}
    else:
        price = get_price(product, date1)
        if price is None and date1 == datetime.now().strftime('%Y%m%d'):
            # 오늘 데이터가 없으면 어제 데이터 안내
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
            price_yesterday = get_price(product, yesterday)
            if price_yesterday is not None:
                return {"response": f"시세 데이터는 00시 자정에 업데이트 되므로 최신 데이터는 어제 날짜 데이터입니다.\n{format_date(yesterday)}(어제) 기준 {product} {price_yesterday}", "type": "price"}
            else:
                # 오늘/어제 모두 없으면 최근 데이터 안내
                recent_date, price_recent = get_latest_price(product)
                if price_recent is not None:
                    return {"response": f"{format_date(date1)} {product} 가격 정보를 찾을 수 없습니다.\n가장 최근의 {product} 가격 정보 업데이트일은 {format_date(recent_date)}입니다.\n{format_date(recent_date)} 기준 {product} {price_recent}", "type": "price"}
                else:
                    return {"response": f"2015년부터 현재까지 {product} 가격 정보가 한 건도 없습니다.", "type": "price"}
        if price is None:
            return {"response": f"{format_date(date1)} 기준 {product} 가격 정보를 찾을 수 없습니다.", "type": "price"}
        return {"response": f"{price}", "type": "price"}

def get_price(product_name, date):
    # 오라클 DB에서 해당 날짜, 품목 kg당 가격 조회
    try:
        conn = oracledb.connect(
            user="YH",
            password="0000",
            dsn="116.36.205.25:1521/XEPDB1"
        )
        cur = conn.cursor()
        sql = """
            SELECT h.RECORDED_UNIT_PRICE
            FROM tb_price_api_history h
            JOIN tb_code_detail d ON h.LOW_CODE_VALUE = d.LOW_CODE_VALUE
            WHERE d.LOW_CODE_NAME = :product_name
              AND h.RECORDED_DATE = TO_DATE(:p_date, 'YYYYMMDD')
        """
        cur.execute(sql, product_name=product_name, p_date=date)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        if rows:
            prices = [row[0] for row in rows if row[0] is not None]
            if not prices:
                return None
            max_price = max(prices)
            min_price = min(prices)
            date_str = format_date(date)
            if max_price == min_price:
                return f"{date_str} 기준 {product_name} 가격은 {max_price}원입니다. (kg당 가격)"
            else:
                return f"{date_str} 기준 {product_name} 최고가는 {max_price}원, 최저가는 {min_price}원입니다. (kg당 가격)\n(가격 차이가 많이 나는 경우 원산지가 달라 생기는 차이 일 수 있습니다.)"
        else:
            return None
    except Exception as e:
        print(f"[DEBUG] DB 조회 오류: {e}")
        return None

def get_latest_price(product_name):
    # DB에서 해당 품목의 가장 최근 날짜와 kg당 가격 정보 반환 (YYYYMMDD, price 문자열)
    try:
        conn = oracledb.connect(
            user="YH",
            password="0000",
            dsn="116.36.205.25:1521/XEPDB1"
        )
        cur = conn.cursor()
        sql = """
            SELECT TO_CHAR(h.RECORDED_DATE, 'YYYYMMDD'), h.RECORDED_UNIT_PRICE
            FROM tb_price_api_history h
            JOIN tb_code_detail d ON h.LOW_CODE_VALUE = d.LOW_CODE_VALUE
            WHERE d.LOW_CODE_NAME = :product_name
            ORDER BY h.RECORDED_DATE DESC
        """
        cur.execute(sql, product_name=product_name)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        if rows:
            # 가장 최근 날짜의 가격 정보(여러 행일 경우 최고/최저가 포맷 재활용)
            recent_date = rows[0][0]
            prices = [row[1] for row in rows if row[0] == recent_date and row[1] is not None]
            if not prices:
                return recent_date, None
            max_price = max(prices)
            min_price = min(prices)
            if max_price == min_price:
                return recent_date, f"가격은 {max_price}원입니다. (kg당 가격)"
            else:
                return recent_date, f"최고가는 {max_price}원, 최저가는 {min_price}원입니다. (kg당 가격)\n(가격 차이가 많이 나는 경우 원산지가 달라 생기는 차이 일 수 있습니다.)"
        else:
            return None, None
    except Exception as e:
        print(f"[DEBUG] DB 조회 오류(최신): {e}")
        return None, None

def get_avg_unit_price(product_name, date):
    try:
        conn = oracledb.connect(
            user="YH",
            password="0000",
            dsn="116.36.205.25:1521/XEPDB1"
        )
        cur = conn.cursor()
        sql = """
            SELECT h.RECORDED_UNIT_PRICE
            FROM tb_price_api_history h
            JOIN tb_code_detail d ON h.LOW_CODE_VALUE = d.LOW_CODE_VALUE
            WHERE d.LOW_CODE_NAME = :product_name
              AND h.RECORDED_DATE = TO_DATE(:p_date, 'YYYYMMDD')
        """
        cur.execute(sql, product_name=product_name, p_date=date)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        prices = [row[0] for row in rows if row[0] is not None]
        if prices:
            return sum(prices) / len(prices)
        else:
            return None
    except Exception as e:
        print(f"[DEBUG] DB 조회 오류(평균가): {e}")
        return None