import copy
import jsonpath_ng.ext as jsonpath_ext


def resolve_value(value, context):
    """解析期望值：如果是 jsonpath 表达式（以 $ 开头）则从 context 中提取，否则原样返回"""
    if isinstance(value, str) and value.startswith("$"):
        matches = jsonpath_ext.parse(value).find(context)
        return matches[0].value if matches else None
    return value


def resolve_deep(obj, context):
    """递归遍历 dict/list，对所有 $ 开头的字符串调用 resolve_value"""
    if isinstance(obj, dict):
        return {k: resolve_deep(v, context) for k, v in obj.items()}
    if isinstance(obj, list):
        return [resolve_deep(item, context) for item in obj]
    if isinstance(obj, str) and obj.startswith("$"):
        return resolve_value(obj, context)
    return obj


def _fill_actual(expected, actual):
    """递归处理 expected 中的动态值：jsonpath 表达式从 actual 中提取对应值"""
    if isinstance(expected, dict):
        result = {}
        for k, v in expected.items():
            result[k] = _fill_actual(v, actual)
        return result
    if isinstance(expected, list):
        return [_fill_actual(e, actual) for e in expected]
    if isinstance(expected, str) and expected.startswith("$"):
        matches = jsonpath_ext.parse(expected).find(actual)
        return matches[0].value if matches else None
    return expected


def assert_json(expected, actual, case_name=""):
    """整体 JSON 比对，只比较 expected 中声明的字段，actual 中多余的字段自动忽略"""
    filled = _fill_actual(copy.deepcopy(expected), actual)
    actual_subset = _extract_subset(filled, actual)
    assert filled == actual_subset, (
        f"[{case_name}] JSON 不一致\n期望: {filled}\n实际: {actual_subset}"
    )


def _extract_subset(expected, actual):
    """从 actual 中只提取 expected 中存在的字段，用于忽略多余字段"""
    if isinstance(expected, dict) and isinstance(actual, dict):
        return {k: _extract_subset(v, actual.get(k)) for k, v in expected.items()}
    if isinstance(expected, list) and isinstance(actual, list):
        return [_extract_subset(e, a) for e, a in zip(expected, actual)]
    return actual
