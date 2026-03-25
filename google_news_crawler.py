import requests
import feedparser
import time
import datetime
from deep_translator import GoogleTranslator
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import numpy as np

def translate_text(text):
    if not text: return ""
    try:
        return GoogleTranslator(source='auto', target='ko').translate(text[:4500])
    except: return text

def get_article_content(driver, url):
    """
    Selenium을 사용하여 구글 뉴스 리다이렉트를 처리하고 본문을 추출합니다.
    """
    try:
        try:
            driver.get(url)
        except TimeoutException:
            pass # 페이지 로드가 지연되더라도 이미 렌더링된 본문 텍스트는 추출 시도
            
        time.sleep(3) # 리다이렉트 대기
        
        content = driver.execute_script("return document.body ? document.body.innerText : '';")
        if content:
            content = " ".join(content.split())
            content_summary = content[:200]
            return content, content_summary
        return "", ""
    except Exception as e:
        print(f"  [GoogleNews] Detail Parsing Error: {e}")
        return "", ""

def get_google_news_data(days_to_scrape=1):
    TARGET_GROUPS = [
        {
            "name": "China Competitors",
            "targets": ["海尔", "美的", "海信集團"],
            "url_template": 'https://news.google.com/rss/search?q="{query}"%20when%3A{period}-ETF%2C%20-专利&hl=zh-CN&gl=CN&ceid=CN%3Azh-Hans'
        },
        {
            "name": "Global Competitors",
            "targets": ["Electrolux", "GE Appliance", "Whirlpool", "Bosch Appliance"],
            "url_template": 'https://news.google.com/rss/search?q="{query}"%20when%3A{period}&hl=en-US&gl=US&ceid=US%3Aen'
        },
        {
            "name": "Logistics Keywords",
            "targets": ["수에즈 운하", "파나마 운하", "홍해", "SCFI"],
            "url_template": 'https://news.google.com/rss/search?q="{query}"%20when%3A{period}&hl=ko&gl=KR&ceid=KR%3Ako'
        }
    ]

    search_period = f"{days_to_scrape}d"
    results = []

    print(">>> 구글 뉴스 크롤링 시작")
    print(f"※ 최근 {search_period} 뉴스를 검색합니다.")

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(15)

    try:
        for group in TARGET_GROUPS:
            print(f"\n--- Group: {group['name']} ---")
            for target in group['targets']:
                target_url = group['url_template'].format(query=target, period=search_period)
                print(f"Searching: {target}")
                
                group_results = crawl_google_rss_url(driver, target_url, target)
                results.extend(group_results)
                
                if group_results:
                    print(f"  -> {len(group_results)}건 수집 완료")
                else:
                    print("  -> 수집된 뉴스 없음")
    finally:
        driver.quit()

    print("\n>>> 모든 구글 뉴스 크롤링 완료")
    return results

def crawl_google_rss_url(driver, news_url, competitor, max_retries=3):
    retries = 0
    while retries < max_retries:
        try:
            res = requests.get(news_url, timeout=(5, 10))
            if res.status_code == 200:
                datas = feedparser.parse(res.text).entries
                parsed_data = parse_rss_entries(driver, competitor, datas)
                time.sleep(abs(np.random.randn() * 2)) 
                return parsed_data
            else:
                print(f"  [Error] Status Code: {res.status_code}")
                if 400 <= res.status_code < 500:
                    break
        except requests.exceptions.Timeout:
            print(f"  [Timeout] 요청 시간 초과 (시도 {retries+1}/{max_retries})")
        except requests.exceptions.RequestException as err:
            print(f"  [Connection Error] {err} (시도 {retries+1}/{max_retries})")
        except Exception as e:
            print(f"  [Unknown Error] {e}")

        retries += 1
        wait_time = 2 ** retries
        time.sleep(wait_time)
        print(f"  Retrying in {wait_time} seconds...")

    print(f"  [Fail] '{competitor}' 크롤링 최종 실패")
    return []

def parse_rss_entries(driver, competitor, datas):
    enveloped_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    parsed_results = []

    for data in datas:
        try:
            # RSS 항목 파싱
            title = translate_text(data.title)
            provider = data.source.title if hasattr(data, 'source') and hasattr(data.source, 'title') else "Google News"
            
            provider_link_page = data.link
            provider_link_page = provider_link_page.replace("/rss/", "/")
            
            try:
                datetime_object = datetime.datetime.strptime(data.published, "%a, %d %b %Y %H:%M:%S %Z")
            except:
                datetime_object = datetime.datetime.now()
            
            year = str(datetime_object.year)
            month = str(datetime_object.month)
            week = str(datetime_object.isocalendar()[1])
            date_str = datetime_object.strftime('%Y-%m-%d %H:%M:%S')

            # 본문 추출
            content, content_summary = get_article_content(driver, provider_link_page)
            if not content:
                content = data.title # 본문이 없으면 제목으로 대체

            # 결과 리스트에 딕셔너리 추가 (기존 프로젝트 포맷 맞춤)
            parsed_results.append({
                'title': title,
                'content': translate_text(content),
                'enveloped_at': enveloped_at,
                'date': date_str,
                'provider': provider,
                'category_main': '',
                'category_sub': '',
                'reporter': '',
                'provider_link_page': provider_link_page,
                'useful': -1,
                'strategy_agenda': -1,
                'content_summary': translate_text(content_summary),
                'category1': competitor,
                'category2': '',
                'YEAR': year,
                'MONTH': month,
                'WEEK': week
            })
        except Exception as e:
            print(f"  [RSS Parse Error] {e}")
            
    return parsed_results

if __name__ == "__main__":
    import argparse
    import csv
    import os
    parser = argparse.ArgumentParser(description="Run Google News crawler independently.")
    parser.add_argument("--days", type=int, default=1, help="Number of days to scrape (DATE_THRESHOLD)")
    args = parser.parse_args()
    
    print(f"구글 뉴스 크롤링을 시작합니다. (과거 {args.days}일)")
    data = get_google_news_data(days_to_scrape=args.days)
    
    if data:
        os.makedirs("output", exist_ok=True)
        today_str = datetime.now().strftime('%Y%m%d')
        filename = f"output/{today_str}_googlenews.csv"
        keys = data[0].keys()
        with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(data)
        print(f"✅ 수집 완료: 총 {len(data)}건 -> {filename}")
    else:
        print("수집된 기사가 없습니다.")
