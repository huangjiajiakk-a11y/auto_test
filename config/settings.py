import os
import yaml


_config_cache = None


def get_config() -> dict:
    """读取 config.yaml 配置"""
    global _config_cache
    if _config_cache is None:
        config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
        with open(config_path, encoding="utf-8") as f:
            _config_cache = yaml.safe_load(f)
    return _config_cache
