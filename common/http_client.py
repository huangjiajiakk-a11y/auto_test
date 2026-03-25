import requests
from config.settings import get_config


class HttpClient:
    """统一的 HTTP 请求封装，自动拼接 base_url 和注入 token"""

    def __init__(self, token: str = ""):
        self.base_url = get_config()["base_url"]
        self.session = requests.Session()
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})

    def _url(self, path: str) -> str:
        return self.base_url + path

    def get(self, path: str, params: dict = None, **kwargs) -> requests.Response:
        return self.session.get(self._url(path), params=params, timeout=10, **kwargs)

    def post(self, path: str, json: dict = None, **kwargs) -> requests.Response:
        return self.session.post(self._url(path), json=json, timeout=10, **kwargs)

    def put(self, path: str, json: dict = None, **kwargs) -> requests.Response:
        return self.session.put(self._url(path), json=json, timeout=10, **kwargs)

    def delete(self, path: str, **kwargs) -> requests.Response:
        return self.session.delete(self._url(path), timeout=10, **kwargs)
