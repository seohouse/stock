README: 비동기 전환 요약 (한글)

목표
- 기존 동기 파이프라인을 asyncio 기반 비동기 파이프라인으로 전환하여 WS/REST/IO 동시처리 성능을 개선하고 통합 테스트를 용이하게 함.

완료된 작업
1) 패키지
- .venv에 aiohttp, aiofiles 설치

2) 비동기화 주요 변경
- order_manager_stub.py
  - 동기 -> 비동기 전환
  - aiofiles로 로그 비동기 기록, asyncio.Lock 사용
  - async place_buy_limit / place_sell_market / get_positions 제공

- position_manager.py
  - asyncio 기반 모니터(Task)로 전환
  - async start_monitor / stop_monitor / open_position 제공
  - 기존 부분익절/전량익절/트레일링/손절/타임컷 로직을 await 오더 호출로 실행

- scanner_core_ws.py
  - 주문 호출부를 await로 비동기 호출하도록 변경
  - AggregatorWS 연결을 asyncio.create_task로 백그라운드 실행

- scanner_with_pm.py
  - sync 스크립트를 async로 변환(main()을 asyncio.run으로 실행)
  - PositionManager/OrderManager의 async API를 사용하도록 수정

- kiwoom_token_manager.py
  - async_auth_request, async_get_access_token 추가(aiohttp 기반 또는 sync TokenManager와 브리지)
  - 기존 sync TokenManager는 보존(호환성 목적)

- kiwoom_rest_client_async.py
  - mock 전용 async REST 함수 추가(get_prev_close, get_ohlcv, place_order, get_positions)

3) 테스트 및 결과
- 단위/스모크 테스트 수행
  - OrderManagerStub 단위 테스트: 성공
  - PositionManager 통합 스모크: 성공(부분익절/전량익절 동작 확인)
- 가속화된 모의 E2E 테스트(10회) 실행: simulation_summary.json 생성/갱신
  - 결과: Total trades: 35 (simulation_summary.json 참조)
  - 로그: logs/mock_orders.log에 모든 주문/체결 기록

주의사항 / 미완료 항목
- 실제 Kiwoom 실서버 연동(실 토큰 발급·계좌조회)은 아직 실행하지 않았음(사용자 승인 필요).
- 일부 모듈(예: 기존 동기형 kiwoom_rest_loader_mock)이 혼합되어 있어 완전한 비동기화(예: 외부 REST 호출 경로의 전부 비동기)는 추가 리팩터링 필요.
- TokenStore는 현재 파일 기반(kiwoom_token_store.json)으로 보관. 운영 전에는 키 관리 서비스로 이전 권장.

운영 가이드(간단)
- 개발 환경 활성화:
  - source .venv/bin/activate
- 모의 WS 시작(이미 실행 중일 수 있음):
  - python3 kiwoom_mock_server.py &
- market_watcher 실행(자동 플래그 생성/삭제):
  - python3 market_watcher.py &
- 스캐너(모의 E2E) 단발 실행:
  - .venv 활성화 후 python3 scanner_with_pm.py
- 가속화된 모의(여러 번) 실행:
  - .venv 활성화 후 python3 run_multiple_simulations.py
  - 결과 파일: simulation_summary.json, logs/mock_orders.log

권장 다음 단계
- (보안) TokenStore를 비밀관리(vault/keyring)로 이전
- (완성) 기존 REST 로더/클라이언트를 전부 async로 전환해 완전 비동기 파이프라인 구축
- (신뢰성) 에러·재시도·데드맨스위치 정책 보강 및 운영 모니터링/알림 추가

문의/추가 변경 원하면 알려주세요.
