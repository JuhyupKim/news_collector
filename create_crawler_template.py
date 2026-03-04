import os
import sys
import io

# 콘솔 출력 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

TEMPLATE = """import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import re
import csv

def get_{crawler_name}_data(days_to_scrape=1):
    cutoff_date = (datetime.now() - timedelta(days=days_to_scrape)).date()
    results = []
    base_url = "{base_url}"
    
    page = 1
    headers = {{
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }}
    
    while True:
        # TODO: 실제 뉴스의 목록 페이지 URL 규칙에 맞게 수정하세요.
        list_url = f"{{base_url}}/news/articleList.html?page={{page}}"
        
        try:
            resp = requests.get(list_url, headers=headers, timeout=15)
            # UTF-8이 아닌 사이트의 경우 여기서 설정 (예: resp.encoding = 'euc-kr')
            resp.encoding = 'utf-8' 
            
            if resp.status_code != 200:
                break
                
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # TODO: 뉴스 목록 페이지의 개별 기사 항목(li 태그 등)을 가리키는 CSS 선택자로 변경하세요.
            items = soup.select('.article-list > li')
            
            if not items:
                break
                
            found_in_range = False
            
            for item in items:
                try:
                    # 1. 날짜 추출 및 포맷팅 (TODO: 사이트 구조에 맞게 수정)
                    date_elem = item.select_one('.date')
                    if not date_elem:
                        continue
                        
                    date_text = date_elem.get_text(strip=True)
                    # 날짜에서 정규식을 통해 YYYY-MM-DD HH:MM 추출
                    date_match = re.search(r'(\d{{4}}-\d{{2}}-\d{{2}})\s+(\d{{2}}:\d{{2}}(?::\d{{2}})?)', date_text)
                    if date_match:
                        ext_date = date_match.group(1)
                        ext_time = date_match.group(2)
                        if len(ext_time) == 5:
                            ext_time += ":00"
                        full_date_time = f"{{ext_date}} {{ext_time}}"
                    else:
                        full_date_time = datetime.now().strftime("%Y-%m-%d 00:00:00")
                        
                    date_obj = datetime.strptime(full_date_time, '%Y-%m-%d %H:%M:%S')
                    
                    # 2. 날짜 필터링 (기간 이후의 기사면 건너뜀)
                    if date_obj.date() < cutoff_date:
                        continue
                        
                    found_in_range = True
                    
                    # 3. 링크 및 제목 추출 (TODO: 사이트 구조에 맞게 수정)
                    title_tag = item.select_one('h2 a')
                    if not title_tag:
                        continue
                        
                    title = title_tag.get_text(strip=True)
                    raw_link = title_tag['href']
                    link = raw_link if raw_link.startswith('http') else base_url + raw_link
                    
                    # 4. 상세페이지 본문 추출
                    content = ""
                    cat_main, cat_sub = "홈", "뉴스"
                    
                    try:
                        det_resp = requests.get(link, headers=headers, timeout=15)
                        det_resp.encoding = 'utf-8'
                        det_soup = BeautifulSoup(det_resp.text, 'html.parser')
                        
                        # 본문 영역 (TODO: 사이트 구조에 맞게 수정)
                        content_area = det_soup.select_one('.article-body')
                        if content_area:
                            # 안내문구, 스크립트, 광고 등 불필요 요소 제거
                            for tag in content_area.select('script, style, figure, .advertisement'):
                                tag.decompose()
                            content = content_area.get_text('\\n', strip=True)
                            
                    except Exception as det_e:
                        print(f"  ❌ 상세페이지 오류 ({{link}}): {{det_e}}")
                        
                    print(f"  [{provider_name}] 수집: {{full_date_time}} | {{title[:20]}}...")
                    
                    # 5. 데이터 적재
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
                    time.sleep(1) # 서버 트래픽 제어를 위한 대기
                    
                except Exception as item_e:
                    print(f"  ❌ 항목 파싱 오류: {{item_e}}")
                    continue
                    
            # 이번 페이지에서 지정된 기간 내의 기사를 찾지 못했다면 루프 종료
            if not found_in_range:
                break
                
            page += 1
            
        except Exception as list_e:
            print(f"❌ 목록 페이지 로드 오류: {{list_e}}")
            break
            
    return results

if __name__ == "__main__":
    print("{provider_name} 크롤러 단독 실행 테스트를 시작합니다...")
    crawled_data = get_{crawler_name}_data(days_to_scrape=1)
    
    if crawled_data:
        import os
        os.makedirs("output", exist_ok=True)
        today_str = datetime.now().strftime('%Y%m%d')
        filename = f"output/{{today_str}}_{provider_name}.csv"
        
        keys = crawled_data[0].keys()
        with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(crawled_data)
        
        print(f"✅ 테스트 수집 완료: 총 {{len(crawled_data)}}건이 '{{filename}}'에 성공적으로 저장되었습니다.")
    else:
        print("수집된 기사가 없습니다. 선택자(CSS Selector)나 사이트를 다시 확인해주세요.")
"""

def main():
    print("====================================")
    print("✨ 새로운 뉴스 크롤러 템플릿 생성기 ✨")
    print("====================================\n")
    
    crawler_name = input("1. 새 크롤러의 영문 이름을 입력하세요 (예: mynews, hankyung): ").strip().lower()
    if not crawler_name:
        print("이름을 꼭 입력해야 합니다. 프로그램을 종료합니다.")
        return
        
    provider_name = input("2. 뉴스 제공자의 한글 이름을 입력하세요 (예: 마이뉴스, 한국경제): ").strip()
    if not provider_name:
        provider_name = crawler_name
        
    base_url = input("3. 사이트 메인 주소를 입력하세요 (예: https://www.example.com): ").strip()
    if not base_url:
        base_url = "https://www.example.com"
        
    # 특수문자나 띄어쓰기 치환
    crawler_name_safe = crawler_name.replace(" ", "_").replace("-", "_")
    
    file_content = TEMPLATE.format(
        crawler_name=crawler_name_safe,
        provider_name=provider_name,
        base_url=base_url
    )
    
    filename = f"{crawler_name_safe}_crawler.py"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(file_content)
            
        print("\n\n🎉 템플릿 생성이 완료되었습니다! 🎉")
        print(f"✅ 새 파일 '{filename}' 이 생성되었습니다.")
        print("\n[다음 할 일]")
        print(f"1. 생성된 '{filename}'을 열어서 'TODO'라고 주석 처리된 부분을 실제 웹사이트 구조에 맞게 수정하세요.")
        print(f"   (특히 목록 페이지 URL, 뉴스 기사 목록 '.article-list > li' 등 CSS 선택자를 꼭 바꿔야 합니다.)")
        print(f"2. 단독 테스트를 위해 터미널에서 'python {filename}'을 실행해보며 검증하세요.")
        print("3. 문제가 없다면 'news_collector.py' 파일을 열어서 다음을 추가하세요:\n")
        print(f"   상단: import {crawler_name_safe}_crawler")
        print(f"   중간: crawler_tasks 리스트 안에 아래 한 줄 추가:")
        print(f"         {{\"name\": \"{provider_name}\", \"func\": {crawler_name_safe}_crawler.get_{crawler_name_safe}_data}}")
        
    except Exception as e:
        print(f"❌ 파일 생성 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main()
