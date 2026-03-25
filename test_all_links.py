import sys
import io
import time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from deep_translator import GoogleTranslator

def translate_text(text):
    if not text: return ""
    try:
        # 4500자 제한, 초과분은 잘라서라도 번역
        return GoogleTranslator(source='auto', target='ko').translate(text[:4500])
    except Exception as e:
        print(f"Translation error: {e}")
        return text

def test_links():
    urls = [
        "https://news.cheaa.com/2026/0325/653850.shtml",
        "https://news.google.com/articles/CBMipwFBVV95cUxQSnRqNEIwMG43RlducGRkYUdJUXZHM2QtMTg4TW1DdlV0V28wUjVhU0lfNlVNdEhZRjh6SWpLZFlFazlTTmh2ckwyQzVXb1llcUtKRDF5WHc5YTRnQl9HRUZYeUFiOUhqYm1pdXRUVjV1N19LN1F2VlR4b1JCeGU4d3FWTlhnVlZpRzJwSDEzYTZDWFJHdThuNnNLcG1qd1p3ZXNPXzUyaw?oc=5",
        "https://news.google.com/articles/CBMiV0FVX3lxTE1telZFb3VDY241SHRjdGlPNDlZb0c1YUxTcEs5TDNPdUczZy12OWJ2UjR4dWpRSTRFcGc1a3lrZVRGRzU4ZkFnTXF0a1QtUV84ZWIzcVBoMA?oc=5",
        "https://news.google.com/articles/CBMiV0FVX3lxTE5YNXVqMDlqNnl2ZmZ1cGZieEQxT1Z5TVhCTmpMcTBDeUsydGFSRDEyMDl0NzIxWU1mNE1kZkQ0OWg4REgyRWI0d01sYklmNXFwMDBNWTBtRQ?oc=5",
        "https://news.google.com/articles/CBMiVEFVX3lxTFBZdElfaVNzZDRxYXMtQVRTUVhIRDZHc3B5UWtXRUtTSjBRZ2dWdkRDZ2l2MkN0MG9aVllrVldic09yQmxJNDdwVjVZSkRWM19VU2dWTQ?oc=5",
        "https://news.google.com/articles/CBMiUEFVX3lxTE04M2VBZWktajlpNHd3dWZ0aDdFVUxxTV8xZV92U1VLOENHaThMOWVMeV91QWZVNWlQTlNzUFNvNzdRNHg0TEFiR0l2dEZZLTRB?oc=5",
        "http://news.zdwang.com/a/202603/2498373.html",
        "https://news.google.com/articles/CBMibkFVX3lxTE04eW1OOGVLQTdXQjdrWV9nUHRHbDdJUkRtOFhIWWE4TkRzNHNaV0h1X2VPUGJ4dHhaYU5rdnNKdlB1NU84d0xqOFI5a05hMERKR2t2N2l3VzVSQWVXZUZqWEVkQUtiblJZRDQ2c3BB?oc=5",
        "https://news.google.com/articles/CBMiaEFVX3lxTE5Iaktyb0p4bnZNYW9pMUFTaXFEUnVsY014OVc3ZnhUdjg2RTk3aDdrd0NIMjJYOWRzeFFxNGZYSWgxZlduc29rMEtldnlUWkVGdGtaS0Exd2x4dlhEQnFGU01iRzBRS3Vt?oc=5",
        "http://news.zdwang.com/a/202603/2498372.html",
        "http://news.zdwang.com/a/202603/2598417.html"
    ]

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(15)
    
    try:
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] Testing URL: {url}", flush=True)
            try:
                driver.get(url)
                time.sleep(3) # Wait for redirect and loading
                
                real_url = driver.current_url
                print(f"  -> Real URL: {real_url}")
                
                content = driver.execute_script("return document.body ? document.body.innerText : '';")
                if content:
                    content = " ".join(content.split()) # compress whitespace
                    print(f"  -> Extract Length: {len(content)}")
                    
                    # Test translation on the first 100 characters
                    preview = content[:150]
                    translated_preview = translate_text(preview)
                    print(f"  -> Original Preview: {preview}")
                    print(f"  -> Translated Preview: {translated_preview}")
                else:
                    print(f"  -> Extract Length: 0", flush=True)
            except Exception as e:
                print(f"  -> Error resolving {url}: {e}", flush=True)
    finally:
        driver.quit()

if __name__ == "__main__":
    test_links()
