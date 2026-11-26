"""월간 리포트 통합 테스트. 외부 리포트 서버 응답을 흉내 내느라 느리다."""

import time

import pytest


@pytest.mark.slow
def test_monthly_report_end_to_end(client):
    for _ in range(3):
        client.post("/orders", json={"customer": "kim", "items": [{"product_id": 1, "qty": 1}]})
    time.sleep(30)  # 리포트 서버 응답 대기 흉내
    r = client.get("/orders")
    assert len(r.json()) == 3
