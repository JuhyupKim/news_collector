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

def get_cheaa_data(days_to_scrape=1):
    cutoff_date = datetime.now() - timedelta(days=days_to_scrape)
    results = []
    base_url = "https://m.cheaa.com/"
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"}
    desktop_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"}
    
    for page in range(1, 4): # 날짜가 섞여있으므로 3페이지까지 넉넉히 검사
        url = base_url if page == 1 else f"{base_url}include/ajax_more.php?type=index&page={page}"
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            boxes = soup.select("div.newsBox")
            
            for box in boxes:
                # 1. 목록에서 날짜 추출
                date_text = box.select_one("p b").text if box.select_one("p b") else ""
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date_text)
                if not date_match: continue
                
                list_date_only = date_match.group(1) # "YYYY-MM-DD"
                date_obj = datetime.strptime(list_date_only, '%Y-%m-%d')
                
                # 날짜 범위 필터링 (건너뛰기)
                if date_obj.date() < cutoff_date.date(): continue
                
                a_tag = box.select_one("p a")
                link = a_tag['href']
                if not link.startswith('http'): link = "https://news.cheaa.com" + link
                
                # 2. 상세페이지에서 시/분/초 수집 시도
                full_date_time = f"{list_date_only} 00:00:00" # 기본값 설정
                content = ""
                cat_main = ""
                try:
                    det_resp = requests.get(link, headers=desktop_headers, timeout=15)
                    det_resp.encoding = 'utf-8'
                    det_soup = BeautifulSoup(det_resp.text, 'html.parser')
                    
                    # div.info 내의 시간 텍스트 정밀 탐색 (공백 및 특수공백 대응)
                    info_area = det_soup.select_one("div.info")
                    if info_area:
                        info_text = info_area.get_text(" ", strip=True)
                        # 패턴: YYYY-MM-DD 뒤에 한 칸 이상의 공백과 시간(HH:MM)이 있는지 확인
                        time_pattern = re.search(r'(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}(?::\d{2})?)', info_text)
                        if time_pattern:
                            ext_date = time_pattern.group(1)
                            ext_time = time_pattern.group(2)
                            # 초 단위가 없으면(16:27) :00 추가
                            if len(ext_time) == 5: ext_time += ":00"
                            full_date_time = f"{ext_date} {ext_time}"
                    
                    cont_area = det_soup.select_one("div#ctrlfscont") or det_soup.select_one("div.article")
                    if cont_area:
                        for unwanted in cont_area.select('script, style, .share, [id^="share"]'):
                            unwanted.decompose()
                        content = cont_area.get_text("\n", strip=True)
                    else:
                        content = ""
                        
                    title_tag_full = det_soup.find('title')
                    if title_tag_full:
                        parts = [p.strip() for p in title_tag_full.text.split('-')]
                        if len(parts) >= 2:
                            cat_main = parts[1]
                except Exception as ex:
                    print(f"  [CHEAA] Detail Parsing Error: {ex}")

                print(f"  [CHEAA] 매칭: {full_date_time} | {a_tag.text[:20]}...")

                # 3. 데이터 저장 (모든 날짜값은 반드시 19자리 문자열이어야 함)
                results.append({
                    'title': translate_text(a_tag.text),
                    'content': translate_text(content),
                    'enveloped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'date': str(full_date_time), # 강제 문자열 변환
                    'provider': 'cheaa',
                    'category_main': translate_text(cat_main), 
                    'category_sub': '',
                    'provider_link_page': link, 'useful': 1, 'strategy_agenda': 0,
                    'content_summary': translate_text(content[:200]),
                    'category1': 'cheaa', 'category2': '',
                    'YEAR': date_obj.year, 'MONTH': date_obj.month, 'WEEK': date_obj.isocalendar()[1]
                })
                time.sleep(1.2)
        except Exception as e:
            print(f"  ❌ CHEAA 페이지 오류: {e}")
            break
    return results