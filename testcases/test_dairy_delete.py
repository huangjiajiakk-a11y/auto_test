import pytest
import pymysql
from common.yaml_util import load_yaml
from common.http_client import HttpClient
from config.settings import get_config


test_data = load_yaml("test_dairy_delete.yaml")


class TestDairyDelete:
    """删除日记接口测试 - POST /api/dairy/delete"""

    def test_delete_dairy_success(self, client):
        """删除日记成功 - 先发布一条日记，再删除"""
        # 1. 发布日记，获取 diaryNum
        publish_resp = client.post("/api/dairy/publish", json={
            "content": "这是一条待删除的测试日记",
            "type": "IMAGE_TEXT",
        })
        assert publish_resp.status_code == 200, (
            f"前置发布日记失败: {publish_resp.text}"
        )
        diary_num = publish_resp.json()["data"]["diaryNum"]
        print(f"发布日记成功, diaryNum={diary_num}")

        # 2. 删除日记
        delete_resp = client.post("/api/dairy/delete", params={"diaryNum": diary_num})
        resp_body = delete_resp.json()
        print(resp_body)

        assert delete_resp.status_code == 200, (
            f"删除日记失败: 期望 200，实际 {delete_resp.status_code}"
        )

        # 3. 数据库断言：status 应为 0（软删除）
        cfg = get_config()["mysql"]
        conn = pymysql.connect(
            host=cfg["host"], port=cfg["port"], user=cfg["user"],
            password=cfg["password"], database=cfg["database"],
            charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor,
        )
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT `status` FROM `l_dairy` WHERE `diary_num` = %s",
                    (diary_num,),
                )
                row = cur.fetchone()
        finally:
            conn.close()

        assert row is not None, f"数据库未找到 diary_num={diary_num} 的记录"
        assert row["status"] == 0, (
            f"期望 status=0（已删除），实际 status={row['status']}"
        )

    @pytest.mark.parametrize(
        "case",
        test_data,
        ids=[item["case_name"] for item in test_data],
    )
    def test_delete_dairy_api(self, client, case):
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

        try:
            resp_body = resp.json()
            print(resp_body)
        except Exception:
            resp_body = None
            print(f"status={resp.status_code}, body={resp.text}")

        assert resp.status_code == case["expected_code"], (
            f"[{case['case_name']}] 期望 {case['expected_code']}，实际 {resp.status_code}"
        )

        if case.get("expected_fields"):
            assert resp_body is not None, (
                f"[{case['case_name']}] 响应不是 JSON 格式，无法校验字段"
            )
            for field in case["expected_fields"]:
                assert field in resp_body, (
                    f"[{case['case_name']}] 响应缺少字段: {field}"
                )
