# Selenium IDE Runner

Selenium IDE로 작성한 테스트 시나리오를 Selenium Grid를 통해 병렬 실행하여 QA 테스트 시간을 대폭 단축하는 프로젝트입니다.

## 주요 기능

- 🚀 **병렬 실행**: Selenium Grid를 활용하여 여러 테스트를 동시에 실행
- 📊 **실시간 모니터링**: noVNC를 통해 각 Chrome 노드의 실행 과정을 실시간으로 확인 가능
- 📁 **일괄 실행**: `scenarios/` 폴더의 모든 `.side` 파일을 자동으로 실행
- 📝 **결과 리포트**: JSON 형식으로 테스트 결과를 저장하고 분석 가능
- 🔍 **실패 테스트 분석**: `parser.py`를 통해 실패한 테스트만 추출하여 빠른 디버깅
- 🌐 **HTTP API**: FastAPI를 통한 RESTful API로 컨테이너 간 통신 및 원격 제어 가능

## 프로젝트 구조

```
selenium-ide-runner/
├── docker-compose.yml    # Selenium Grid 및 API 서비스 설정
├── Dockerfile            # FastAPI 애플리케이션 Docker 이미지
├── main.py               # FastAPI 애플리케이션
├── requirements.txt      # Python 의존성
├── init.sh               # 초기 설정 스크립트
├── run.sh                # 테스트 실행 스크립트
├── parser.py             # 실패 테스트 분석 유틸리티
├── scenarios/            # Selenium IDE 테스트 파일 (.side)
└── reports/              # 테스트 결과 JSON 파일
```

## 사전 요구사항

- Docker 및 Docker Compose
- Node.js 및 npm
- Bash 쉘

## 설치 및 설정

### 1. 초기 설정

프로젝트를 처음 사용하는 경우, 다음 명령어로 필요한 도구들을 설치합니다:

```bash
./init.sh
```

이 스크립트는 다음을 설치합니다:
- `selenium-side-runner`: Selenium IDE 테스트 실행 도구
- `chromedriver`, `geckodriver`: 브라우저 드라이버

### 2. Selenium Grid 시작

Docker Compose를 사용하여 Selenium Hub와 Chrome 노드들을 시작합니다:

```bash
docker-compose up -d
```

이 명령어는 다음을 시작합니다:
- **Selenium Hub**: 포트 `4444`에서 실행
- **FastAPI 서버**: 포트 `8000`에서 실행
- **Chrome Node 1**: noVNC 포트 `7901`로 노출
- **Chrome Node 2**: noVNC 포트 `7902`로 노출

### 3. Grid 상태 확인

브라우저에서 다음 URL을 열어 Selenium Grid 상태를 확인할 수 있습니다:

```
http://localhost:4444
```

## 사용 방법

### 방법 1: HTTP API 사용 (권장)

FastAPI를 통해 HTTP 요청으로 테스트를 관리하고 실행할 수 있습니다.

#### API 엔드포인트

- **GET /sides**: 사이드 파일 목록 조회
- **GET /sides/{side_id}**: 사이드 파일 다운로드
- **POST /sides/{side_id}**: 사이드 파일 재현 (Selenium Grid로 실행)
- **PATCH /sides/{side_id}**: 사이드 파일 업로드
- **DELETE /sides/{side_id}**: 사이드 파일 삭제
- **GET /health**: 헬스 체크

#### API 사용 예시

```bash
# 사이드 파일 목록 조회
curl http://localhost:8000/sides

# 사이드 파일 업로드
curl -X PATCH http://localhost:8000/sides/my-test \
  -F "file=@/path/to/my-test.side"

# 사이드 파일 실행
curl -X POST http://localhost:8000/sides/my-test

# 사이드 파일 다운로드
curl http://localhost:8000/sides/my-test -o my-test.side

# 사이드 파일 삭제
curl -X DELETE http://localhost:8000/sides/my-test
```

#### API 문서

서버 실행 후 다음 URL에서 자동 생성된 API 문서를 확인할 수 있습니다:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 방법 2: 로컬 스크립트 사용

`scenarios/` 폴더에 있는 모든 `.side` 파일을 병렬로 실행합니다:

```bash
./run.sh
```

실행 결과는 `reports/` 폴더에 타임스탬프가 포함된 JSON 파일로 저장됩니다.

### 실시간 모니터링

테스트 실행 중 각 Chrome 노드의 브라우저 화면을 실시간으로 확인할 수 있습니다:

- **Chrome Node 1**: http://localhost:7901
- **Chrome Node 2**: http://localhost:7902

noVNC 비밀번호: `q1w2e3r4`

### 실패한 테스트 분석

테스트 실행 후 실패한 테스트만 추출하여 분석할 수 있습니다:

```bash
# JSON 형식으로 출력
python parser.py reports/results-YYYY-MM-DDTHH-MM-SS.json

# 평문 형식으로 출력 (가독성 향상)
python parser.py reports/results-YYYY-MM-DDTHH-MM-SS.json --plain
```

## 테스트 시나리오 추가

### API를 통한 업로드 (권장)

```bash
curl -X PATCH http://localhost:8000/sides/{side_id} \
  -F "file=@/path/to/your-test.side"
```

### 직접 파일 복사

1. Selenium IDE에서 테스트를 작성하고 `.side` 파일로 내보내기
2. `scenarios/` 폴더에 `.side` 파일 복사
3. `./run.sh` 실행 시 자동으로 포함되어 실행됩니다

## Selenium Grid 구성

현재 설정은 다음과 같습니다:

- **Hub**: 1개 (포트 4444)
- **Chrome Nodes**: 2개
  - 각 노드는 최대 1개의 세션만 실행 (`SE_NODE_MAX_SESSIONS=1`)
  - 병렬 실행을 위해 각 노드가 독립적으로 테스트를 처리

더 많은 병렬 실행이 필요한 경우 `docker-compose.yml`에 추가 Chrome 노드를 추가할 수 있습니다.

## 문제 해결

### Grid에 연결할 수 없는 경우

1. Docker 컨테이너가 실행 중인지 확인:
   ```bash
   docker-compose ps
   ```

2. Hub가 정상적으로 시작되었는지 확인:
   ```bash
   docker-compose logs selenium-hub
   ```

### 테스트가 실행되지 않는 경우

1. API 서버가 정상적으로 실행 중인지 확인:
   ```bash
   curl http://localhost:8000/health
   ```

2. API 서버 로그 확인:
   ```bash
   docker-compose logs api
   ```

3. `selenium-side-runner`가 설치되어 있는지 확인 (로컬 실행 시):
   ```bash
   which selenium-side-runner
   ```

4. `scenarios/` 폴더에 `.side` 파일이 있는지 확인

### noVNC에 접속할 수 없는 경우

1. 포트가 올바르게 노출되었는지 확인:
   ```bash
   docker-compose ps
   ```

2. 컨테이너 로그 확인:
   ```bash
   docker-compose logs chrome-node-1
   docker-compose logs chrome-node-2
   ```

## 정리

모든 컨테이너를 중지하고 제거하려면:

```bash
docker-compose down
```

## 라이선스

이 프로젝트는 개인 사용 목적으로 작성되었습니다.

