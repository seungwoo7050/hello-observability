# Hello Observability

마이크로서비스 아키텍처를 위한 관측성 시스템 구축 프로젝트입니다. 이 프로젝트는 메트릭, 로그, 트레이스의 세 가지 핵심 관측성 요소를 수집하고 시각화하는 방법을 보여줍니다.

## 프로젝트 개요

이 프로젝트는 다음 구성 요소로 이루어져 있습니다:

1. **마이크로서비스**:
   - Product Service: 제품 정보 관리
   - Inventory Service: 재고 관리
   - Order Service: 주문 처리
   - Gateway Service: API 게이트웨이

2. **관측성 스택**:
   - Prometheus: 메트릭 수집
   - Loki: 로그 수집
   - Jaeger: 분산 추적
   - Grafana: 시각화

3. **프론트엔드**:
   - React 애플리케이션: 사용자 인터페이스

## 디렉토리 구조

```
hello-observability/
├── docker-compose.yml
├── observability/
│   ├── prometheus/
│   │   └── prometheus.yml
│   ├── grafana/
│   │   └── provisioning/
│   │       ├── dashboards/
│   │       │   ├── dashboards.yaml
│   │       │   └── microservices-dashboard.json
│   │       └── datasources/
│   │           └── datasources.yaml
│   ├── loki/
│   │   └── loki-config.yml
│   ├── promtail/
│   │   └── promtail-config.yml
│   └── jaeger/
├── services/
│   ├── product-service/
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── inventory-service/
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── order-service/
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── gateway-service/
│       ├── app.py
│       ├── requirements.txt
│       └── Dockerfile
├── frontend/
│   ├── public/
│   │   ├── index.html
│   │   ├── favicon.ico
│   │   └── manifest.json
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── index.js
│   │   └── index.css
│   ├── package.json
│   └── Dockerfile
└── load-test.py
```

## 설치 및 실행 방법

### 전제 조건

- Docker 및 Docker Compose 설치
- Git

### 설치 단계

1. 저장소 클론:
```bash
git clone https://github.com/yourusername/hello-observability.git
cd hello-observability
```

2. 시스템 실행:
```bash
docker-compose up -d
```

3. 서비스 상태 확인:
```bash
docker-compose ps
```

### 접속 주소

- 프론트엔드: http://localhost:3001
- API 게이트웨이: http://localhost:8080
- Grafana: http://localhost:3000 (기본 계정: admin/admin)
- Prometheus: http://localhost:9090
- Jaeger UI: http://localhost:16686

## 서비스 세부 정보

### Product Service (포트: 8081)

제품 정보를 관리하는 서비스입니다. 

API 엔드포인트:
- `GET /products`: 모든 제품 목록 조회
- `GET /products/{id}`: 특정 제품 조회
- `POST /products`: 새 제품 생성

### Inventory Service (포트: 8082)

재고를 관리하는 서비스입니다.

API 엔드포인트:
- `GET /inventory`: 전체 재고 조회
- `GET /inventory/{product_id}`: 특정 제품 재고 조회
- `PUT /inventory/{product_id}`: 재고 업데이트
- `POST /inventory/check`: 재고 가용성 확인

### Order Service (포트: 8083)

주문을 처리하는 서비스입니다.

API 엔드포인트:
- `GET /orders`: 모든 주문 조회
- `GET /orders/{id}`: 특정 주문 조회
- `POST /orders`: 새 주문 생성

### Gateway Service (포트: 8080)

API 게이트웨이 역할을 하는 서비스입니다.

API 엔드포인트:
- `/api/products*`: Product Service로 라우팅
- `/api/inventory*`: Inventory Service로 라우팅
- `/api/orders*`: Order Service로 라우팅

## 관측성 컴포넌트

### Prometheus (포트: 9090)

메트릭 수집 및 모니터링 도구입니다. 각 서비스의 성능 메트릭을 수집합니다.

주요 메트릭:
- HTTP 요청 수
- 응답 시간
- 오류율
- 시스템 자원 사용량

### Loki (포트: 3100)

로그 집계 시스템입니다. 모든 서비스의 로그를 중앙에서 수집합니다.

특징:
- 레이블 기반 로그 쿼리
- Grafana와 통합
- 경량 설계

### Jaeger (포트: 16686)

분산 추적 시스템입니다. 서비스 간 요청 흐름을 추적합니다.

특징:
- 엔드투엔드 트레이스 시각화
- 서비스 의존성 그래프
- 병목 현상 식별

### Grafana (포트: 3000)

데이터 시각화 도구입니다. Prometheus, Loki, Jaeger의 데이터를 통합하여 대시보드로 보여줍니다.

사전 구성된 대시보드:
- Microservices Dashboard: 서비스 요청률, 응답 시간, 오류율 등 표시

## 부하 테스트

프로젝트에는 부하 테스트를 실행하기 위한 스크립트가 포함되어 있습니다:

```bash
python load-test.py
```

이 스크립트는 다양한 API 엔드포인트에 요청을 보내 시스템에 부하를 생성합니다. 이를 통해 관측성 도구에서 패턴을 확인할 수 있습니다.

## 문제 해결

### 일반적인 문제

1. **서비스 시작 실패**:
   ```bash
   docker-compose logs [service-name]
   ```
   로그를 확인하여 오류 메시지를 찾습니다.

2. **Flask/Werkzeug 버전 호환성 문제**:
   각 서비스의 `requirements.txt`에 `flask==2.0.1`과 `werkzeug==2.0.1`이 명시되어 있는지 확인합니다.

3. **Loki 설정 오류**:
   `loki-config.yml`에 `allow_structured_metadata: false`가 추가되어 있는지 확인합니다.

4. **프론트엔드 빌드 실패**:
   필요한 모든 파일(특히 `public/index.html`)이 프론트엔드 디렉토리에 있는지 확인합니다.

### 서비스 재시작

특정 서비스만 재시작:
```bash
docker-compose restart [service-name]
```

전체 시스템 재시작:
```bash
docker-compose down
docker-compose up -d
```

## 학습 자료

이 프로젝트를 통해 다음과 같은 관측성 개념을 학습할 수 있습니다:

1. **메트릭 기반 모니터링**:
   - Prometheus를 사용한 메트릭 수집
   - PromQL 쿼리 작성
   - 알림 규칙 설정

2. **로그 관리**:
   - 구조화된 로깅
   - 중앙 집중식 로그 수집
   - 로그 쿼리 및 분석

3. **분산 추적**:
   - OpenTelemetry를 사용한 계측
   - 서비스 간 컨텍스트 전파
   - 트레이스 시각화 및 분석

4. **통합 관측성**:
   - 메트릭, 로그, 트레이스 상관 관계
   - 대시보드 설계
   - 인시던트 대응

## 확장 및 개선 방향

이 프로젝트는 다음과 같은 방향으로 확장할 수 있습니다:

1. **알림 통합**: Grafana 알림을 Slack, Email 등과 연동
2. **자동 복구 메커니즘**: 문제 감지 시 자동 조치 구현
3. **사용자 정의 메트릭**: 비즈니스 관련 메트릭 추가
4. **모니터링 대시보드 확장**: 더 많은 인사이트를 제공하는 대시보드 구성
5. **인프라 모니터링 추가**: 호스트 및 컨테이너 메트릭 통합

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 기여

이슈와 풀 리퀘스트를 통한 기여를 환영합니다!