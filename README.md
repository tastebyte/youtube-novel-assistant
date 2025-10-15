# 유튜브소설어시스트

AI를 활용한 유튜브 소설 제작 도구

## 기능

- 📝 **대본 입력**: 소설의 전체 대본을 입력
- 👥 **등장인물 자동 추출**: AI가 대본에서 등장인물을 자동으로 찾아냄
- 🎨 **캐릭터 이미지 생성**: 각 등장인물의 일관된 이미지 생성
- 🎬 **장면 자동 분리**: 대본을 개별 장면으로 자동 분할
- 🖼️ **장면 이미지 생성**: 각 장면에 맞는 이미지 자동 생성
- 💾 **저장 및 관리**: 모든 데이터를 체계적으로 저장하고 관리

## 설치 및 실행

### 1. 필요한 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

**방법 1: .env 파일 사용**
```bash
cp .env.example .env
```

`.env` 파일을 편집하여 실제 API 키를 입력:
```
GEMINI_API_KEY=실제_제미나이_API_키
```

**방법 2: Streamlit Secrets 사용 (권장)**
```bash
mkdir -p .streamlit
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

`.streamlit/secrets.toml` 파일을 편집:
```toml
GEMINI_API_KEY = "실제_제미나이_API_키"
```

### 3. 애플리케이션 실행

```bash
streamlit run main.py
```

## 프로젝트 구조

```
├── main.py              # 메인 애플리케이션
├── requirements.txt     # 필요한 패키지 목록
├── .env.example        # 환경 변수 예시
├── src/
│   ├── __init__.py
│   ├── models.py       # 데이터 모델
│   ├── utils.py        # 유틸리티 함수
│   ├── data_manager.py # 데이터 관리 (구현 예정)
│   ├── api_clients.py  # API 클라이언트 (구현 예정)
│   └── workflow.py     # 워크플로우 엔진 (구현 예정)
└── data/               # 데이터 저장 디렉토리 (자동 생성)
```

## 개발 상태

현재 기본 구조가 완성되었으며, 다음 기능들을 순차적으로 구현 중입니다:

- [x] 프로젝트 기본 구조 및 환경 설정
- [ ] 데이터 관리자 구현
- [ ] API 클라이언트 구현
- [ ] 자동화 워크플로우 구현
- [ ] UI 개선 및 기능 추가

## 라이선스

MIT License