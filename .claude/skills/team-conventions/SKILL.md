---
name: team-conventions
description: 이 저장소(app/)의 API 엔드포인트·서비스·모델 코드를 새로 작성하거나 수정하거나 리뷰할 때 사용한다. 계층 위반(API에서 DB 직접 호출), float 금액, 기존 마이그레이션 수정 같은 팀 컨벤션 위반을 스크립트로 검사하고 수정안을 제시한다.
---

# 팀 컨벤션 검사

## 절차
1. 검사 스크립트를 실행한다. 바꾼 파일만 검사하려면 경로를 인자로 준다.
   ```bash
   python .claude/skills/team-conventions/scripts/check_layers.py            # app/ 전체
   python .claude/skills/team-conventions/scripts/check_layers.py app/api/orders.py
   ```
2. 출력된 위반을 규칙별로 묶어 정리한다: `[LAYER]` `[MONEY]` `[MIGRATION]`
3. 각 위반에 대해 아래 "수정 패턴"에 맞는 수정안을 제시한다. 사용자가 수정을 요청한 경우에만 고친다.
4. 고쳤다면 스크립트를 다시 실행해 "컨벤션 위반 없음"을 확인하고, `python dev.py test`를 통과시킨다.

## 수정 패턴

**[LAYER] API에서 DB 직접 호출**
```python
# app/services/order_service.py
def list_orders():
    conn = get_conn()
    ...


# app/api/orders.py  → get_conn import 제거, 서비스 호출만
return order_service.list_orders()
```

**[MONEY] float 금액 / 할인율**
```python
COUPONS = {"WELCOME10": 10}  # 퍼센트 정수
total = total * (100 - pct) // 100  # 정수 연산 + 내림
price: int  # 스키마도 int
```

**[MIGRATION] 기존 파일 수정**
`git checkout -- migrations/<파일>`로 되돌리고 `migrations/003_<설명>.sql`을 새로 만든다.

## 참고
- 규칙의 근거: `docs/domain.md`, 루트 `CLAUDE.md`
- 스크립트가 잡지 못하는 위반(예: 내부 id 노출)은 직접 읽어서 판단한다
