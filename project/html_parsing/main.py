import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
import curl_cffi.requests as requests
import json

def get_html_from_url(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    origin = f"{parsed_url.scheme}://{domain}"

    # 크롬 브라우저와 완벽히 일치하도록 헤더의 대소문자 및 속성 세팅
    headers = {
        "host": domain,
        "connection": "keep-alive",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "accept-encoding": "gzip, deflate, br, zstd", # zstd 추가로 실제 브라우저 모사 강화
        "referer": f"{origin}/", # 홈에서 링크를 타고 온 것처럼 속임
        "sec-ch-ua": '"Not/A)Brand";v="99", "Google Chrome";v="124", "Chromium";v="124"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin", # Referer를 주었으므로 same-origin이 일치함
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    
    try:
        session = requests.Session(impersonate="chrome124")
        
        try:
            pre_headers = headers.copy()
            pre_headers["sec-fetch-site"] = "none"
            pre_headers.pop("referer", None)
            
            # 메인 홈을 먼저 찔러서 세션 쿠키 및 초기 방화벽 검증 통과
            session.get(f"{origin}/", headers=pre_headers, timeout=5)
            # 인간적인 봇 차단 회피를 위한 미세한 Jitter(지연) 추가
            time.sleep(random.uniform(0.3, 0.8))
        except Exception:
            pass 
            
        # 실제 상품 상세 페이지 요청
        response = session.get(url, headers=headers, timeout=15)
        
        # 상태 코드 및 AntiBot 시그니처 검증 
        html_lower = response.text.lower()
        if "cf-browser-verification" in html_lower or "just a moment..." in html_lower:
            print(f"[차단 감지] Cloudflare 챌린지 페이지에 걸렸습니다. (상태 코드: {response.status_code})")
            return None
            
        if response.status_code == 200:
            print(f"[성공] HTML 수집 완료! ({url})")
            return response.text
        else:
            print(f"[실패] HTTP 상태 코드 {response.status_code}")
            return None
            
    except Exception as e:
        print(f"[에러] 네트워크 또는 curl_cffi 구동 오류: {e}")
        return None

def extract_product__info_from_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    product_info = {
        "title": None,
        "price": None,
        "brand": None,
        "image": None,
        "is_available": False
    }
    
    # 1. 상품명 추출 (h1.Product-title)
    title_tag = soup.select_one("h1.Product-title")
    if title_tag:
        product_info["title"] = title_tag.get_text(strip=True)
        
    # 2. 가격 추출 (div.Product-price에서 숫자만 추출)
    price_tag = soup.select_one("div.Product-price")
    if price_tag:
        price_text = price_tag.get_text(strip=True)
        # '120,000원'에서 숫자만 남기기
        price_numeric = re.sub(r'[^\d]', '', price_text)
        product_info["price"] = int(price_numeric) if price_numeric else None

    # 3. 브랜드 추출 (h2.Product-brand 내부의 a 태그)
    brand_tag = soup.select_one("h2.Product-brand a")
    if brand_tag:
        product_info["brand"] = brand_tag.get_text(strip=True)

    # 4. 이미지 추출 (img.Product-image의 src 속성)
    image_tag = soup.select_one("img.Product-image")
    if image_tag:
        product_info["image"] = image_tag.get("src")

    # 5. 판매중 여부 판단
    # '구매하기' 버튼이 존재하고, '품절' 관련 클래스나 텍스트가 없는지 확인
    buy_button = soup.select_one("div.Product-buy")
    if buy_button and "구매하기" in buy_button.get_text():
        # 하단 추천 상품 목록에 있는 'ProductPreview-sold'(품절 표시)와 헷갈리지 않도록 
        # 메인 구매 버튼의 텍스트와 상태로 판별합니다.
        product_info["is_available"] = True

    return product_info

def extract_product__info_with_json_ld(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    product_info = {
        "title": None,
        "price": None,
        "brand": None,
        "image": None,
        "is_available": False
    }
    
    # 1. HTML 내의 모든 JSON-LD 태그 검색
    json_ld_tags = soup.find_all("script", type="application/ld+json")
    
    for tag in json_ld_tags:
        try:
            # 문자열을 파이썬 딕셔너리로 변환
            data = json.loads(tag.string)
            
            # 여러 개의 JSON-LD 중 '@type'이 'Product'인 것만 타겟팅
            if data.get("@type") == "Product":
                
                # 1) 상품명 추출
                product_info["title"] = data.get("name")
                
                # 2) 브랜드 추출 (문자열일 수도 있고, 딕셔너리 구조일 수도 있음)
                brand_data = data.get("brand")
                if isinstance(brand_data, dict):
                    product_info["brand"] = brand_data.get("name")
                elif isinstance(brand_data, str):
                    product_info["brand"] = brand_data
                
                # 3) 이미지 추출 (리스트 형태면 첫 번째 이미지 사용)
                images = data.get("image")
                if isinstance(images, list) and len(images) > 0:
                    product_info["image"] = images[0]
                elif isinstance(images, str):
                    product_info["image"] = images
                
                # 4) 가격 및 판매 여부 추출 (offers 구조 해석)
                offers = data.get("offers")
                if offers:
                    # 가격 추출
                    product_info["price"] = offers.get("price")
                    
                    # 판매중 여부 추출 (InStock 상태인지 확인)
                    availability = offers.get("availability", "")
                    if "InStock" in availability or "in stock" in availability.lower():
                        product_info["is_available"] = True
                        
                # 유효한 Product 데이터를 찾았으므로 루프 종료
                break
                
        except (json.JSONDecodeError, AttributeError, TypeError) as e:
            # JSON 파싱 에러 등이 나면 다음 태그로 넘어감
            continue

    # 검증: 핵심 데이터인 title이 비어있다면 2단계 실패로 판단
    if not product_info["title"]:
        return None

    return product_info

def parse_musinsa_html(html_content):
    if not html_content:
        return None

    soup = BeautifulSoup(html_content, "html.parser")

    # 1. pdp-data 라는 ID를 가진 스크립트 태그를 조준합니다.
    script_tag = soup.find("script", id="pdp-data")

    if not script_tag:
        print("[오류] pdp-data 스크립트 태그를 찾을 수 없습니다.")
        return None

    script_text = script_tag.string

    try:
        # 2. 정규표현식으로 window.__MSS_FE__.product.state = { ... }; 부분을 추출합니다.
        # state = 뒤에 오는 JSON 객체({ ... })만 완벽하게 매칭합니다.
        match = re.search(
            r"window\.__MSS_FE__\.product\.state\s*=\s*(\{.*?\});",
            script_text,
            re.DOTALL,
        )

        if not match:
            print(
                "[오류] 스크립트 내에서 product.state JSON 데이터를 찾지 못했습니다."
            )
            return None

        # 3. 추출한 문자열을 파이썬 딕셔너리로 변환합니다.
        json_data = json.loads(match.group(1))

        # 4. 안전하게 원하는 데이터만 쏙쏙 골라냅니다.
        product_info = {
            "상품번호": json_data.get("goodsNo"),
            "상품명(국문)": json_data.get("goodsNm"),
            "상품명(영문)": json_data.get("goodsNmEng"),
            "브랜드": json_data.get("brandInfo", {}).get("brandName"),
            "카테고리": json_data.get("baseCategoryFullPath"),
            "정가": json_data.get("goodsPrice", {}).get("normalPrice"),
            "할인가": json_data.get("goodsPrice", {}).get("salePrice"),
            "할인율": json_data.get("goodsPrice", {}).get("discountRate"),
            "메인이미지": json_data.get("thumbnailImageUrl"),
            "리뷰수": json_data.get("goodsReview", {}).get("totalCount"),
            "평점": json_data.get("goodsReview", {}).get("satisfactionScore"),
        }

        return product_info

    except json.JSONDecodeError as je:
        print(f"[오류] JSON 파싱 실패: {je}")
        return None
    except Exception as e:
        print(f"[오류] 파싱 중 예상치 못한 에러 발생: {e}")
        return None

if __name__ == "__main__":
    
    #무신사, 후르츠 성공.
    url = "https://fetching.co.kr/product/52615440/V-S1%20%EC%8A%A4%EB%8B%88%EC%BB%A4%EC%A6%88%20%EB%B8%94%EB%9E%99"
    html_content = get_html_from_url(url)
    result = extract_product__info_from_html(html_content)
    print(result)

    #url = "https://www.musinsa.com/products/3513309"
    #html_from_curl_cffi = get_html_from_url(url)
    #result = parse_musinsa_html(html_from_curl_cffi)
    #print(json.dumps(result, indent=4, ensure_ascii=False))