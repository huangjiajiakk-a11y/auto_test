from typing import Any
from mcp.server.fastmcp import FastMCP
import requests
import pymysql
import os
import yaml

# Initialize FastMCP server
mcp = FastMCP("auto_test_tools", log_level="ERROR")


# ---------- 读取配置 ----------
def _get_mysql_config() -> dict:
    config_path = os.path.join(os.path.dirname(__file__), "config", "config.yaml")
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)["mysql"]


def _get_connection():
    cfg = _get_mysql_config()
    return pymysql.connect(
        host=cfg["host"],
        port=cfg["port"],
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


# ---------- Swagger 工具 ----------
@mcp.tool()
def fetch_swagger_schema(swagger_address: str) -> dict:
    """
    从 GitHub 拉取 Swagger/OpenAPI 接口文档,解析所有接口参数
    """
    resp = requests.get(swagger_address, timeout=10)
    resp.raise_for_status()
    return resp.json()


# ---------- MySQL 工具 ----------
@mcp.tool()
def mysql_query(sql: str) -> list[dict]:
    """
    执行 SELECT 查询,返回结果列表
    """
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()
    finally:
        conn.close()


@mcp.tool()
def mysql_execute(sql: str) -> str:
    """
    执行 INSERT/UPDATE/DELETE 语句,返回影响行数
    """
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            affected = cur.execute(sql)
            conn.commit()
            return f"affected_rows: {affected}"
    finally:
        conn.close()


@mcp.tool()
def mysql_list_tables() -> list[str]:
    """
    列出当前数据库的所有表名
    """
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SHOW TABLES")
            return [list(row.values())[0] for row in cur.fetchall()]
    finally:
        conn.close()


@mcp.tool()
def mysql_describe_table(table_name: str) -> list[dict]:
    """
    查看指定表的结构(字段名、类型、是否可空、键、默认值等)
    """
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(f"DESCRIBE `{table_name}`")
            return cur.fetchall()
    finally:
        conn.close()


if __name__ == "__main__":
    # 启动服务，claude Code 自动识别
    mcp.run(transport='stdio')
