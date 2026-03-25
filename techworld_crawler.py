import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import re
import csv

def scrape_techworld_news(days_to_scrape=1):
    cutoff_date = (datetime.now() - timedelta(days=days_to_scrape)).date()
    results = []
    base_url = "https://www.epnc.co.kr"
    
    page = 1
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    while True:
        # 목록 페이지 URL (예시 경로)
        list_url = f"{base_url}/news/articleList.html?page={page}"
        try:
            resp = requests.get(list_url, headers=headers, timeout=15)
            resp.encoding = 'utf-8'
            if resp.status_code != 200:
                break
                
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Changed from 'ul.type2 > li' to find all 'li' containing '.titles a'
            items = []
            for li in soup.find_all('li'):
                if li.select_one('h2.titles a'):
                    items.append(li)
            
            if not items:
                break
                
            found_in_range = False
            
            for item in items:
                # 더미 데이터(샘플) 스킵
                if item.get('id') == 'sample' or 'blind' in item.get('class', []):
                    continue
                    
                try:
                    # 1. 목록에서 날짜 추출 및 19자리 문자열 포맷팅
                    date_elem = item.select_one('em.info.dated')
                    if not date_elem:
                        continue
                        
                    date_text = date_elem.get_text(strip=True)
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}(?::\d{2})?)', date_text)
                    
                    if date_match:
                        ext_date = date_match.group(1)
                        ext_time = date_match.group(2)
                        if len(ext_time) == 5:
                            ext_time += ":00"
                        full_date_time = f"{ext_date} {ext_time}"
                    else:
                        continue
                        
                    date_obj = datetime.strptime(full_date_time, '%Y-%m-%d %H:%M:%S')
                    
                    # 2. 날짜 필터링 (건너뛰기)
                    if date_obj.date() < cutoff_date:
                        continue
                        
                    found_in_range = True
                    
                    # 3. 링크 추출 및 절대경로 변환
                    title_tag = item.select_one('h2.titles a')
                    if not title_tag: 
                        continue
                        
                    title = title_tag.get_text(strip=True)
                    raw_link = title_tag['href']
                    link = raw_link if raw_link.startswith('http') else base_url + raw_link
                    
                    # 4. 상세페이지 본문 추출
                    content = ""
                    try:
                        det_resp = requests.get(link, headers=headers, timeout=15)
                        det_resp.encoding = 'utf-8'
                        det_soup = BeautifulSoup(det_resp.text, 'html.parser')
                        
                        
                        # 카테고리 추출 (예: 제목 < 서브 < 메인 < 웹사이트명)
                        cat_main, cat_sub = "홈", "최신뉴스"
                        title_tag_full = det_soup.find('title')
                        if title_tag_full:
                            parts = [p.strip() for p in title_tag_full.text.split('<')]
                            if len(parts) >= 3:
                                cat_sub = parts[1]
                                cat_main = parts[2]
                                
                        content_area = det_soup.select_one('#article-view-content-div')
                        if content_area:
                            # 불필요 요소 제거 (안내문구, 스크립트, 사진 레이아웃 등)
                            for tag in content_area.select('script, style, figure, .copy-txt-box, .share, [id^="share"]'):
                                tag.decompose()
                            content = content_area.get_text('\n', strip=True)
                    except Exception as det_e:
                        print(f"  ❌ 상세페이지 오류 ({link}): {det_e}")
                        pass
                        
                    print(f"  [테크월드뉴스] 수집: {full_date_time} | {title[:20]}...")
                    
                    # 5. 데이터 적재
                    results.append({
                        'title': title,
                        'content': content,
                        'content_summary': content[:200].replace('\n', ' '),
                        'enveloped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'date': str(full_date_time),
                        'provider': '테크월드',
                        'category_main': cat_main,
                        'category_sub': cat_sub,
                        'provider_link_page': link,
                        'useful': 1,
                        'strategy_agenda': 1,
                        'YEAR': date_obj.year,
                        'MONTH': date_obj.month,
                        'WEEK': date_obj.isocalendar()[1]
                    })
                    
                    time.sleep(1) # 트래픽 제어
                    
                except Exception as e:
                    print(f"  ❌ 항목 파싱 오류: {e}")
                    continue
            
            # 수집 대상 날짜가 더 이상 없으면 페이지 루프 종료
            if not found_in_range:
                break
                
            page += 1
            
        except Exception as e:
            print(f"❌ 목록 페이지 로드 오류: {e}")
            break
            
    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run Techworld crawler independently.")
    parser.add_argument("--days", type=int, default=1, help="Number of days to scrape (DATE_THRESHOLD)")
    args = parser.parse_args()

    print(f"테크월드뉴스 크롤링을 시작합니다. (과거 {args.days}일)")
    crawled_data = scrape_techworld_news(days_to_scrape=args.days)
    
    if crawled_data:
        import os
        import csv
        os.makedirs("output", exist_ok=True)
        today_str = datetime.now().strftime('%Y%m%d')
        filename = f"output/{today_str}_techworld.csv"
        
        keys = crawled_data[0].keys()
        with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(crawled_data)
        
        print(f"✅ 수집 완료: 총 {len(crawled_data)}건의 기사가 '{filename}'에 성공적으로 저장되었습니다.")
    else:
        print("수집된 기사가 없습니다.")