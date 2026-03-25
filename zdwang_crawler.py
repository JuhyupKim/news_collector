import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import re
from deep_translator import GoogleTranslator

def translate_text(text):
    if not text: return ""
    try:
        return GoogleTranslator(source='auto', target='ko').translate(text[:4500])
    except: return text

def get_zdwang_data(days_to_scrape=1):
    cutoff_date = datetime.now() - timedelta(days=days_to_scrape)
    results = []
    categories = [
        {'url': 'http://news.zdwang.com/web/', 'main': '뉴스센터', 'sub': '과기쾌보'},
        {'url': 'http://news.zdwang.com/hea/', 'main': '뉴스센터', 'sub': '지혜가전'}
    ]
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    
    for cat in categories:
        page = 1
        while True:
            list_url = f"{cat['url']}index.html" if page == 1 else f"{cat['url']}{page}.html"
            try:
                resp = requests.get(list_url, headers=headers, timeout=15)
                resp.encoding = 'gb2312'
                if resp.status_code != 200: break
                soup = BeautifulSoup(resp.text, 'html.parser')
                items = soup.select('UL.list LI')
                if not items or page > 5: break
                
                found_in_range = False
                for item in items:
                    pubtime_tag = item.select_one('span.pubtime')
                    if not pubtime_tag: continue
                    
                    # 목록의 날짜로 먼저 범위 확인
                    list_date_str = re.search(r'\d{4}-\d{2}-\d{2}', pubtime_tag.text.replace('年','-').replace('月','-').replace('日','')).group()
                    date_obj = datetime.strptime(list_date_str, '%Y-%m-%d')
                    if date_obj.date() < cutoff_date.date(): continue
                    
                    found_in_range = True
                    a_tag = item.select_one('H3.title a')
                    raw_href = a_tag['href'].strip()
                    link = raw_href if raw_href.startswith('http') else f"http://news.zdwang.com{raw_href if raw_href.startswith('/') else '/'+raw_href}"
                    
                    # 상세페이지에서 시/분/초 추출
                    full_date_time = f"{list_date_str} 00:00:00" # 기본값
                    content = ""
                    try:
                        detail_resp = requests.get(link, headers=headers, timeout=15)
                        detail_resp.encoding = 'gb2312'
                        detail_soup = BeautifulSoup(detail_resp.text, 'html.parser')
                        
                        # 💡 상세페이지 날짜/시간 영역 스캔
                        info_text = detail_soup.get_text(" ", strip=True)
                        time_match = re.search(r'(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}(?::\d{2})?)', info_text)
                        if time_match:
                            ext_date = time_match.group(1)
                            ext_time = time_match.group(2)
                            if len(ext_time) == 5:
                                ext_time += ":00"
                            full_date_time = f"{ext_date} {ext_time}"
                        
                        content_area = detail_soup.find('div', class_='content')
                        if content_area:
                            for unwanted in content_area.select('script, style, .share, [id^="share"]'):
                                unwanted.decompose()
                            content = content_area.get_text("\n", strip=True)
                        else:
                            content = ""
                    except Exception as ex:
                        print(f"  [zdwang] Detail Parsing Error: {ex}")

                    print(f"  [zdwang] 수집: {full_date_time} | {a_tag.get('title','').strip()[:20]}...")

                    results.append({
                        'title': translate_text(a_tag.get('title','').strip()),
                        'content': translate_text(content),
                        'enveloped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'date': str(full_date_time), # 💡 강제 문자열 변환
                        'provider': 'zdwang',
                        'category_main': cat['main'], 'category_sub': cat['sub'],
                        'provider_link_page': link, 'useful': 1, 'strategy_agenda': 0,
                        'content_summary': translate_text(content[:200]),
                        'category1': 'zdwang', 'category2': cat['sub'],
                        'YEAR': date_obj.year, 'MONTH': date_obj.month, 'WEEK': date_obj.isocalendar()[1]
                    })
                    time.sleep(1.2)
                if not found_in_range: break
                page += 1
            except: break
    return results

if __name__ == "__main__":
    import argparse
    import csv
    import os
    parser = argparse.ArgumentParser(description="Run ZDWang crawler independently.")
    parser.add_argument("--days", type=int, default=1, help="Number of days to scrape (DATE_THRESHOLD)")
    args = parser.parse_args()
    
    print(f"ZDWang 크롤링을 시작합니다. (과거 {args.days}일)")
    data = get_zdwang_data(days_to_scrape=args.days)
    
    if data:
        os.makedirs("output", exist_ok=True)
        today_str = datetime.now().strftime('%Y%m%d')
        filename = f"output/{today_str}_zdwang.csv"
        keys = data[0].keys()
        with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(data)
        print(f"✅ 수집 완료: 총 {len(data)}건 -> {filename}")
    else:
        print("수집된 기사가 없습니다.")