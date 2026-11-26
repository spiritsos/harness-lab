# Order Service

FastAPI + SQLite 주문 관리 API. 도메인 규칙(주문 상태·금액·주문번호)은 @docs/domain.md

## 명령 (이 명령만 쓴다)
- 테스트: `python dev.py test` — 반드시 통과한 뒤에 "완료"라고 말한다
- 린트: `python dev.py lint` / 포맷: `python dev.py fmt`
- `pytest`를 직접 실행하지 않는다. slow 테스트(30초+)까지 돌아간다. 전체 테스트는 `python dev.py test-all`(CI용)
- 로컬 실행: `python dev.py run`, 샘플 데이터: `python dev.py seed`

## 구조
- `app/api/` 라우터: 요청 검증과 HTTP 응답 변환만
- `app/services/` 비즈니스 로직과 DB 접근
- `app/models.py` Pydantic 스키마 / `app/db.py` 연결·마이그레이션
- `tests/` pytest. API 테스트는 `client` fixture 사용 (임시 DB)

## 규칙
- API 계층(`app/api/`)에서 `get_conn()`·SQL 직접 호출 금지 → `app/services/`에 함수를 만든다
- 금액은 원 단위 `int`. `float` 금지. 할인은 정수 연산 후 내림 (`total * 90 // 100`)
- `migrations/`의 기존 파일은 수정 금지. 스키마 변경은 새 번호 파일(`003_...sql`)로
- 새 엔드포인트에는 테스트 필수 (성공 1개 + 실패 1개 이상)
- 외부에는 `order_no`(A-0000)만 노출. 내부 `id`를 경로·응답에 쓰지 않는다

## 금지
- `scripts/reset_db.py` 실행 금지 (DB 전체 삭제). 필요하면 사람에게 요청
- `.env` 읽기·출력 금지

## 도구
- 데이터 확인은 추측하지 말고 MCP `shopdb`(읽기 전용)로 조회한다
- app/ 코드를 바꾸면 team-conventions Skill로 검사, 구현이 끝나면 code-reviewer에게 리뷰를 맡긴다

## 작업 방식
- 엔드포인트 추가처럼 2개 이상 파일을 바꾸는 작업은 Plan 모드로 계획부터 제시
- 끝나면 바꾼 파일 목록과 `python dev.py test` 결과를 보고한다
