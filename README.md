# 나만의 AI 비서

BTC/USD 일별 시세 데이터(365일치)를 분석해 요약 정보를 만들고, 이 요약을 시스템 프롬프트에 주입해 "내 데이터를 아는" AI와 대화할 수 있는 서비스입니다. 데이터 CRUD와 대화 기록 저장/불러오기도 함께 제공합니다.

## 기술 스택

- 백엔드: FastAPI, Pydantic, firebase-admin, openai
- 데이터베이스: Firebase Firestore
- 프론트엔드: HTML / CSS / Vanilla JavaScript (프레임워크 미사용)
- 배포: 백엔드 Render, 프론트엔드 Vercel

## 배포 URL

- 프론트엔드: (배포 후 작성)
- 백엔드 API: (배포 후 작성)
- Swagger UI: (배포 후 작성)/docs

## 로컬 실행 방법

### 백엔드

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 값 채워넣기
uvicorn main:app --reload
```

- 서버: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs

초기 데이터가 필요하면 (한 번만 실행):

```bash
python seed_data.py
```

### 프론트엔드

`frontend/config.js`의 `API_BASE_URL`이 로컬 백엔드 주소(`http://127.0.0.1:8000`)를 가리키는지 확인한 뒤:

```bash
cd frontend
python3 -m http.server 5500
```

브라우저에서 http://127.0.0.1:5500 접속.

## 환경 변수

| 변수 | 설명 |
|---|---|
| `OPENAI_API_KEY` | OpenAI API 키 |
| `OPENAI_MODEL` | 사용할 모델 (기본값 `gpt-4o-mini`) |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Firebase 서비스 계정 키. JSON 문자열 전체를 넣거나(Render 권장), 로컬에서는 키 파일 경로를 넣어도 됨 |
| `ALLOWED_ORIGINS` | CORS 허용 origin, 콤마로 구분 (예: 프론트엔드 배포 주소) |
| `API_BASE_URL` (Vercel 빌드 전용) | 프론트엔드가 호출할 백엔드 주소. Vercel 프로젝트 환경 변수에 설정하면 `build.sh`가 빌드 시점에 `config.js`에 주입함 |

## 계정/키 준비 가이드 (처음 하는 경우)

1. **Firebase**: https://console.firebase.google.com 에서 새 프로젝트 생성 → 왼쪽 메뉴 Firestore Database → 데이터베이스 만들기(테스트 모드로 시작) → 프로젝트 설정 → 서비스 계정 → "새 비공개 키 생성"으로 JSON 키 다운로드.
2. **OpenAI**: https://platform.openai.com/api-keys 에서 API 키 발급. 결제 정보 등록 필요 (사용량 제한을 꼭 설정할 것).
3. **Render**: https://render.com 가입(GitHub 연동) → New Web Service → 이 저장소 연결 → Root Directory `backend`, Build Command `pip install -r requirements.txt`, Start Command `uvicorn main:app --host 0.0.0.0 --port $PORT` → Environment 탭에서 위 환경 변수 등록.
4. **Vercel**: https://vercel.com 가입(GitHub 연동) → New Project → 이 저장소 연결 → Root Directory `frontend`, Build Command `sh build.sh`, Output Directory `.` → Environment Variables에 `API_BASE_URL`(Render 배포 URL)을 등록.

## Render 무료 플랜 콜드 스타트 안내

무료 플랜은 일정 시간 요청이 없으면 서버가 잠들고, 첫 요청 시 다시 깨어나는 데 최대 1분 정도 걸릴 수 있습니다. 프론트엔드는 페이지 로드 시 백엔드에 미리 핑을 보내고, 응답이 늦어지면 "서버를 깨우는 중" 안내 배너를 보여줍니다.

## 데이터 출처

`data/btc_usd_365d.csv` — CoinGecko 공개 API(`/coins/bitcoin/market_chart`)에서 수집한 BTC/USD 365일 일별 종가. API 키 불필요, 비상업적 학습 목적 사용 가능.

## 제출 스크린샷

아래 화면을 캡처해 이 섹션에 추가하세요.

- [ ] 데이터 요약이 보이는 채팅 화면 (질문 + 답변 포함)
- [ ] 데이터 관리 화면 (CRUD 중 1개 동작이 보이도록)
- [ ] 대화 기록 화면 (불러오기 동작이 보이도록)

## 보너스 과제 (미구현)

Function Calling/MCP 연동, 통계 확장, 그래프 시각화, CSV/JSON 내보내기, 다크 모드는 시간이 되면 추가할 선택 항목입니다.
