#!/usr/bin/env python
# _*_ coding:utf-8 _*_
__author__ = 'Qun Li'

import os, sys, json, traceback, ast
sys.path.append(os.path.dirname(os.path.dirname(__file__)))


def _is_blank(x):
    return x is None or (isinstance(x, str) and x.strip() == "")


def safe_parse(x):
    """
    把 Excel 里读出来的值转换成 Python 对象：
    - None / "" / "   " -> None
    - dict/list/int/float/bool -> 原样返回
    - str:
        - 尝试 json.loads
        - 失败再尝试 ast.literal_eval （兼容单引号、None/True/False 这种）
        - 仍失败则原样返回字符串
    """
    if _is_blank(x):
        return None

    if isinstance(x, (dict, list, int, float, bool)):
        return x

    if isinstance(x, str):
        s = x.strip()
        if s == "":
            return None

        # 先尝试 JSON（推荐 Excel 写标准 JSON：双引号）
        try:
            return json.loads(s)
        except Exception:
            pass

        # 再尝试 Python 字面量（兼容旧 Excel：单引号、None/True/False）
        try:
            return ast.literal_eval(s)
        except Exception:
            # 实在解析不了，就返回原字符串
            return s

    return x


class SendRequests():
    """发送请求数据"""

    def sendRequests(self, s, apiData):
        try:
            method = apiData.get("method")
            url = apiData.get("url")

            par = safe_parse(apiData.get("params"))
            h = safe_parse(apiData.get("headers"))
            body_data = safe_parse(apiData.get("body"))
            req_type = apiData.get("type")

            # 兼容原项目：type=data/json/其他
            if req_type == "json":
                body = json.dumps(body_data) if body_data is not None else None
            else:
                body = body_data

            # verify=False 保持你原逻辑
            re = s.request(
                method=method,
                url=url,
                headers=h,
                params=par,
                data=body,
                verify=False
            )
            return re

        except Exception as e:
            print("SendRequests Exception:", e)
            traceback.print_exc()
            return None
