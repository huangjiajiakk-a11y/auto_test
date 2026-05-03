from common.http_client import HttpClient
from common.db_util import assert_db_check, execute_db
from common.jsonpath_util import resolve_value, resolve_deep, assert_json


class BaseTestCase:
    """接口测试基类，封装通用的请求发送、响应校验、数据库断言逻辑"""

    def run_case(self, client, case):
        case.setdefault("extracted", {})
        try:
            for step in case["steps"]:
                self._run_step(client, case, step)
        finally:
            cleanup = case.get("cleanup")
            if cleanup:
                args = [resolve_value(a, case) for a in cleanup.get("args", [])]
                execute_db(cleanup["sql"], args or None)
                print(f"[{case['case_name']}] 数据清理完成")

    @staticmethod
    def _run_step(client, case, step):
        """执行单步请求：发送请求、提取变量、断言"""
        method = step["method"].lower()
        kwargs = {}
        if step.get("params"):
            kwargs["params"] = resolve_deep(step["params"], case)
        if step.get("json"):
            kwargs["json"] = resolve_deep(step["json"], case)

        if not step.get("need_token", True):
            resp = getattr(HttpClient(), method)(step["path"], **kwargs)
        else:
            resp = getattr(client, method)(step["path"], **kwargs)

        # 解析响应
        try:
            resp_body = resp.json()
            print(resp_body)
        except Exception:
            resp_body = None
            print(f"status={resp.status_code}, body={resp.text}")

        # 状态码断言
        name = step.get("name", case["case_name"])
        assert resp.status_code == step["expected_code"], (
            f"[{name}] 期望 {step['expected_code']}，实际 {resp.status_code}"
        )

        # 提取变量
        if resp_body:
            for key, expr in step.get("extract", {}).items():
                case["extracted"][key] = resolve_value(expr, resp_body)

        # JSON 整体比对
        if step.get("expected_json"):
            assert resp_body is not None, f"[{name}] 响应不是 JSON 格式，无法校验"
            assert_json(step["expected_json"], resp_body, name)

        # 字段存在性校验
        if step.get("expected_fields"):
            assert resp_body is not None, f"[{name}] 响应不是 JSON 格式，无法校验字段"
            for field in step["expected_fields"]:
                assert field in resp_body, f"[{name}] 响应缺少字段: {field}"

        # 数据库断言
        if step.get("db_check"):
            case["json"] = step.get("json", {})
            case["params"] = step.get("params", {})
            case["db_check"] = step["db_check"]
            assert_db_check(case)
