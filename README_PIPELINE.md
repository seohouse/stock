창원개미 모의 트레이드 파이프라인(요약)

개요
- 이 파이프라인은 '창원개미' 전략의 모의(모크) 실행 환경입니다.
- 목표: HTS 첫화면 스캔(Top‑M → Top‑1) → 전일대비 거래량비 계산 → 창원개미 규칙(Top‑1, 매수=지정가 IOC, 매도=시장가 전량, 동기매매)으로 모의 주문을 실행
- 모든 거래는 모의(파일 기반 로그)로 기록되며, 실계좌 연결 전 검증용입니다.

주요 파일
- mock_ws_server.py
  - 로컬 WebSocket 서버(포트 8765)를 실행합니다. 틱/체결 이벤트를 브로드캐스트합니다.
- aggregator_ws.py
  - WS에 접속하여 틱 스트림을 처리하고 심볼별 누적거래량(today_cum), 체결강도(trade_intensity)를 집계합니다.
- kiwoom_rest_loader_mock.py
  - REST 엔드포인트를 모의하는 로더(전일거래량 등)입니다. 실제 Kiwoom REST 대신 사용.
- aggregator_mock.py
  - WS 대신 랜덤 모의 데이터로 aggregator 역할을 하는 스텁입니다.
- scanner_core_mock.py
  - 전체 스캐너/스코어/트레이드 플로우의 핵심입니다.
  - Top‑M 조회(모의) → prev_day 조회(모의) → aggregator에서 오늘 누적 불러옴 → score 계산 → Top‑1 선정 → 임계치 통과 시 OrderManagerStub로 매수/매도
- order_manager_stub.py
  - 모의 주문 실행기(지정가 매수 IOC, 시장가 매도). logs/mock_orders.log에 거래 로그를 남깁니다.
- run_mock_trade.py
  - 간단한 1회 모의 트레이드 실행 스크립트(Top‑1 선정 → 매수→대기→매도)
- logs/mock_orders.log
  - 주문/체결 로그(파일 경로에 생성됨)

실행 가이드(모의 E2E)
1) 로그 디렉토리 생성
   mkdir -p logs

2) 단일 데모 실행
   python3 scanner_core_mock.py
   또는
   python3 run_mock_trade.py

3) (옵션) WS 기반 aggregator 실행
   - 먼저 mock WS 서버(별 터미널) 실행:
     python3 mock_ws_server.py
   - 다른 터미널에서 aggregator_ws.py 실행:
     python3 aggregator_ws.py
   - scanner_core_mock.py에서 aggregator_ws로부터 실시간 데이터를 사용하도록 연결하려면 scanner_core_mock을 약간 수정해 AggregatorWS 인스턴스를 주입하세요.

코드 정리·주석
- 각 파일에 최소한의 함수/클래스 설명과 실행 흐름 주석을 추가했습니다.
- 모듈 경계: REST loader(전일 데이터), aggregator(실시간 틱 집계), scanner(스코어·순위·진입), order manager(주문 실행)로 명확히 분리되어 있습니다.

동작 원리 요약
1) scanner_core_mock는 Top‑M 리스트를 얻습니다(모의).  
2) 각 심볼에 대해 prev_day(prev_volume)와 today_cum, trade_intensity를 조회합니다.  
3) 간단한 composite score를 계산하고 Top‑1을 선택합니다.  
4) volume_ratio 임계치(기본 1.5)를 통과하면 order_manager_stub로 매수(지정가 IOC) 후 2초 대기 후 시장가 전량 매도합니다.

확장/다음 단계
- 실제 Kiwoom REST/WS 연동: kiwoom_rest_loader.py와 ws 클라이언트를 구현하여 실 데이터에 연결
- TokenManager 통합: kiwoom_token_manager.py를 사용해 OAuth 토큰 관리 추가
- OrderManager 실연동: order_manager_stub → 실제 주문 래퍼로 교체(안전장치 필수)
- 모니터링: 로그 기반 대시보드/metrics(예: Prometheus) 추가

안전
- 현재 모든 주문은 모의입니다. 실거래 전에는 .env나 실제 API 키를 사용해 실계좌로 이동하기 전에 충분한 검증이 필요합니다.

문의
- 파일별 동작 설명이나 추가 주석/테스트를 원하시면 어느 파일을 우선 보강할지 알려주세요.
