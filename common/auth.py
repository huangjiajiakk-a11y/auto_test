from __future__ import annotations

import requests
from config.settings import get_config


_token_cache: str | None = None


def login_and_get_token() -> str:
    """登录并获取 token，结果会缓存，整个测试会话只登录一次"""
    global _token_cache
    if _token_cache is not None:
        return _token_cache

    cfg = get_config()
    url = cfg["base_url"] + cfg["login"]["url"]
    payload = {
        "username": cfg["login"]["username"],
        "password": cfg["login"]["password"],
    }
    resp = requests.post(url, json=payload, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    _token_cache = data.get("accessToken", "")
    return _token_cache
