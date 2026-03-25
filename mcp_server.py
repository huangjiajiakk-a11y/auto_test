from typing import Any
from mcp.server.fastmcp import FastMCP
import requests

# Initialize FastMCP server
mcp = FastMCP("get_swagger", log_level="ERROR")


# Constants
# swagger_address = "https://raw.githubusercontent.com/huangjiajiakk-a11y/h_auto_test/refs/heads/main/api.json"


@mcp.tool()
def fetch_swagger_schema(swagger_address: str) -> dict:
    """
    从 GitHub 拉取 Swagger/OpenAPI 接口文档，解析所有接口参数
    """
    resp = requests.get(swagger_address, timeout=10)
    resp.raise_for_status()
    return resp.json()


if __name__ == "__main__":
    # 启动服务，claude Code 自动识别
    mcp.run(transport='stdio')
