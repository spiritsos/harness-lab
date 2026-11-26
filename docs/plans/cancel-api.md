# 계획: 주문 취소 API (Plan 모드 결과를 저장한 예)

## 요구사항
- `POST /orders/{order_no}/cancel`
- docs/domain.md: 취소는 PAID 상태에서만 허용, `cancelled_at` 기록

## 변경 파일
1. `app/services/order_service.py` — `cancel_order(order_no)` 추가
   - 없는 주문 → `OrderNotFound`
   - PAID가 아니면 → `InvalidTransition(현재 상태)`
   - 성공 시 status=CANCELLED, cancelled_at=now
2. `app/api/orders.py` — 라우터 추가. 예외를 404 / 409로 변환 (DB 직접 호출 없음)
3. `tests/test_cancel.py` — PAID 취소 성공, PENDING·SHIPPED 취소 409, 없는 주문 404

## 사람 검토 포인트
- 409 응답 메시지에 현재 상태와 허용 상태를 함께 넣는다 (에이전트·사용자 모두 이해 가능하게)
- 환불 처리는 범위 밖 (별도 작업)
