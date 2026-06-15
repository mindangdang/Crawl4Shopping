import asyncio
import nodriver as uc
from bs4 import BeautifulSoup

async def main():
    # 1. nodriver 브라우저 실행 (자동으로 감지 우회 적용)
    # 처음에는 로그인 과정을 눈으로 확인하기 위해 headless=False를 권장합니다.
    browser = await uc.start(headless=False)
    
    try:
        # 2. 인스타그램 로그인 페이지 이동
        page = await browser.get("https://www.instagram.com/accounts/login/")
        # 페이지 로딩 및 안정화를 위해 잠시 대기
        await page.wait(5)

        # 3. 로그인 정보 입력 및 로그인
        # ※ 인스타그램의 봇 탐지를 피하기 위해 부계정을 사용하세요.
        USER_ID = "YOUR_INSTAGRAM_ID"
        USER_PW = "YOUR_INSTAGRAM_PASSWORD"

        # username 입력창 찾아서 타이핑
        input_id = await page.select('input[name="username"]')
        await input_id.send_keys(USER_ID)
        
        # password 입력창 찾아서 타이핑
        input_pw = await page.select('input[name="password"]')
        await input_pw.send_keys(USER_PW)
        await page.wait(1)

        # 로그인 버튼 클릭 (type="submit" 버튼 찾기)
        login_btn = await page.select('button[type="submit"]')
        await login_btn.click()
        
        print("로그인 버튼을 클릭했습니다. 대시보드가 로드될 때까지 대기합니다...")
        await page.wait(7) # 로그인 완료 후 메인 피드가 뜰 때까지 충분히 대기

        # 4. 크롤링하려는 특정 게시물 URL로 이동
        target_url = "https://www.instagram.com/p/게시물고유코드/"
        await page.get(target_url)
        await page.wait(5) # 게시물 데이터가 완전히 렌더링될 때까지 대기

        # 5. 전체 HTML 소스코드 가져오기
        html_source = await page.get_content()

        # BeautifulSoup으로 가독성 있게 파싱
        soup = BeautifulSoup(html_source, 'html.parser')

        # 6. 결과 파일 저장
        with open("instagram_nodriver.html", "w", encoding="utf-8") as f:
            f.write(soup.prettify())

        print("nodriver를 이용해 성공적으로 HTML을 파일로 저장했습니다!")

    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
        
    finally:
        # 7. 브라우저 종료
        browser.stop()

# 비동기 함수 실행
if __name__ == "__main__":
    uc.loop().run_until_complete(main())