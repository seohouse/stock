---
name: changwon-gaemi
description: "Real-time momentum trading skill implementing the '창원개미' strategy: target-universe filtering, 100-point realtime scoring, buy/sell/stop rules and configurable parameters. Trigger when user asks to register or run an automated momentum/short-horizon trading strategy for Korean equities."
---

# 창원개미 — Quick reference

This skill encodes the user's realtime trading rules ("창원개미") and provides a runnable script and reference for how to evaluate scores and execute orders.

When to use
- Use this skill when you need to: implement, simulate, or run the "창원개미" real-time trading strategy against a live or mock market feed.
- This skill is triggered by requests like: "Register the 창원개미 strategy", "Run 창원개미 on live feed", "Simulate 창원개미 for symbol 005930".

What the skill provides
- A compact SKILL.md with the rules and parameter descriptions (this file).
- scripts/run_changwon_gaemi.py — a runnable reference implementation that:
  - Filters the target universe by price and volume ratio
  - Computes the 100-point realtime score from the specified sub-scores
  - Emits buy signals when score >= buy_threshold and executes market orders (stubbed)
  - Handles stop-loss, profit-taking, and emergency halt on market-wide adverse conditions

Configuration (defaults)
- PRICE_MIN = 800
- PRICE_MAX = 150000
- VOLUME_RATIO_MIN = 5.0  # 500% as ratio
- SCORE_THRESHOLD_BUY = 80
- REG_RETRY_MAX = 3
- REG_RETRY_DELAY = 1.0
- STOP_LOSS_MIN = -0.015
- STOP_LOSS_MAX = -0.03
- TAKE_PROFIT_MIN = 0.015
- TAKE_PROFIT_MAX = 0.03

Realtime scoring components (weights)
- Order of precedence and weights (sum 100):
  - Supply/Demand Momentum (수급 동력): 35 pts
  - Price Trend (가격 추세): 30 pts
  - Orderbook Structure (호가창 구조): 20 pts
  - Execution Strength (체결 강도): 15 pts

Safety & hard stops (Priority: Highest)
- The skill implements absolute, agent-level trading halts based on market index behavior and institutional flow. If any stop condition triggers the system sets global_trading_lock = true and halts all new entries immediately.

Stop conditions (OR - any one triggers halt):
1) Index price action
  - Index intra-day drop: KOSPI or KOSDAQ falls >= 1.0% vs open.
  - Flash crash: Index falls >= 0.5% within 3 minutes.
2) Institutional flow
  - Pre-10:30 session large sell: foreigner net-sell < -1000억 AND institution net-sell < -500억.
  - Recent 10-min surge in net-sell: combined foreign+institution net-sell increases by >= 300억 in past 10 minutes.
3) Technical trend
  - Golden-line breach: index 1-min or 3-min candle breaks below 20-period MA and fails to recover.

Agent Actions when halt triggers
- Set global_trading_lock = true and stop all scoring and new entry evaluations.
- Protect held positions:
  - If index <= -1.5% vs open: tighten trailing stops to just above average entry price.
  - If index <= -2.0% vs open: sell all positions immediately and shutdown system.
- Immediately send alert via configured channels (Telegram/Discord): "지수 급락 및 양매도 발생으로 인한 매매 중단"

References
- Data sources required for these checks: ka20003 (index), realtime index websocket, ka10131 (institutional/foreigner flow) or equivalent intraday investor flow endpoints.
- See scripts/ for enforcement logic and a simulation mode.

---
# Failure-based ledger synchronization (추가 규칙)

이 섹션은 네 요청에 따라 "금액 관련 주문 실패 발생 시 API 호출을 통해 로컬 원장(local_ledger.json)을 동기화"하는 동작을 명세한다.

동작 요약
- 실패 카운터: 금액 관련 주문 실패(예: 매수증거금 부족, 매도가능수량 부족 등)를 감지하면 실패 카운터를 1 증가시킨다.
- 동기화 트리거: 실패 카운터가 SYNC_ON_FAIL_THRESHOLD(기본 5)에 도달하면 즉시 계좌조회 API를 호출해서 로컬 원장을 실제 계좌 상태로 동기화한다(로컬 원장 덮어쓰기 또는 보정).
- 반복 동작: 동기화 후 실패 카운터는 리셋되며, 이후 또 SYNC_ON_FAIL_THRESHOLD만큼 실패가 발생하면 동일한 동기화를 반복한다(즉 매 N회 실패마다 동기화).
- 로깅/알림: 각 동기화 시도와 결과(성공/실패, 불일치 요약)는 로그에 기록하고 Telegram/설정된 채널로 요약 알림을 보낸다.

구성 가능한 파라미터
- SYNC_ON_FAIL_THRESHOLD = 5  # N회 실패마다 동기화 트리거
- FAIL_COUNTER_RESET_AFTER_SYNC = true  # 동기화 성공 시 실패 카운터 리셋 여부
- ENABLE_GLOBAL_LOCK_IF_MISMATCH = true  # 동기화 후 원장과 실제 계좌 간 큰 불일치 발견 시 global_trading_lock 설정 여부
- MISMATCH_PCT_THRESHOLD = 0.05  # 현금(또는 총자산) 불일치 비율 임계값(예: 0.05 == 5%)
- SYNC_BACKOFF_SECONDS = 30  # 동기화 실패 시 재시도 간격

예상 플로우 (간단히)
1) 주문 실행 중 금액 관련 실패 감지 → fail_count += 1
2) if fail_count >= SYNC_ON_FAIL_THRESHOLD:
   - 호출: 계좌조회 API (REST) → 계좌 현금/보유수량 정보 수신
   - 업데이트: local_ledger.json을 API값으로 보정(혹은 덮어쓰기)
   - 로그/알림 전송
   - fail_count = 0 (또는 설정에 따라 유지)
3) 이후 추가 실패가 발생하면 동일 루프 반복

안전 조치
- 동기화 결과와 로컬 원장 간 차이가 MISMATCH_PCT_THRESHOLD 이상이면(예: 현금 차이 > 5%) 자동으로 global_trading_lock=true를 설정하여 신규 진입을 중단할 수 있다(ENABLE_GLOBAL_LOCK_IF_MISMATCH 설정에 따름). 이 동작은 알림과 함께 저장된다.
- 동기화 API 호출은 rate-limit을 주의하여 구현(백오프/재시도 로직 포함).
- mock 모드에서도 동일 로직을 수행하되, mock API 응답을 사용함.

개발/배치 노트
- 스크립트(예: execute_recommendations.py)와 데몬(changwon_selector.py 등)에 fail_count 추적과 sync_on_fail 로직을 추가해야 함. Token 캐시와 동기화 간의 경합을 피하려면 sync 작업은 토큰 캐시 획득/사용 로직과 동일한 잠금/시계열을 사용.
- 동기화 중 원장 덮어쓰기 전에는 백업(local_ledger.json.bak.TIMESTAMP)을 반드시 생성.

원하면 내가 코드 패치(실제 스크립트에 fail counter + sync 호출 추가)를 만들어서 적용하고 mock 시뮬레이션으로 테스트해줄게.