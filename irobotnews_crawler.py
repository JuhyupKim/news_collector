import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import re
import csv

def get_irobotnews_data(days_to_scrape=1):
    cutoff_date = datetime.now() - timedelta(days=days_to_scrape)
    results = []
    base_url = "https://www.irobotnews.com"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    page = 1
    keep_going = True
    
    while keep_going:
        # 목록 페이지 URL 포맷 (예시로 page 파라미터 활용)
        list_url = f"{base_url}/news/articleList.html?page={page}&view_type=sm"
        
        try:
            resp = requests.get(list_url, headers=headers, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # id="sample" 인 더미 리스트 제외하고 추출
            items = soup.select('ul.altlist-webzine > li.altlist-webzine-item:not(#sample)')
            
            if not items:
                break
                
            for item in items:
                a_tag = item.select_one('h2.altlist-subject a')
                if not a_tag:
                    continue
                    
                title = a_tag.get_text(strip=True)
                raw_link = a_tag.get('href', '')
                
                # 상대 경로를 절대 경로로 변환
                link = raw_link if raw_link.startswith('http') else f"{base_url}{raw_link if raw_link.startswith('/') else '/' + raw_link}"
                
                # 상세 페이지 진입
                try:
                    det_resp = requests.get(link, headers=headers, timeout=15)
                    det_resp.raise_for_status()
                    det_soup = BeautifulSoup(det_resp.text, 'html.parser')
                    
                    # 날짜 추출 (예: 입력 2026.03.02 22:03)
                    info_area = det_soup.select_one('ul.infomation')
                    info_text = info_area.get_text(separator=" ", strip=True) if info_area else ""
                    
                    full_date_time = f"{datetime.now().strftime('%Y-%m-%d')} 00:00:00" # 기본값
                    date_match = re.search(r'(\d{4})\.(\d{2})\.(\d{2})\s+(\d{2}:\d{2}(?::\d{2})?)', info_text)
                    
                    if date_match:
                        y, m, d, hm = date_match.groups()
                        if len(hm) == 5:
                            hm += ":00"
                        full_date_time = f"{y}-{m}-{d} {hm}" # 19자리 맞춤
                    
                    date_obj = datetime.strptime(full_date_time, '%Y-%m-%d %H:%M:%S')
                    
                    # Cutoff 날짜 필터링
                    if date_obj.date() < cutoff_date.date():
                        keep_going = False
                        break
                        
                    # 본문 추출 및 불필요한 태그 제거 (스크립트, 스타일, 이미지 안내 등)
                    content_area = det_soup.select_one('article#article-view-content-div')
                    content = ""
                    if content_area:
                        for tag in content_area.select('script, style, figure, .photo-layout, .share, [id^="share"]'):
                            tag.decompose()
                        content = content_area.get_text('\n', strip=True)
                        
                        
                    # 카테고리 추출 (예: 제목 < 서브 < 메인 < 웹사이트명)
                    cat_main, cat_sub = "홈", "최신뉴스"
                    title_tag_full = det_soup.find('title')
                    if title_tag_full:
                        parts = [p.strip() for p in title_tag_full.text.split('<')]
                        if len(parts) >= 3:
                            cat_sub = parts[1]
                            cat_main = parts[2]
                            
                    content_summary = content[:200]
                    
                    print(f"수집 완료: {full_date_time} | {title[:30]}...")
                    
                    results.append({
                        'title': title,
                        'content': content,
                        'content_summary': content_summary,
                        'enveloped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'date': str(full_date_time),
                        'provider': '로봇신문',
                        'category_main': cat_main,
                        'category_sub': cat_sub,
                        'provider_link_page': link,
                        'useful': 1,
                        'strategy_agenda': 1,
                        'YEAR': date_obj.year,
                        'MONTH': date_obj.month,
                        'WEEK': date_obj.isocalendar()[1]
                    })
                    
                    time.sleep(1) # 서버 부하 방지
                    
                except Exception as e:
                    print(f"상세 페이지 오류 ({link}): {e}")
                    continue
                    
            page += 1
            
        except Exception as e:
            print(f"목록 페이지 통신 오류: {e}")
            break
            
    return results

if __name__ == "__main__":
    # 최근 1일치 기사 수집 실행
    scraped_data = get_irobotnews_data(days_to_scrape=1)
    
    if scraped_data:
        import os
        os.makedirs("output", exist_ok=True)
        today_str = datetime.now().strftime('%Y%m%d')
        file_name = f"output/{today_str}_로봇신문.csv"
        keys = scraped_data[0].keys()
        
        with open(file_name, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(scraped_data)
            
        print(f"\n[성공] 총 {len(scraped_data)}건의 기사가 '{file_name}'로 저장되었습니다.")
    else:
        print("\n[안내] 수집된 데이터가 없습니다.")