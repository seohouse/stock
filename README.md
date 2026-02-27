# Kiwoom Trading Workspace

간단 사용법(빠른 시작):

1) 클론 및 가상환경
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -U pip

2) 개발용 설치(편집 가능 모드)
   pip install -e .

3) 실행
   - 기존(레거시) 호출: `./scanner_core_ws.py` 등 (루트에 shim이 있음)
   - 모듈로 직접 실행: `python -m <module>` (예: `python -m scanner_core_ws`)

구조:
- src/ : 실제 파이썬 소스 파일들(.py)
- 루트: 각 스크립트 이름으로 shim(실행 스크립트)이 존재하여 기존 호출을 유지합니다
- memory/, logs/, .env 등 민감파일은 .gitignore에 포함되어 있습니다

주의:
- .env 및 토큰 스토어 파일은 절대 커밋하지 마세요.
- 실 API 호출 전 포털(키/화이트리스트) 확인 필수.


## 변경: 로컬 mock WS 서버 제거
- 일시:  (UTC)
- 작업: 로컬 mock WebSocket 서버(mock_ws_server.py)를 저장소 및 워크스페이스에서 완전히 제거했습니다.
- 이유: 실제 운영/테스트는 실서버 또는 별도 테스트 환경으로 이전했습니다.

복구 방법:
- 복구가 필요하면 요청 주세요. 백업에서 복원하거나 제가 새 mock을 생성해 드립니다.
