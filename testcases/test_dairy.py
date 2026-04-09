import pytest
from common.yaml_util import load_yaml
from common.http_client import HttpClient


test_data = load_yaml("test_dairy.yaml")


class TestDairy:
    """日记发布接口测试 - POST /api/dairy/publish"""

    @pytest.mark.parametrize(
        "case",
        test_data,
        ids=[item["case_name"] for item in test_data],
    )
    def test_dairy_api(self, client, case):
        method = case["method"].lower()
        path = case["path"]

        kwargs = {}
        if case.get("params"):
            kwargs["params"] = case["params"]
        if case.get("json"):
            kwargs["json"] = case["json"]

        if not case.get("need_token", True):
            resp = getattr(HttpClient(), method)(path, **kwargs)
        else:
            resp = getattr(client, method)(path, **kwargs)

        print(resp.json())

        assert resp.status_code == case["expected_code"], (
            f"[{case['case_name']}] 期望 {case['expected_code']}，实际 {resp.status_code}"
        )

        if case.get("expected_fields"):
            body = resp.json()
            for field in case["expected_fields"]:
                assert field in body, (
                    f"[{case['case_name']}] 响应缺少字段: {field}"
                )
