# 나만의 AI 비서

BTC/USD 일별 시세 데이터(365일치)를 분석해 요약 정보를 만들고, 이 요약을 시스템 프롬프트에 주입해 "내 데이터를 아는" AI와 대화할 수 있는 서비스입니다. 데이터 CRUD와 대화 기록 저장/불러오기도 함께 제공합니다.

## 기술 스택

- 백엔드: FastAPI, Pydantic, firebase-admin, openai
- 데이터베이스: Firebase Firestore
- 프론트엔드: HTML / CSS / Vanilla JavaScript (프레임워크 미사용)
- 배포: 백엔드 Render, 프론트엔드 Vercel

## 설계 노트 (아키텍처 및 의사결정)

### 라우터/서비스 분리 기준

- `backend/routers/*.py`: HTTP 계층. 요청을 Pydantic 모델로 받고, 서비스 함수를 호출해 결과를 응답으로 돌려주는 역할만 한다. 경로·HTTP 메서드·상태 코드 외의 로직은 두지 않는다.
- `backend/services/*.py`: 비즈니스 로직 계층. Firestore 읽기/쓰기, 통계 계산, OpenAI 호출 등 실제 동작을 담당한다. FastAPI에 의존하지 않아 `seed_data.py` 같은 독립 스크립트나 다른 서비스에서도 그대로 재사용할 수 있다.
- 예: `data_service.list_data_points()`는 `GET /api/data`뿐 아니라 `chat_service._build_system_prompt()`에서도 그대로 재사용된다. 로직이 라우터 안에 있었다면 이런 재사용이 불가능하고 중복 구현됐을 것이다.

### Pydantic 검증을 쓴 이유

`schemas.py`의 모델이 요청을 FastAPI 엔드포인트 함수에 도달하기 전에 자동으로 검증한다. 예를 들어 `ChatRequest.message`는 1~2000자로 제한해 빈 메시지나 과도하게 긴 입력을 차단하고, `DataPointCreate.date`는 실제 날짜 형식만, `value`는 숫자 타입만 허용한다. 이 덕분에 서비스 로직에서 "입력이 이런 모양일 것"이라는 가정을 반복 검증할 필요가 없다. 다만 이 검증은 **형식**만 다룬다 — 욕설/유해어 필터링이나 프롬프트 인젝션 방어 같은 **내용** 검증은 구현하지 않았다. 개인용 데이터 비서라는 과제 범위를 벗어난다고 판단했고, 다중 사용자 서비스로 확장한다면 `chat_service.ask()` 앞단에 OpenAI Moderation API 같은 별도 콘텐츠 검사 단계를 추가하는 걸 권장한다.

### Firestore 컬렉션 스키마

**`data` 컬렉션** — 문서 1개 = 데이터 포인트 1개
| 필드 | 타입 | 설명 |
|---|---|---|
| `date` | string (`YYYY-MM-DD`) | 관측 날짜 |
| `value` | number | 관측 값 |
| `memo` | string \| null | 선택 메모 |

**`conversations` 컬렉션** — 문서 1개 = 대화 1개
| 필드 | 타입 | 설명 |
|---|---|---|
| `title` | string | 첫 사용자 메시지 앞 30자 또는 지정값 |
| `created_at` | Firestore Timestamp | 생성 시각 |
| `messages` | array<{role, content}> | 대화 전체 메시지 |

별도 인덱스는 두지 않았다 — 두 컬렉션 모두 수백~수천 문서 규모라 전체 조회 후 정렬(`data_service`의 파이썬 정렬, `conversation_service`의 `order_by("created_at")`)로 충분하다. 데이터가 수만 건 이상으로 커지면 복합 인덱스와 서버사이드 페이지네이션이 필요해진다.

### 대화 저장 방식과 시점

