---
description: 기능 스펙을 받아 계획 → 승인 → 테스트 먼저 → 구현 → 검증 → 리뷰 순으로 진행한다
argument-hint: [기능 설명]
---

다음 기능을 구현하라: $ARGUMENTS

반드시 아래 순서를 지킨다.

1. 관련 코드와 `docs/domain.md`를 읽고, 바꿀 파일과 접근 방식을 담은 **변경 계획**을 먼저 제시한다.
2. 계획에 대해 사용자의 승인을 받기 전에는 파일을 수정하지 않는다.
3. 승인되면 **테스트를 먼저** 작성하고 `python dev.py test`로 실패하는 것을 확인한다.
4. 구현한다. API 계층에는 DB 코드를 두지 않는다 (team-conventions Skill 참고).
5. `python dev.py test`와 `python dev.py lint`를 모두 통과시킨다.
6. code-reviewer 서브에이전트에게 리뷰를 맡기고, 🔴·🟠 항목이 있으면 고친다.
7. 변경 파일 목록, 테스트 결과, 남은 위험을 요약해 보고한다.
