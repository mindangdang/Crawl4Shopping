import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

def browse_with_selenium(url):
    options = uc.ChromeOptions()
    # 필요한 경우 헤드리스 모드 활성화 (창을 띄우지 않음)
    # options.add_argument('--headless')
    
    # 브라우저 초기화
    driver = uc.Chrome(options=options)
    
    try:
        # 1. 페이지 이동
        driver.get(url)
        # 페이지 로딩 및 WAF 자바스크립트 챌린지 수행 시간 대기
        time.sleep(5) 
        
        # 2. 브라우징 액션 예시 (특정 요소가 나타날 때까지 대기하거나 스크롤)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # 3. 브라우저가 최종 렌더링한 HTML 가져오기
        final_html = driver.page_source
        print(f"[성공] Selenium 브라우징을 통해 {len(final_html)} 바이트의 HTML 확보")
        return final_html
        
    except Exception as e:
        print(f"[에러] Selenium 브라우징 중 오류 발생: {e}")
        return None
    finally:
        driver.quit()