user+assistant 메시지 쌍은 사용자가 보낼 때가 아니라 **GPT 응답을 성공적으로 받은 직후**(`chat_service.ask` 끝부분)에 한 번에 저장한다. OpenAI 호출이 실패했을 때 질문만 있는 빈 대화가 남지 않도록 하기 위해서다. 대화 1건을 서브컬렉션 없이 `messages` 배열을 통째로 문서 하나에 저장하는 이유는, 이 과제 규모(대화당 메시지 수십 개 이내)에서는 문서 하나를 통째로 읽고 쓰는 게 가장 단순하고, "목록에서는 title/message_count만 가볍게, 개별 조회에서만 전체 messages를 읽는" 지금 구조와 맞기 때문이다. 메시지가 수천 개 이상으로 커지면 Firestore 문서 1MB 제한에 걸릴 수 있어 그때는 서브컬렉션 구조로 바꿔야 한다.

### 프론트엔드 상태 흐름

`app.js`는 `currentConversationId` 하나로 "지금 이어가는 대화"를 추적한다.
1. 메시지 전송 시 `currentConversationId`가 `null`이면 `/api/chat`이 새 대화를 만들어 id를 돌려주고, 이후 메시지는 같은 id로 계속 이어 붙는다.
2. "새 대화 시작" 버튼은 `currentConversationId`를 `null`로 되돌리고 화면 메시지를 비운다.
3. 대화 기록 탭에서 "불러오기"를 누르면 `GET /api/conversations/{id}`로 전체 메시지를 가져와 `currentConversationId`를 그 id로 설정하고, 화면에 메시지를 재구성한 뒤 채팅 탭으로 전환한다. 이후 이어서 보내는 메시지는 불러온 대화에 계속 append된다.

### 컨텍스트 주입 방식 — 의도와 한계

**의도**: GPT는 기본적으로 사용자의 개인 데이터를 모른다. `/api/chat`이 호출될 때마다 `build_summary()`로 최신 데이터 요약을 계산해 시스템 프롬프트 맨 앞에 텍스트로 삽입함으로써, 별도 파인튜닝이나 벡터DB 없이도 "내 데이터를 아는 것처럼" 답하게 만드는 가장 단순한 방법이다.

**한계**:
- "요약"만 넘기기 때문에 개별 데이터 포인트 단위의 세밀한 질문(예: "3월 15일 값이 뭐야?")에는 정확히 답하지 못할 수 있다. 이런 질문까지 다루려면 관련 원본 데이터를 직접 조회해 프롬프트에 넣거나(RAG), Function Calling으로 필요할 때 API를 부르게 하는 방식이 더 적합하다 (보너스 과제 영역).
- 데이터가 매우 커지면(수만 건 이상) 매 요청마다 요약을 다시 계산하는 비용이 커질 수 있다 — 현재 365개 규모에서는 문제되지 않는다.
- 요약이 매 요청 최신 데이터 기준으로 갱신되는 건 장점이자, 대화가 길어질 경우 이전 답변 시점의 요약과 최신 요약이 미묘하게 달라질 수 있다는 점에서 일관성 이슈가 될 수 있다.

### 요약 로직을 별도 모듈로 뺀 이유

`analysis_service.build_summary()`는 `GET /api/data/summary` 라우터와 `chat_service._build_system_prompt()` 양쪽에서 동일하게 재사용된다. 이 계산이 라우터 안에 있었다면 "API로 보여주는 요약"과 "AI에게 주는 요약"이 서로 다른 코드로 중복 구현되면서 언젠가 둘이 어긋날 위험이 있다. `List[DataPoint] -> DataSummary`만 다루는 순수 함수(Firestore·FastAPI 의존성 없음)로 분리해뒀기 때문에 별도 스크립트나 테스트에서도 바로 재사용·검증할 수 있다.

