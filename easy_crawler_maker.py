import requests
from bs4 import BeautifulSoup
import urllib.parse
import os
import sys
import io

# 콘솔 출력 인코딩 설정 (cp949 오류 방지)
sys.stdout.reconfigure(encoding='utf-8')

def find_css_selector(element):
    """주어진 BeautifulSoup 엘리먼트의 유일한 CSS 선택자를 찾습니다."""
    path = []
    
    # 클래스나 ID로 짧은 경로 찾기 시도
    for parent in [element] + list(element.parents):
        if parent.name == '[document]':
            break
            
        selector = parent.name
        
        # ID가 있으면 ID 사용이 가장 확실함
        if parent.get('id'):
            selector += f"#{parent.get('id')}"
            path.insert(0, selector)
            break
            
        # 클래스가 있으면 클래스 추가
        if parent.get('class'):
            classes = ".".join(parent.get('class'))
            selector += f".{classes}"
            
        # 형제 노드들 중 몇 번째인지 확인 (nth-child)
        if parent.parent and parent.parent.name != '[document]':
            siblings = parent.parent.find_all(parent.name, recursive=False)
            if len(siblings) > 1:
                index = siblings.index(parent) + 1
                selector += f":nth-child({index})"
                
        path.insert(0, selector)
        
    # 선택자 조합
    full_selector = " > ".join(path)
    
    # 정말 이 엘리먼트 하나를 가리키는지 검증
    # 만약 너무 길거나 복잡하면 적당히 자르는 로직이 필요하지만, 여기서는 단순화하여 반환
    return full_selector

def get_generalized_selector(element):
    """
    모든 기사 목록을 포괄할 수 있도록 nth-child 등을 제거한 
    일반화된 CSS 선택자를 찾습니다.
    """
    path = []
    
    for parent in [element] + list(element.parents):
        if parent.name == '[document]':
            break
            
        selector = parent.name
        
        # 목록 요소에는 ID를 쓰지 않거나, 쓰더라도 상위 컨테이너에만 적용
        if parent.get('id') and parent.name not in ['li', 'tr', 'td', 'a', 'span', 'div']:
             selector += f"#{parent.get('id')}"
             path.insert(0, selector)
             break
             
        if parent.get('class'):
            classes = ".".join(parent.get('class'))
            selector += f".{classes}"
            
        path.insert(0, selector)
        
    return " > ".join(path)

# =========================================================================
# 메인 템플릿 코드
# =========================================================================
TEMPLATE = """import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import re
import csv
import sys
import io

# 콘솔 출력 인코딩 설정 (cp949 오류 방지)
sys.stdout.reconfigure(encoding='utf-8')

def get_{crawler_name}_data(days_to_scrape=1, max_items=None, seen_links=None):
    if seen_links is None:
        seen_links = set()
    cutoff_date = (datetime.now() - timedelta(days=days_to_scrape)).date()
    results = []
    base_url = "{base_url}"
    
    page = 1
    headers = {{
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }}
    
    while True:
        # 동적으로 페이징 URL 처리 (페이지 번호 위치에 따라 수정 필요)
        list_url = f"{list_url_pattern}".replace("PAGE_NUM", str(page))
        
        try:
            resp = requests.get(list_url, headers=headers, timeout=15)
            # 한글 깨짐 방지를 위한 자동 인코딩 감지 또는 수동 설정
            resp.encoding = resp.apparent_encoding 
            
            if resp.status_code != 200:
                break
                
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # 목록 컨테이너 추출
            items = soup.select("{list_item_selector}")
            
            if not items:
                break
                
            found_in_range = False
            
            for item in items:
                try:
                    # 제목 및 링크 추출
                    title_tag = item.select_one("{title_selector}")
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
                    date_elem = item.select_one("{date_selector}") if "{date_selector}" else item
                    full_date_time = datetime.now().strftime("%Y-%m-%d 00:00:00")
                    
                    if date_elem:
                        date_text = date_elem.get_text(separator=' ', strip=True)
                        date_match = re.search(r'(\\d{{4}}[-./]\\d{{2}}[-./]\\d{{2}})', date_text)
                        short_date_match = re.search(r'(?<!\\d)(0[1-9]|1[0-2])[-./](0[1-9]|[12]\\d|3[01])(?!\\d)', date_text)
                        
                        ext_date = None
                        if date_match:
                            ext_date = date_match.group(1).replace('.', '-').replace('/', '-')
                        elif short_date_match:
                            curr_year = datetime.now().year
                            ext_date = f"{{curr_year}}-{{short_date_match.group(1)}}-{{short_date_match.group(2)}}"
                            
                        if ext_date:
                            # 시간도 있다면 추출
                            time_match = re.search(r'(\\d{{2}}:\\d{{2}}(?::\\d{{2}})?)', date_text)
                            ext_time = time_match.group(1) if time_match else "00:00:00"
                            if len(ext_time) == 5:
                                ext_time += ":00"
                                
                            full_date_time = f"{{ext_date}} {{ext_time}}"
                            
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
                        content_area = det_soup.select_one("{body_selector}")
                        if content_area:
                            for tag in content_area.select('script, style, figure, .ad'):
                                tag.decompose()
                            content = content_area.get_text('\\n', strip=True)
                    except Exception as det_e:
                        print(f"  ❌ 상세 본문 오류 ({{link}}): {{det_e}}")
                        
                    print(f"  [{provider_name}] 수집: {{full_date_time}} | {{title[:20]}}...")
                    
                    results.append({{
                        'title': title,
                        'content': content,
                        'content_summary': content[:200].replace('\\n', ' '),
                        'enveloped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'date': str(full_date_time),
                        'provider': '{provider_name}',
                        'category_main': cat_main,
                        'category_sub': cat_sub,
                        'provider_link_page': link,
                        'useful': 1,
                        'strategy_agenda': 1,
                        'YEAR': date_obj.year,
                        'MONTH': date_obj.month,
                        'WEEK': date_obj.isocalendar()[1]
                    }})
                    seen_links.add(link)
                    time.sleep(1) # 서버 트래픽 보호
                    
                    if max_items and len(results) >= max_items:
                        return results
                    
                except Exception as item_e:
                    print(f"  ❌ 항목 오류: {{item_e}}")
                    continue
                    
            if not found_in_range:
                break
            page += 1
            
        except Exception as list_e:
            print(f"❌ 페이지 목록 오류: {{list_e}}")
            break
            
    return results

if __name__ == "__main__":
    print("{provider_name} 테스트 실행 중...")
    data = get_{crawler_name}_data(days_to_scrape=1)
    if data:
        print(f"✅ {{len(data)}}건 수집 성공!")
        print(f"제목 미리보기: {{data[0]['title']}}")
        print(f"날짜 미리보기: {{data[0]['date']}}")
    else:
        print("❌ 수집 실패. 생성된 코드의 CSS Selector를 개발자 도구로 수동 확인해주세요.")
"""

