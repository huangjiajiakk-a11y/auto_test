import pymysql
from config.settings import get_config
from common.jsonpath_util import resolve_value


def query_db(sql, args=None):
    """执行查询SQL，返回单条记录"""
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
            cur.execute(sql, args)
            return cur.fetchone()
    finally:
        conn.close()


def execute_db(sql, args=None):
    """执行 INSERT/UPDATE/DELETE 语句，返回影响行数"""
    cfg = get_config()["mysql"]
    conn = pymysql.connect(
        host=cfg["host"],
        port=cfg["port"],
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        charset="utf8mb4",
    )
    try:
        with conn.cursor() as cur:
            affected = cur.execute(sql, args)
            conn.commit()
            return affected
    finally:
        conn.close()


def assert_db_check(case):
    """根据 case 中的 db_check 配置执行数据库字段校验"""
    db = case["db_check"]
    if "match_value_from" in db:
        match_value = resolve_value(db["match_value_from"], case)
    else:
        match_value = case["json"][db["match_by"]]
    checks = db.get("checks", [{"field": db.get("field"), "value": db.get("value")}])
    fields = ", ".join(f"`{c['field']}`" for c in checks)
    sql = f"SELECT {fields} FROM `{db['table']}` WHERE `{db['match_by']}` = %s ORDER BY id DESC LIMIT 1"

    row = query_db(sql, (match_value,))

    assert row is not None, (
        f"[{case['case_name']}] 数据库未找到 {db['match_by']}={match_value} 的记录"
    )
    for check in checks:
        expected = resolve_value(check.get("value"), case)
        assert row[check["field"]] == expected, (
            f"[{case['case_name']}] 期望 {check['field']}={expected}，实际 {row[check['field']]}"
        )
