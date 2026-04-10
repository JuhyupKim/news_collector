import sys
import io
import time
sys.stdout.reconfigure(encoding='utf-8')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def get_content_all_urls():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    urls = [
        "https://news.google.com/articles/CBMibkFVX3lxTFBEcXFtaTVGcVc2c0NHdXBtVVpTcG1BUDRRZF92aFJ5Y25yWjgteEh0WkZPRTBRb2Q2NXhfVGVOQTBLbVloSUk2NmhRRDRlVTRlNkp5Q2hyUVNXVHZ2NnN0UjlSTnZuUnA1bk14cGV3?oc=5",
        "https://news.google.com/articles/CBMiT0FVX3lxTE1kWTBldWZ2VGc4R0pJeE5uaW5LY2g2MVdOSHE5Ry0xeUhtX3dWU2N5TzFUWWNMMlhtYTN6Q2MyZzQ0TVlacTVtcVAyd1o4Umc?oc=5"
    ]

    try:
        for i, url in enumerate(urls, 1):
            print(f"\n--- URL {i} ---")
            driver.get(url)
            time.sleep(3) # wait for redirect
            real_url = driver.current_url
            print(f"Real URL: {real_url}")
            
            # extract content
            content = driver.execute_script("return document.body ? document.body.innerText : '';")
            if content:
                content = " ".join(content.split())
                print(f"Content Length: {len(content)}")
                print(f"Preview: {content[:150]}...")
            else:
                print("Content Length: 0")
    finally:
        driver.quit()

get_content_all_urls()
