url = 'https://fetching.co.kr/product/58383691/%EC%8A%A4%EB%8B%88%EC%BB%A4%EC%A6%88%20V-S1%20%EC%BB%A8%ED%83%9D%ED%8A%B8%20%EB%B8%94%EB%9E%99'

import asyncio
import nodriver as uc

async def main():
    # 코드스페이스(리눅스)에 설치된 크롬의 기본 경로
    chrome_path = "/usr/bin/google-chrome"
    
    print("[정보] 코드스페이스 환경에서 크롬 가동 중...")
    
    browser = await uc.start(
        browser_executable_path=chrome_path,
        no_sandbox=True, # 리눅스 환경에서 가동하기 위해 sandbox를 꺼줍니다.
        headless=True
    )  
    
    print("[정보] 타겟 페이지 이동 중...")
    page = await browser.get('https://nowsecure.nl')
    
    await asyncio.sleep(5)
    
    html = await page.get_content()
    print(f"[성공] HTML 수집 완료! (길이: {len(html)}자)")
    print()
    
    browser.stop()

if __name__ == '__main__':
    uc.loop().run_until_complete(main())