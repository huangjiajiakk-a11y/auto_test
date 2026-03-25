import os
import yaml


def load_yaml(filename: str) -> list[dict]:
    """从 testdata 目录加载 yaml 测试数据"""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "testdata")
    filepath = os.path.join(data_dir, filename)
    with open(filepath, encoding="utf-8") as f:
        return yaml.safe_load(f)
