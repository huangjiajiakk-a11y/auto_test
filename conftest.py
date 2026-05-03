import json
import types
import pytest
from pytest_metadata.plugin import metadata_key
from common.auth import login_and_get_token
from common.http_client import HttpClient
from common.yaml_util import load_yaml
from common.base_test import BaseTestCase


@pytest.fixture(scope="session")
def token():
    """会话级 fixture，整个测试只登录一次"""
    return login_and_get_token()


@pytest.fixture(scope="session")
def client(token):
    """会话级 HTTP 客户端，自动携带 token"""
    return HttpClient(token=token)


def pytest_html_results_table_header(cells):
    """在报告表头添加 '请求信息' 和 '响应信息' 列"""
    cells.insert(2, '<th class="sortable" data-column-type="requestInfo">请求信息</th>')
    cells.insert(3, '<th class="sortable" data-column-type="responseInfo">响应信息</th>')


def pytest_html_results_table_row(report, cells):
    """在报告每行填充请求和响应数据"""
    req = getattr(report, "request_info", "")
    resp = getattr(report, "response_info", "")
    cells.insert(2, f"<td>{req}</td>")
    cells.insert(3, f"<td>{resp}</td>")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        client = item.funcargs.get("client")
        if client and hasattr(client, "last_request_info") and client.last_request_info:
            info = client.last_request_info
            # 构建请求信息
            req_parts = [
                f"<b>{info['method']}</b> {info['url']}",
            ]
            if info.get("request_params"):
                req_parts.append(
                    f"Params: <pre>{json.dumps(info['request_params'], ensure_ascii=False, indent=2)}</pre>")
            if info.get("request_body"):
                req_parts.append(f"Body: <pre>{json.dumps(info['request_body'], ensure_ascii=False, indent=2)}</pre>")

            report.request_info = "<br>".join(req_parts)

            # 构建响应信息
            try:
                resp_body = json.dumps(json.loads(info["response_body"]), ensure_ascii=False, indent=2)
            except (json.JSONDecodeError, TypeError):
                resp_body = info.get("response_body", "")

            report.response_info = (
                f"Status: <b>{info['status_code']}</b><br>"
                f"<pre>{resp_body}</pre>"
            )
        else:
            report.request_info = ""
            report.response_info = ""


# ── YAML 自动发现 ──────────────────────────────────────────────

def pytest_collect_file(parent, file_path):
    """1、优先扫描pytest.ini文件中的testpaths
    2、收集 testdata/ 下的 test_*.yaml 文件
    3、每读到一个文件，自动调用pytest_collect_fire函数"""
    if file_path.suffix in (".yaml", ".yml") and file_path.name.startswith("test_"):
        return YamlModule.from_parent(parent, path=file_path) # parent为当前文件的父节点，file_path则为扫描到的yaml文件



class YamlModule(pytest.Module):
    """将一个 YAML 测试数据文件转换为 pytest 可收集的模块"""

    def _getobj(self):
        """合成一个包含参数化测试类的模块对象"""
        test_data = load_yaml(self.path.name)

        # 动态创建测试类
        class AutoTest(BaseTestCase):
            pass

        # 参数化装饰
        def test_api(self, client, case):
            self.run_case(client, case)

        test_api = pytest.mark.parametrize(
            "case",
            test_data,
            ids=[item["case_name"] for item in test_data],
        )(test_api)

        AutoTest.test_api = test_api

        # 用 YAML 文件名（去掉 .yaml）作为类名
        class_name = self.path.stem.replace("test_", "Test_").title().replace("_", "")
        AutoTest.__name__ = class_name
        AutoTest.__qualname__ = class_name

        # 合成模块
        mod = types.ModuleType(self.path.stem)
        mod.__file__ = str(self.path)
        mod.__loader__ = None
        mod.__test__ = True
        setattr(mod, class_name, AutoTest)
        return mod
