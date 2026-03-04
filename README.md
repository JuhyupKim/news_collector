# 뉴스 자동 수집 및 분류 크롤러 프로젝트 (News Scraper Suite)

본 프로젝트는 여러 IT 및 가전, 기술 매체의 뉴스 기사들을 주기적으로 스크랩하여 지정된 형식의 단일 데이터세트(CSV)로 통합하는 자동화 파이프라인입니다.

## 📌 주요 기능
1. **멀티스레딩 고속 수집**: 5개의 개별 뉴스 크롤러 모듈이 독립적으로 작동하며, `news_collector.py`를 통해 모든 크롤러가 동시에 병렬(Asynchronous)로 데이터를 수집하여 속도를 극대화합니다.
2. **동적 카테고리 매핑**: 하드코딩된 분류가 아닌, 각 기사 본문과 메타데이터(`<title>` 태그 분석, Breadcrumbs 형태 등)를 역추적하여 사이트의 네이티브 메인 카테고리(`category_main`)와 서브 카테고리(`category_sub`)를 자동으로 추출합니다.
3. **정밀한 시간 포맷팅**: 웹사이트별로 제각각인 날짜 포맷(예: `YYYY.MM.DD HH:MM`, `YYYY/MM/DD` 등)을 분석하여 `YYYY-MM-DD HH:MM:SS` 형식의 19자리 표준 문자열로 정규화합니다.

## 🗂 프로젝트 구조
```text
newsletter/
├── output/                   # 성공적으로 병합된 최종 결과물(CSV)이 저장되는 디렉터리
├── temp/                     # 임시 추출물, 엑셀 로그, PDF 레퍼런스 등이 격리된 임시 폴더
├── tests/                    # 개별 크롤러 동작 검증이나 실험을 위한 격리 폴더
├── news_collector.py         # 모든 크롤러 스크립트를 Multi-threading으로 동시 구동하는 메인 파이프라인
├── zdwang_news_crawler.py    # ZDWang(중국 IT) 뉴스 전용 크롤러
├── samsung_crawler.py        # 삼성 뉴스룸 전용 크롤러 (Selenium 기반)
├── cheaa_crawler.py          # CHEAA 뉴스 전용 크롤러
├── techworld_crawler.py      # 테크월드뉴스 전용 크롤러
└── irobotnews_crawler.py     # 로봇신문 전용 크롤러
```

## 🚀 사용 방명 및 실행 흐름
가장 중심이 되는 메인 스크립트를 실행하면 전체 수집이 시작됩니다:
```bash
python news_collector.py
```

### 실행 내부 로직
1. `news_collector.py` 실행 시 지정된 `DATE_THRESHOLD`(예: 최근 1일치)를 기준 삼아 5개의 크롤러가 `ThreadPoolExecutor`를 통해 동시 실행됩니다.
2. **사전 렌더링 검열 (Lazy Load)**: Selenium 등 메모리 소모가 심한 크롤러(`samsung_crawler`)는 백그라운드 스레드가 해당 함수를 구동할 때만 인스턴스를 발생시키도록 최적화되어 있습니다.
3. **콘솔 인코딩 방어**: 윈도우 커맨드라인에서 이모지(Emoji) 출력으로 인해 발생할 수 있는 `cp949` 오류를 방지하고자 Python 내부에 `utf-8` I/O Wrapper가 설치되어 있습니다.
4. 모든 병렬 수집이 완료되면 취합된 파이썬 Dictionary 리스트 데이터를 날짜 역순으로 정렬한 뒤, `./output/[YYMMDD_HHMMSS]_competitor.csv`로 저장됩니다.

## 🛠 필수 의존성 (Dependencies)
스크립트를 실행하려면 다음과 같은 라이브러리들이 필요합니다.
```bash
pip install requests beautifulsoup4 pandas selenium webdriver-manager deep-translator
```
- **requests / beautifulsoup4**: 일반적인 정적 웹페이지 통신 및 HTML 구문 분석
- **pandas**: 리스트 형태의 딕셔너리를 단일 데이터프레임 구조로 병합 후 `.csv` 변환
- **selenium / webdriver-manager**: 자바스크립트 렌더링이 필수적인 동적 페이지 구조(Samsung 등) 수집
- **deep-translator**: 수집된 중국어 뉴스 기사의 실시간 한국어 번역 지원

## 📝 크롤러별 추출 특징
- **ZDWang**: 웹 카테고리 맵 리스트 기반 Native Mapping
- **Samsung**: Selenium 내 브라우저 탐색 후 `<json-ld>` 메타데이터 파싱 및 `>` Breadcrumbs 분류
- **Techworld / IRobotNews**: 텍스트 형태 `<title>` 헤더 내 `<` 구분 심볼 스플릿 기반의 정밀 추출
- **CHEAA**: `<title>` 본문 내 배정된 특정 하이픈 `-` 심볼을 기반으로 카테고리 동적 분리
