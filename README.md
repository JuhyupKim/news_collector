## 📝 크롤러별 추출 특징
- **ZDWang**: 웹 카테고리 맵 리스트 기반 Native Mapping
- **Samsung**: Selenium 내 브라우저 탐색 후 `<json-ld>` 메타데이터 파싱 및 `>` Breadcrumbs 분류
- **Techworld / IRobotNews**: 텍스트 형태 `<title>` 헤더 내 `<` 구분 심볼 스플릿 기반의 정밀 추출
- **CHEAA**: `<title>` 본문 내 배정된 특정 하이픈 `-` 심볼을 기반으로 카테고리 동적 분리
