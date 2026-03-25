import pandas as pd
import os
import sys
import io
from datetime import datetime
import concurrent.futures

# utf-8 for console output robustness
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import zdwang_crawler
import cheaa_crawler
import samsung_crawler
import techworld_crawler
import irobotnews_crawler
import google_news_crawler

# oo일전 뉴스부터 수집
DATE_THRESHOLD = 1

# 1. 설정값 상수화
COLUMNS = [
    'title', 'content', 'enveloped_at', 'date', 'provider',
    'category_main', 'category_sub', 'reporter', 'provider_link_page',
    'useful', 'strategy_agenda', 'content_summary', 'category1', 'category2',
    'YEAR', 'MONTH', 'WEEK'
]

print(f"\n🚀 최근 {DATE_THRESHOLD}일치 데이터 수집을 시작합니다...")

import businesspost_crawler

# 2. 크롤러 등록 (작업 리스트화)
# 각 크롤러의 인스턴스나 실행 함수를 리스트에 담아 관리합니다.
# 만약 앞서 리팩토링한 것처럼 클래스 형태라면 인스턴스를 생성합니다.
crawler_tasks = [
    {"name": "ZDWANG", "func": zdwang_crawler.get_zdwang_data},
    {"name": "CHEAA", "func": cheaa_crawler.get_cheaa_data},
    {"name": "SAMSUNG", "func": lambda days: samsung_crawler.SamsungCrawler().run(days)},
    {"name": "TECHWORLD", "func": techworld_crawler.scrape_techworld_news},
    {"name": "IROBOTNEWS", "func": irobotnews_crawler.get_irobotnews_data},
    {"name": "BUSINESSPOST", "func": businesspost_crawler.get_businesspost_data},
    {"name": "GOOGLE_NEWS", "func": google_news_crawler.get_google_news_data}
]

all_data = []

# 3. 비동기/멀티스레딩을 통한 자동화 수집
def execute_crawler(task):
    try:
        print(f"--- {task['name']} 수집 중 ---")
        data = task['func'](DATE_THRESHOLD)
        if data:
            print(f"✅ {task['name']}: {len(data)}건 수집 완료")
            return data
        else:
            print(f"⚠️ {task['name']}: 수집된 데이터 없음")
            return []
    except Exception as e:
        print(f"❌ {task['name']} 수집 실패: {e}")
        return []

with concurrent.futures.ThreadPoolExecutor(max_workers=len(crawler_tasks)) as executor:
    # 각 크롤러 태스크를 비동기로 실행
    futures = [executor.submit(execute_crawler, task) for task in crawler_tasks]
    for future in concurrent.futures.as_completed(futures):
        all_data.extend(future.result())

if not all_data:
    print("최종 수집된 데이터가 없습니다.")

# 4. 데이터프레임 생성 및 통합 후처리
df_result = pd.DataFrame(all_data)

# 존재하지 않는 컬럼 빈 값으로 생성
for col in COLUMNS:
    if col not in df_result.columns:
        df_result[col] = ""

# 컬럼 순서 고정 및 날짜 정렬
df_result = df_result[COLUMNS]
df_result = df_result.sort_values(by=['date', 'enveloped_at'], ascending=False).reset_index(drop=True)

# 5. 절대 경로를 사용한 안전한 파일 저장
base_dir = os.path.dirname(os.path.abspath(__file__))
db_dir = os.path.join(base_dir, 'output')
os.makedirs(db_dir, exist_ok=True)

today_str = datetime.now().strftime('%y%m%d_%H%M%S')
save_path = os.path.join(db_dir, f"{today_str}_competitor.csv")
df_result.to_csv(save_path, encoding='utf-8-sig', index=False)
print(f"📁 결과 저장 완료: {save_path}")

# 기존 크롤링 자료와 통합 파트는 현재 db_crawling이 정의되어 있지 않으므로 주석 처리
# if not df_result.empty:
#     df_crawling = pd.concat([df_crawling, df_result], axis=0, ignore_index=True)