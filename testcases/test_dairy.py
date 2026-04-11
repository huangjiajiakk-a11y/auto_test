import pytest
import pymysql
from common.yaml_util import load_yaml
from common.http_client import HttpClient
from config.settings import get_config


test_data = load_yaml("test_dairy.yaml")


def _query_db(sql):
    cfg = get_config()["mysql"]
    conn = pymysql.connect(
        host=cfg["host"],
        port=cfg["port"],
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchone()
    finally:
        conn.close()


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

        # 数据库断言
        if case.get("db_check"):
            db = case["db_check"]
            match_value = case["json"][db["match_by"]]
            sql = f"SELECT `{db['field']}` FROM `{db['table']}` WHERE `{db['match_by']}` = %s ORDER BY id DESC LIMIT 1"
            # pymysql 的 %s 占位需要通过 execute 传参，这里直接拼安全值
            cfg = get_config()["mysql"]
            conn = pymysql.connect(
                host=cfg["host"], port=cfg["port"], user=cfg["user"],
                password=cfg["password"], database=cfg["database"],
                charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor,
            )
            try:
                with conn.cursor() as cur:
                    cur.execute(sql, (match_value,))
                    row = cur.fetchone()
            finally:
                conn.close()

            assert row is not None, (
                f"[{case['case_name']}] 数据库未找到 {db['match_by']}={match_value} 的记录"
            )
            assert row[db["field"]] == db["value"], (
                f"[{case['case_name']}] 期望 {db['field']}={db['value']}，实际 {row[db['field']]}"
            )
