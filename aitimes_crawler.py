import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import re
import csv
import sys
import io

# 콘솔 출력 인코딩 설정 (cp949 오류 방지)
sys.stdout.reconfigure(encoding='utf-8')

def get_aitimes_data(days_to_scrape=1, max_items=None, seen_links=None):
    if seen_links is None:
        seen_links = set()
    cutoff_date = (datetime.now() - timedelta(days=days_to_scrape)).date()
    results = []
    base_url = "https://www.aitimes.com"
    
    page = 1
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    while True:
        # 동적으로 페이징 URL 처리 (페이지 번호 위치에 따라 수정 필요)
        list_url = f"https://www.aitimes.com/news/articleList.html?page=PAGE_NUM".replace("PAGE_NUM", str(page))
        
        try:
            resp = requests.get(list_url, headers=headers, timeout=15)
            # 한글 깨짐 방지를 위한 자동 인코딩 감지 또는 수동 설정
            resp.encoding = resp.apparent_encoding 
            
            if resp.status_code != 200:
                break
                
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # 목록 컨테이너 추출
            items = soup.select("li.altlist-text-item")
            
            if not items:
                break
                
            found_in_range = False
            
            for item in items:
                try:
                    # 제목 및 링크 추출
                    title_tag = item.select_one("a")
                    if not title_tag:
                        continue
                        
                    title = title_tag.get_text(strip=True)
                    raw_link = title_tag['href'] if title_tag.name == 'a' else title_tag.parent.get('href', '')
                    
                    if not raw_link:
                        # a 태그가 아닌 경우 하위에서 a태그 찾기
                        a_tag = item.select_one('a')
                        if a_tag:
                            raw_link = a_tag.get('href', '')
                            
                    link = raw_link if raw_link.startswith('http') else base_url.rstrip('/') + '/' + raw_link.lstrip('/')
                    
                    if link in seen_links:
                        continue
                    
                    # 날짜 추출 (날짜가 없으면 오늘 날짜로)
                    date_elem = item.select_one("") if "" else item
                    full_date_time = datetime.now().strftime("%Y-%m-%d 00:00:00")
                    
                    if date_elem:
                        date_text = date_elem.get_text(separator=' ', strip=True)
                        date_match = re.search(r'(\d{4}[-./]\d{2}[-./]\d{2})', date_text)
                        short_date_match = re.search(r'(?<!\d)(0[1-9]|1[0-2])[-./](0[1-9]|[12]\d|3[01])(?!\d)', date_text)
                        
                        ext_date = None
                        if date_match:
                            ext_date = date_match.group(1).replace('.', '-').replace('/', '-')
                        elif short_date_match:
                            curr_year = datetime.now().year
                            ext_date = f"{curr_year}-{short_date_match.group(1)}-{short_date_match.group(2)}"
                            
                        if ext_date:
                            # 시간도 있다면 추출
                            time_match = re.search(r'(\d{2}:\d{2}(?::\d{2})?)', date_text)
                            ext_time = time_match.group(1) if time_match else "00:00:00"
                            if len(ext_time) == 5:
                                ext_time += ":00"
                                
                            full_date_time = f"{ext_date} {ext_time}"
                            
                    try:
                        date_obj = datetime.strptime(full_date_time, '%Y-%m-%d %H:%M:%S')
                    except:
                        # 날짜 파싱 실패 시 기본값
                        date_obj = datetime.now()
                        full_date_time = date_obj.strftime("%Y-%m-%d %H:%M:%S")
                    
                    # 기간 필터링
                    if date_obj.date() < cutoff_date:
                        continue
                        
                    found_in_range = True
                    
                    # 상세 본문 추출
                    content = ""
                    cat_main, cat_sub = "분류", "뉴스"
                    
                    try:
                        det_resp = requests.get(link, headers=headers, timeout=15)
                        det_resp.encoding = det_resp.apparent_encoding
                        det_soup = BeautifulSoup(det_resp.text, 'html.parser')
                        
                        # 카테고리 추출 시도 (Title 태그 활용)
                        title_tag_full = det_soup.find('title')
                        if title_tag_full:
                            parts = [p.strip() for p in re.split(r'[-|<>&]', title_tag_full.text)]
                            if len(parts) >= 2:
                                cat_sub = parts[-2]
                                
                        # 본문 영역
                        content_area = det_soup.select_one("#article-view-content-div")
                        if content_area:
                            for tag in content_area.select('script, style, figure, .ad'):
                                tag.decompose()
                            content = content_area.get_text('\n', strip=True)
                    except Exception as det_e:
                        print(f"  ❌ 상세 본문 오류 ({link}): {det_e}")
                        
                    print(f"  [AI타임스] 수집: {full_date_time} | {title[:20]}...")
                    
                    results.append({
                        'title': title,
                        'content': content,
                        'content_summary': content[:200].replace('\n', ' '),
                        'enveloped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'date': str(full_date_time),
                        'provider': 'AI타임스',
                        'category_main': cat_main,
                        'category_sub': cat_sub,
                        'provider_link_page': link,
                        'useful': 1,
                        'strategy_agenda': 1,
                        'YEAR': date_obj.year,
                        'MONTH': date_obj.month,
                        'WEEK': date_obj.isocalendar()[1]
                    })
                    seen_links.add(link)
                    time.sleep(1) # 서버 트래픽 보호
                    
                    if max_items and len(results) >= max_items:
                        return results
                    
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
    print("AI타임스 테스트 실행 중...")
    data = get_aitimes_data(days_to_scrape=1)
    if data:
        print(f"✅ {len(data)}건 수집 성공!")
        print(f"제목 미리보기: {data[0]['title']}")
        print(f"날짜 미리보기: {data[0]['date']}")
    else:
        print("❌ 수집 실패. 생성된 코드의 CSS Selector를 개발자 도구로 수동 확인해주세요.")
