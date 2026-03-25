import pytest
from common.yaml_util import load_yaml


test_data = load_yaml("test_auth.yaml")


class TestAuth:
    """认证与用户管理接口测试 - 基于 DummyJSON API 文档"""

    @pytest.mark.parametrize(
        "case",
        test_data,
        ids=[item["case_name"] for item in test_data],
    )
    def test_auth_api(self, client, case):
        method = case["method"].lower()
        path = case["path"]

        kwargs = {}
        if case.get("params"):
            kwargs["params"] = case["params"]
        if case.get("json"):
            kwargs["json"] = case["json"]

        # 不需要 token 的接口（如登录）使用无 token 的请求
        if not case.get("need_token", True):
            from common.http_client import HttpClient
            resp = HttpClient().post(path, **kwargs) if method == "post" else HttpClient().get(path, **kwargs)
        else:
            resp = getattr(client, method)(path, **kwargs)

        print(resp.json())

        assert resp.status_code == case["expected_code"], (
            f"[{case['case_name']}] 期望 {case['expected_code']}，实际 {resp.status_code}"
        )

        # 校验返回字段
        if case.get("expected_fields"):
            body = resp.json()
            for field in case["expected_fields"]:
                assert field in body, (
                    f"[{case['case_name']}] 响应缺少字段: {field}"
                )
