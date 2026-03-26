import json as json_lib
import requests
from config.settings import get_config


class HttpClient:
    """统一的 HTTP 请求封装，自动拼接 base_url 和注入 token"""

    def __init__(self, token: str = ""):
        self.base_url = get_config()["base_url"]
        self.session = requests.Session()
        self.last_request_info = {}
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})

    def _url(self, path: str) -> str:
        return self.base_url + path

    def _record_request(self, method, url, resp, **kwargs):
        """记录请求和响应信息，供报告使用"""
        self.last_request_info = {
            "method": method.upper(),
            "url": url,
            "request_headers": dict(resp.request.headers),
            "request_params": kwargs.get("params"),
            "request_body": kwargs.get("json"),
            "status_code": resp.status_code,
            "response_body": resp.text,
        }

    def get(self, path: str, params: dict = None, **kwargs) -> requests.Response:
        url = self._url(path)
        resp = self.session.get(url, params=params, timeout=10, **kwargs)
        self._record_request("GET", url, resp, params=params, **kwargs)
        return resp

    def post(self, path: str, json: dict = None, **kwargs) -> requests.Response:
        url = self._url(path)
        resp = self.session.post(url, json=json, timeout=10, **kwargs)
        self._record_request("POST", url, resp, json=json, **kwargs)
        return resp

    def put(self, path: str, json: dict = None, **kwargs) -> requests.Response:
        url = self._url(path)
        resp = self.session.put(url, json=json, timeout=10, **kwargs)
        self._record_request("PUT", url, resp, json=json, **kwargs)
        return resp

    def delete(self, path: str, **kwargs) -> requests.Response:
        url = self._url(path)
        resp = self.session.delete(url, timeout=10, **kwargs)
        self._record_request("DELETE", url, resp, **kwargs)
        return resp