def get_yes_no(prompt):
    while True:
        ans = input(prompt + " (y/n): ").strip().lower()
        if ans in ['y', 'yes']:
            return True
        if ans in ['n', 'no']:
            return False

def interactive_wizard():
    print("=" * 60)
    print("✨ 초보자용 뉴스 크롤러 마법사 (코딩 지식 불필요) ✨")
    print("=" * 60)
    print("HTML이나 코드를 몰라도 컴퓨터가 물어보는 단어에")
    print("'y'(맞다), 'n'(아니다)만 대답해주세요!\n")
    
    crawler_name = input("1. 새 크롤러 이름 (영문, 예: hankook): ").strip().lower()
    if not crawler_name:
        return print("이름이 필요합니다. 종료합니다.")
        
    provider_name = input("2. 신문사/웹사이트 이름 (한글, 예: 한국일보): ").strip()
    
    list_url = input("3. 뉴스 기사가 나열된 '목록 페이지' 복사해서 붙여넣기\n"
                     "   (예: https://news.site.com/list?page=1): \n> ").strip()
                     
    if "page=" in list_url:
        list_url_pattern = re.sub(r'page=\d+', 'page=PAGE_NUM', list_url)
    elif "p=" in list_url:
        list_url_pattern = re.sub(r'p=\d+', 'p=PAGE_NUM', list_url)
    else:
        print("   목록 주소에 페이지 번호(page=1)가 보이지 않습니다.")
        print("   일단 1페이지 전용으로 생성됩니다.")
        list_url_pattern = list_url

    parsed_url = urllib.parse.urlparse(list_url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    headers = {"User-Agent": "Mozilla/5.0"}
    print("\n🌐 사이트에 접속하여 구조를 분석 중입니다. 잠시만 기다려주세요...")
    
    try:
        resp = requests.get(list_url, headers=headers, timeout=10)
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, 'html.parser')
    except Exception as e:
        return print(f"❌ 사이트 접속에 실패했습니다: {e}")
        
    # --- 제목(Title) 찾기 ---
    print("\n🔍 [1단계] 뉴스 제목 찾기")
    title_selector = ""
    list_item_selector = ""
    sample_article_url = ""
    found_title = False
    
    # 길이가 10이상 100이하인 a 태그 위주로 검사
    a_tags = soup.find_all('a')
    for a in a_tags:
        text = a.get_text(strip=True)
        # 텍스트가 뉴스 제목같아 보인다면
        if len(text) > 10 and len(text) < 100 and "로그인" not in text:
            print(f"\n👉 발견 문구: [{text}]")
            if get_yes_no("이 문구가 수집하려는 뉴스 기사 제목이 맞나요?"):
                # 해당하는 a 태그의 선택자 분석
                generalized = get_generalized_selector(a)
                # li 나 div 등 상위 목록 래퍼 찾기
                for parent in a.parents:
                    if parent.name in ['li', 'tr', 'div.item', 'div.article']:
                        list_item_selector = get_generalized_selector(parent)
                        # 제목 선택자는 하위 경로만 사용
                        title_selector = a.name
                        if a.get('class'):
                            title_selector += "." + ".".join(a.get('class'))
                        break
                
                # 못 찾았으면 임시 처리
                if not list_item_selector:
                    list_item_selector = get_generalized_selector(a.parent)
                    title_selector = 'a'
                    
                sample_article_url = a.get('href', '')
                if not sample_article_url.startswith('http'):
                    sample_article_url = base_url.rstrip('/') + '/' + sample_article_url.lstrip('/')
                    
                found_title = True
                print("✅ 제목 찾는 방법을 완벽히 이해했습니다!")
                break
                
    if not found_title:
        print("❌ 뉴스 제목을 찾지 못했습니다. 목록 사이트가 맞는지 확인해주세요.")
        return
        
    # --- 날짜(Date) 찾기 ---
    print("\n🔍 [2단계] 뉴스 날짜 찾기")
    date_selector = ""
    
    # 2024-05-12 같은 날짜 형태를 찾음
    date_pattern = re.compile(r'\d{4}[-./]\d{2}[-./]\d{2}')
    found_date = False
    
    # 목록 컨테이너 내부만 검색
    wrapper_elements = soup.select(list_item_selector)
    if wrapper_elements:
        first_item = wrapper_elements[0]
        for tag in first_item.find_all():
            text = tag.get_text(strip=True)
            if date_pattern.search(text):
                print(f"\n👉 발견 날짜: [{text}]")
                if get_yes_no("이것이 기사 작성 날짜가 맞나요?"):
                    date_selector = tag.name
                    if tag.get('class'):
                        date_selector += "." + ".".join(tag.get('class'))
                    found_date = True
                    print("✅ 날짜 찾는 방법을 확보했습니다!")
                    break
    
    if not found_date:
         print("⚠️ 화면에서 날짜를 자동으로 찾지 못했습니다. 날짜는 자동으로 오늘 날짜로 입력됩니다.")
         date_selector = "span.date" # 임시

    # --- 본문(Body) 찾기 ---
    print("\n🔍 [3단계] 상세 본문 찾기")
    body_selector = ""
    
    print(f"미리 찾아둔 뉴스 페이지 접속 중... ({sample_article_url})")
    try:
         art_resp = requests.get(sample_article_url, headers=headers, timeout=10)
         art_resp.encoding = art_resp.apparent_encoding
         art_soup = BeautifulSoup(art_resp.text, 'html.parser')
         
         # 본문처럼 보이는 거대한 텍스트 덩어리 찾기 (보통 div, p)
         longest_text_len = 0
         best_tag = None
         
         # div 태그들 위주로 검사
         for d in art_soup.find_all('div'):
             text = d.get_text(strip=True)
             if len(text) > 300 and d.get('class'): 
                 if len(text) > longest_text_len:
                     longest_text_len = len(text)
                     best_tag = d
                     
         if best_tag:
             sample_text = best_tag.get_text(strip=True)[:100]
             print(f"\n👉 발견 본문 앞부분: [{sample_text}...]")
             if get_yes_no("이것이 뉴스 기사의 본문 내용이 맞나요?"):
                 body_selector = best_tag.name
                 if best_tag.get('id'):
                     body_selector += "#" + best_tag.get('id')
                 elif best_tag.get('class'):
                     body_selector += "." + ".".join(best_tag.get('class'))
                 print("✅ 본문 찾는 방법을 확보했습니다!")
             else:
                 body_selector = "div.article-body" # fallback
         else:
             print("⚠️ 알 수 없는 본문 구조입니다. 임시 값으로 대체합니다.")
             body_selector = "div.article-content"
             
    except Exception as e:
         print(f"❌ 본문 페이지 접속 실패: {e}. 임시 값으로 대체합니다.")
         body_selector = "div.content"
         
         
    # --- 템플릿 파일 생성 ---
    print("\n📦 코드를 조립하고 있습니다...")
    final_code = TEMPLATE.format(
        crawler_name=crawler_name,
        provider_name=provider_name,
        base_url=base_url,
        list_url_pattern=list_url_pattern,
        list_item_selector=list_item_selector,
        title_selector=title_selector,
        date_selector=date_selector,
        body_selector=body_selector
    )
    
    filename = f"{crawler_name}_crawler.py"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(final_code)
        
    print("\n🎉 모든 작업이 끝났습니다!")
    print(f"✅ 기계가 학습한 내용을 바탕으로 '{filename}' 파일이 완성되었습니다.")
    print(f"터미널에서 'python {filename}'을 입력하여 수집이 잘 되는지 확인해보세요!")
    print("\n만약 잘 안된다면, HTML 구조가 너무 특이한 사이트입니다. 이때는 전문가의 도움이 필요합니다.")

if __name__ == "__main__":
    try:
        interactive_wizard()
    except KeyboardInterrupt:
        print("\n\n취소되었습니다.")