**요약 기준(트렌드 윈도우) 변경 방법**: `analysis_service.py`의 `window = max(1, min(30, count // 2))`가 "최근 트렌드"를 계산할 때 비교하는 구간 크기(기본 최대 30개)를 정한다. 윈도우 크기를 바꾸려면 이 파일의 `30`이라는 상수만 고치면 된다. 특정 기간(예: 최근 30일)만 잘라서 요약하고 싶다면, `build_summary()`를 호출하기 전에 `points` 리스트를 `date` 기준으로 필터링해서 넘기면 된다 — 라우터나 `chat_service`에서 날짜 범위 파라미터를 추가로 받는 방식으로 확장 가능하다.

## 배포 URL

- 프론트엔드: https://cody-m1-2.vercel.app
- 백엔드 API: https://cody-m1-2.onrender.com
- Swagger UI: https://cody-m1-2.onrender.com/docs

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
| `OPENAI_MODEL` | 사용할 모델 (기본값 `gpt-4o-mini`. 코디세이 프록시 사용 시 `gpt-5-mini`) |
| `OPENAI_BASE_URL` | (선택) OpenAI 호환 프록시 주소. 코디세이 virtual-key 사용 시 `https://copa.codyssey.kr/v1` |
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

## 실행 증거 (배포 환경 curl 검증)

2026-09-17 기준, 배포된 URL에 직접 curl로 요청해 확인한 결과입니다.

```
$ curl -o /dev/null -w "%{http_code}" https://cody-m1-2.vercel.app/
200

$ curl https://cody-m1-2.onrender.com/
{"status":"ok"}

$ curl -o /dev/null -w "%{http_code}" https://cody-m1-2.onrender.com/docs
200
$ curl -o /dev/null -w "%{http_code}" https://cody-m1-2.onrender.com/openapi.json
200

$ curl https://cody-m1-2.onrender.com/api/data/summary
{"period":"2025-09-15 ~ 2026-09-14","count":365,"metrics":{"total":29669978.78,"average":81287.61,"max":124739.81,"min":58566.09},"trend":"상승 (최근 30개 구간 평균 대비 +18.3%)"}
```

데이터 CRUD 라운드트립(추가 → 목록에 반영 확인 → 삭제):

```
$ curl -X POST https://cody-m1-2.onrender.com/api/data \
    -H "Content-Type: application/json" \
    -d '{"date":"2026-09-17","value":99999,"memo":"평가용 테스트 데이터"}'
{"id":"waLnaJCBbvSzYbYOPDDH","date":"2026-09-17","value":99999.0,"memo":"평가용 테스트 데이터"}

# GET /api/data 목록 366개 중 방금 추가한 id 포함 확인됨
# DELETE /api/data/waLnaJCBbvSzYbYOPDDH -> 200 (정리 완료)
```

대화 저장 → 목록 조회 → 개별 불러오기 라운드트립:

```
$ curl -X POST https://cody-m1-2.onrender.com/api/chat \
    -H "Content-Type: application/json" \
    -d '{"message":"이번 달 실적이 어때?"}'
{"reply":"...데이터 요약을 근거로 한 답변...","conversation_id":"3HSLwPY2YORNfk3z6puZ"}

$ curl https://cody-m1-2.onrender.com/api/conversations
# 방금 저장된 conversation_id가 목록에 title/message_count와 함께 포함됨

$ curl https://cody-m1-2.onrender.com/api/conversations/{id}
# 저장했던 user/assistant 메시지 2개가 그대로 반환됨 (불러오기 확인)
```

## 제출 스크린샷

- [x] 데이터 요약이 보이는 채팅 화면 (질문 + 답변 포함)
![alt text](<스크린샷 2026-09-17 오후 10.30.35.png>)
- [x] 데이터 관리 화면 (CRUD 중 1개 동작이 보이도록)
![alt text](<스크린샷 2026-09-17 오후 10.31.52.png>)
- [x] 대화 기록 화면 (불러오기 동작이 보이도록)
![alt text](<스크린샷 2026-09-17 오후 10.32.31.png>)


