import pytest
from common.auth import login_and_get_token
from common.http_client import HttpClient


@pytest.fixture(scope="session")
def token():
    """会话级 fixture，整个测试只登录一次"""
    return login_and_get_token()


@pytest.fixture(scope="session")
def client(token):
    """会话级 HTTP 客户端，自动携带 token"""
    return HttpClient(token=token)
