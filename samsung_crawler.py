import time
import json
import pandas as pd
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

class SamsungCrawler:
    def __init__(self):
        self.base_url = "https://news.samsung.com/kr/latest"
        self.driver = None

    def _setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def _format_datetime(self, date_str):
        """
        어떤 형식의 날짜 문자열이 들어와도 %Y-%m-%d %H:%M:%S 로 변환하는 유틸리티
        """
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 1. 슬래시(/)를 하이픈(-)으로 통일
        clean_str = date_str.replace('/', '-')
        
        try:
            # 2. 시분초까지 포함된 경우 (ISO 8601 등)
            if 'T' in clean_str:
                dt = datetime.fromisoformat(clean_str)
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # 3. 날짜만 있는 경우 (2026-01-07 등)
            if len(clean_str) <= 10:
                return f"{clean_str} 00:00:00"
            
            # 4. 기타 형식 시도
            return datetime.strptime(clean_str, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
        except:
            # 실패 시 현재 시각 반환 (에러 방지)
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def get_detail_data(self, url):
        """상세 페이지 데이터 추출 (날짜 처리 강화)"""
        self.driver.get(url)
        time.sleep(1.5)
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        
        raw_date = None

        # 1. JSON-LD 우선 탐색
        try:
            json_ld_tags = soup.find_all('script', type='application/ld+json')
            for tag in json_ld_tags:
                data = json.loads(tag.string)
                item = data[0] if isinstance(data, list) else data
                if 'datePublished' in item:
                    raw_date = item['datePublished']
                    break
        except: pass

        # 2. 실패 시 화면 상의 날짜 텍스트 가져오기
        if not raw_date:
            date_tag = soup.select_one('p.single-date')
            raw_date = date_tag.get_text(strip=True) if date_tag else None

        # 3. 통합 포맷터로 변환 (중요!)
        formatted_date = self._format_datetime(raw_date)

        # 본문 및 요약 추출
        content_div = soup.select_one('div.single_contents')
        content = ""
        if content_div:
            for tag in content_div.find_all(['p', 'h4']):
                content += tag.get_text(" ", strip=True) + "\n"
        
        ai_summary_tag = soup.select_one('#ai-summary')
        content_summary = ai_summary_tag.get('data-summary', '') if ai_summary_tag else ""
        
        categories = []
        for item in soup.select('.footer_category_box .category'):
            p, n = item.select_one('.parent_category_name'), item.select_one('.now')
            if p and n: categories.append(f"{p.get_text(strip=True)}>{n.get_text(strip=True)}")
        
        return {
            "date": formatted_date,
            "content": content.strip(),
            "content_summary": content_summary,
            "category1": categories[0] if len(categories) > 0 else "",
            "category2": categories[1] if len(categories) > 1 else ""
        }

    def run(self, days_to_scrape=1, max_items=None, global_seen_links=None):
        if max_items is not None and max_items <= 0:
            max_items = None
            
        self._setup_driver()
        cutoff_date = (datetime.now() - timedelta(days=days_to_scrape)).date()
        results = []
        seen_links = set(global_seen_links) if global_seen_links else set()
        page = 1
        keep_going = True

        try:
            while keep_going:
                if max_items is not None and len(results) >= max_items:
                    break
                    
                self.driver.get(f"{self.base_url}/page/{page}")
                time.sleep(2)
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                items = soup.select('ul.category_box > li')
                if not items: break

                for item in items:
                    if max_items is not None and len(results) >= max_items:
                        keep_going = False
                        break
                        
                    # 목록 날짜는 YYYY/MM/DD 형식이므로 슬래시 기준으로 파싱
                    list_date_str = item.select_one('.category_data').get_text(strip=True)
                    list_date_obj = datetime.strptime(list_date_str, '%Y/%m/%d').date()

                    if list_date_obj < cutoff_date:
                        keep_going = False
                        break

                    title = item.select_one('.category_title').get_text(strip=True)
                    link = item.select_one('a.category_item')['href']
                    cat_sub = item.select_one('.category_tag').get_text(strip=True) if item.select_one('.category_tag') else ""

                    if link in seen_links: continue
                    seen_links.add(link)

                    try:
                        detail = self.get_detail_data(link)
                        
                        # detail['date']는 이제 무조건 %Y-%m-%d %H:%M:%S 형식임
                        dt_obj = datetime.strptime(detail['date'], '%Y-%m-%d %H:%M:%S')
    
                        cat_main = detail['category1'].split('>')[0] if '>' in detail['category1'] else detail['category1']
                        cat_sub = detail['category1'].split('>')[1] if '>' in detail['category1'] else ''
                        
                        results.append({
                            "title": title,
                            "content": detail['content'],
                            "enveloped_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            "date": str(detail['date']),
                            "provider": "Samsung Newsroom",
                            "category_main": cat_main.strip(),
                            "category_sub": cat_sub.strip(),
                            "reporter": "",
                            "provider_link_page": link,
                            "useful": 1, "strategy_agenda": 1,
                            "content_summary": detail['content_summary'],
                            "category1": "Samsung Newsroom",
                            "category2": detail['category1'],
                            "YEAR": dt_obj.year, "MONTH": dt_obj.month, "WEEK": dt_obj.isocalendar()[1]
                        })
                    except Exception as ex:
                        print(f"  [Samsung] Detail Parsing Error: {ex}")
                    finally:
                        self.driver.back()
                        time.sleep(1)
                page += 1
        finally:
            if self.driver: self.driver.quit()
        return results

if __name__ == "__main__":
    import argparse
    import csv
    import os
    parser = argparse.ArgumentParser(description="Run Samsung Newsroom crawler independently.")
    parser.add_argument("--days", type=int, default=1, help="Number of days to scrape (DATE_THRESHOLD)")
    args = parser.parse_args()
    
    print(f"삼성뉴스룸 크롤링을 시작합니다. (과거 {args.days}일)")
    crawler = SamsungCrawler()
    data = crawler.run(days_to_scrape=args.days)
    
    if data:
        os.makedirs("output", exist_ok=True)
        today_str = datetime.now().strftime('%Y%m%d')
        filename = f"output/{today_str}_samsung.csv"
        keys = data[0].keys()
        with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(data)
        print(f"✅ 수집 완료: 총 {len(data)}건 -> {filename}")
    else:
        print("수집된 기사가 없습니다.")