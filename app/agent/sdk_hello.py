"""Lab 5 · Hello Agent — 하네스를 '코드로' 내장한 최소 고객지원 에이전트 (Claude Agent SDK).

저장소 하네스(CLAUDE.md·settings·Hooks)가 Claude Code를 감쌌다면,
여기서는 같은 요소를 앱 안에 직접 구현한다.

  TOOLS        get_order(조회) / cancel_order(변경) — 위험도별로 도구를 분리
  PERMISSIONS  allowed_tools에는 조회만. 변경 도구는 can_use_tool 콜백에서 사람 승인
  LIMITS       max_turns, max_budget_usd 로 폭주·비용 제한
  CONTEXT      system_prompt 로 역할 경계

실행:  pip install claude-agent-sdk   (ANTHROPIC_API_KEY 필요)
       python dev.py seed
       python -m app.agent.sdk_hello "주문 A-0003 상태 알려줘"
       python -m app.agent.sdk_hello "A-0003 주문 취소해줘"
※ SDK API는 버전에 따라 바뀝니다. claude-agent-sdk 0.2.x 기준으로 작성했습니다.
"""

import asyncio
import json
import sys

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    PermissionResultAllow,
    PermissionResultDeny,
    ResultMessage,
    TextBlock,
    create_sdk_mcp_server,
    tool,
)

from app.db import init_db
from app.services import order_service


def _text(obj) -> dict:
    return {"content": [{"type": "text", "text": json.dumps(obj, ensure_ascii=False)}]}


def _error(msg: str) -> dict:
    return {"content": [{"type": "text", "text": msg}], "is_error": True}


@tool(
    "get_order",
    "주문 번호로 주문 상태·금액·품목을 조회한다. 고객이 주문에 대해 물으면 먼저 이 도구로 확인하라.",
    {"order_no": str},
)
async def get_order(args):
    order_no = args["order_no"].strip().upper()
    order = order_service.get_order(order_no)
    if order is None:
        return _error(f"주문 {order_no}이 없다. 주문 번호 형식은 A-0000 이다. 고객에게 번호를 다시 확인하라.")
    order.pop("id", None)  # 내부 id는 노출하지 않는다 (CLAUDE.md 규칙과 동일)
    return _text(order)


@tool(
    "cancel_order",
    "주문을 취소한다(되돌릴 수 없음). PAID 상태만 가능. 고객이 명시적으로 취소를 요청했을 때만 사용하라.",
    {"order_no": str},
)
async def cancel_order(args):
    try:
        return _text(order_service.cancel_order(args["order_no"]))
    except order_service.OrderNotFound:
        return _error("없는 주문이다. get_order로 번호를 먼저 확인하라.")
    except order_service.InvalidTransition as e:
        return _error(f"현재 상태 {e}에서는 취소할 수 없다(PAID만 가능). 고객에게 사유를 설명하라.")


async def ask_human(tool_name: str, tool_input: dict, _context):
    """allowed_tools에 없는 도구가 호출되면 여기로 온다 → 사람 승인 장치."""
    if tool_name == "mcp__shop__cancel_order":
        answer = input(f"\n[승인 필요] 주문 {tool_input.get('order_no')} 취소를 허용할까요? (y/N) ")
        if answer.strip().lower() == "y":
            return PermissionResultAllow()
        return PermissionResultDeny(message="담당자가 취소를 승인하지 않았다. 상담원 연결을 안내하라.")
    return PermissionResultDeny(message=f"{tool_name}은 이 앱에서 허용되지 않는 도구다.")


shop = create_sdk_mcp_server(name="shop", version="1.0.0", tools=[get_order, cancel_order])

options = ClaudeAgentOptions(
    system_prompt=(
        "너는 온라인 쇼핑몰 고객지원 에이전트다. 주문 정보는 반드시 도구로 확인하고 추측하지 마라. "
        "금액은 원 단위로 천 단위 콤마를 넣어 안내하라. 환불·보상 약속은 하지 마라."
    ),
    mcp_servers={"shop": shop},
    tools=[],  # Claude Code 내장 도구(Bash·Edit 등)는 이 앱에 필요 없다
    allowed_tools=["mcp__shop__get_order"],  # 조회만 자동 허용, cancel_order는 ask_human을 거친다
    can_use_tool=ask_human,
    setting_sources=[],  # 저장소의 .claude 설정을 섞지 않는다: 앱 하네스는 이 코드가 전부
    max_turns=8,
    max_budget_usd=0.20,
)


async def main(prompt: str) -> None:
    init_db()
    async with ClaudeSDKClient(options=options) as client:
        await client.query(prompt)
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(block.text)
            elif isinstance(msg, ResultMessage):
                print(f"\n— 턴 {msg.num_turns}, 비용 ${msg.total_cost_usd or 0:.4f}")


if __name__ == "__main__":
    asyncio.run(main(" ".join(sys.argv[1:]) or "주문 A-0003은 어디쯤인가요?"))
