import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import re

def get_businesspost_data(days_to_scrape=1, max_items=None, global_seen_links=None):
    if max_items is not None and max_items <= 0:
        max_items = None
        
    cutoff_date = (datetime.now() - timedelta(days=days_to_scrape)).date()
    results = []
    seen_links = set(global_seen_links) if global_seen_links else set()
    base_url = "https://www.businesspost.co.kr"
    
    page = 1
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    while True:
        if max_items is not None and len(results) >= max_items:
            break
            
        # 동적으로 페이징 URL 처리
        list_url = f"https://www.businesspost.co.kr/BP?command=sub&sub=8&page={page}"
        
        try:
            resp = requests.get(list_url, headers=headers, timeout=15)
            # 한글 깨짐 방지를 위한 디코딩
            resp.encoding = 'utf-8'
            
            if resp.status_code != 200:
                break
                
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # 목록 컨테이너 추출
            items = soup.select("div.left_post")
            
            if not items:
                break
                
            found_in_range = False
            
            for item in items:
                if max_items is not None and len(results) >= max_items:
                    break
                    
                try:
                    # 링크 추출
                    a_tag = item.select_one("a")
                    if not a_tag:
                        continue
                        
                    raw_link = a_tag.get('href', '')
                    title_tag = item.select_one("h3")
                    title = title_tag.get_text(strip=True) if title_tag else ""
                    
                    if not title:
                        continue
                            
                    link = raw_link if raw_link.startswith('http') else base_url.rstrip('/') + '/' + raw_link.lstrip('/')
                    
                    if link in seen_links:
                        continue
                    seen_links.add(link)
                    
                    # 상세 본문 추출
                    content = ""
                    cat_main, cat_sub = "분류", "뉴스"
                    full_date_time = ""
                    date_obj = None
                    
                    try:
                        det_resp = requests.get(link, headers=headers, timeout=15)
                        det_resp.encoding = 'utf-8'
                        det_soup = BeautifulSoup(det_resp.text, 'html.parser')
                        
                        # 카테고리 추출
                        category_span = det_soup.select_one("span.category")
                        if category_span:
                            cat_parts = category_span.get_text(strip=True).split()
                            if len(cat_parts) >= 1:
                                cat_main = cat_parts[0]
                            if len(cat_parts) >= 2:
                                cat_sub = cat_parts[1]
                                
                        # 날짜 추출
                        author_info = det_soup.select_one("div.author_info")
                        if author_info:
                            date_text = author_info.get_text(strip=True)
                            # 2026-03-13 11:32:35 형식 등을 찾기
                            date_match = re.search(r'(\d{4}[-./]\d{2}[-./]\d{2})\s+(\d{2}:\d{2}(?::\d{2})?)', date_text)
                            if date_match:
                                ext_date = date_match.group(1).replace('.', '-').replace('/', '-')
                                ext_time = date_match.group(2)
                                if len(ext_time) == 5:
                                    ext_time += ":00"
                                full_date_time = f"{ext_date} {ext_time}"
                                try:
                                    date_obj = datetime.strptime(full_date_time, '%Y-%m-%d %H:%M:%S')
                                except:
                                    pass

                        # 본문 영역
                        content_area = det_soup.select_one("div.detail_editor")
                        if content_area:
                            for tag in content_area.select('script, style, figure, .ad'):
                                tag.decompose()
                            content = content_area.get_text('\n', strip=True)

                    except Exception as det_e:
                        print(f"  ❌ 상세 본문 오류 ({link}): {det_e}")
                    
                    if date_obj is None:
                        continue
                        
                    # 기간 필터링
                    if date_obj.date() < cutoff_date:
                        continue
                        
                    found_in_range = True
                    print(f"  [BUSINESSPOST] 수집: {full_date_time} | {title[:20]}...")
                    
                    results.append({
                        'title': title,
                        'content': content,
                        'content_summary': content[:200].replace('\n', ' '),
                        'enveloped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'date': str(full_date_time),
                        'provider': 'businesspost',
                        'category_main': cat_main,
                        'category_sub': cat_sub,
                        'provider_link_page': link,
                        'useful': 1,
                        'strategy_agenda': 1,
                        'YEAR': date_obj.year,
                        'MONTH': date_obj.month,
                        'WEEK': date_obj.isocalendar()[1]
                    })
                    time.sleep(1) # 서버 트래픽 보호
                    
                except Exception as item_e:
                    print(f"  ❌ 항목 오류: {item_e}")
                    continue
                    
            if not found_in_range:
                break
            page += 1
            
        except Exception as list_e:
            print(f"❌ 페이지 목록 오류: {list_e}")
            break
            
    return results

if __name__ == "__main__":
    import argparse
    import csv
    import os
    parser = argparse.ArgumentParser(description="Run BusinessPost crawler independently.")
    parser.add_argument("--days", type=int, default=1, help="Number of days to scrape (DATE_THRESHOLD)")
    args = parser.parse_args()

    print(f"비즈니스포스트 크롤링을 시작합니다. (과거 {args.days}일)")
    data = get_businesspost_data(days_to_scrape=args.days)
    
    if data:
        os.makedirs("output", exist_ok=True)
        today_str = datetime.now().strftime('%Y%m%d')
        filename = f"output/{today_str}_businesspost.csv"
        keys = data[0].keys()
        with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(data)
        print(f"✅ 수집 완료: 총 {len(data)}건 -> {filename}")
    else:
        print("수집된 기사가 없습니다.")
