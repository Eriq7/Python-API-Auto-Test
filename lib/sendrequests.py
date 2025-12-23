#!/usr/bin/env python
# _*_ coding:utf-8 _*_
__author__ = 'Qun Li'

import os
import sys
import json
import traceback
import ast
from urllib.parse import urlparse, urlunparse, parse_qsl

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
        - 失败再尝试 ast.literal_eval（兼容单引号、None/True/False）
        - 仍失败则尝试解析 querystring: "a=1&b=2" / "eid=1" / "phone="
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

        # 1) JSON（推荐 Excel 写标准 JSON：双引号）
        try:
            return json.loads(s)
        except Exception:
            pass

        # 2) Python 字面量（兼容旧 Excel：单引号、None/True/False）
        try:
            return ast.literal_eval(s)
        except Exception:
            pass

        # 3) ✅ querystring（关键修复点）
        # 支持：
        #   "eid=1"
        #   "name=红米"
        #   "eid=1&name=红米"
        #   "eid=1&phone="  (空值也保留)
        try:
            if "=" in s:
                kv_pairs = parse_qsl(s, keep_blank_values=True)
                if kv_pairs:
                    return dict(kv_pairs)
        except Exception:
            pass

        # 4) 实在解析不了就返回原字符串
        return s

    return x


def _running_in_docker() -> bool:
    # 常见容器标志：/.dockerenv 存在
    return os.path.exists("/.dockerenv")


def _rewrite_url_for_docker(url: str) -> str:
    """
    规则（确定版）：
    - 本机跑：Excel 继续用 127.0.0.1（不改）
    - 只有“测试框架跑在 Docker 容器里”时，才把 127.0.0.1/localhost 重写成 host.docker.internal
      （容器里访问宿主机 target API）
    """
    if not url or not _running_in_docker():
        return url

    try:
        p = urlparse(url)
        if p.hostname in ("127.0.0.1", "localhost"):
            new_netloc = p.netloc.replace(p.hostname, "host.docker.internal")
            return urlunparse((p.scheme, new_netloc, p.path, p.params, p.query, p.fragment))
    except Exception:
        pass

    return url


class SendRequests:
    """发送请求数据"""

    def sendRequests(self, s, apiData):
        try:
            method = (apiData.get("method") or "").strip()
            url = (apiData.get("url") or "").strip()

            if not method or not url:
                raise ValueError(f"Excel row missing method/url: method={method!r}, url={url!r}")

            # ✅ Docker 下自动改写，不要求你改 Excel
            url = _rewrite_url_for_docker(url)

            params = safe_parse(apiData.get("params"))
            headers = safe_parse(apiData.get("headers"))
            body_data = safe_parse(apiData.get("body"))
            req_type = (apiData.get("type") or "").strip().lower()

            # 防御：params/headers 若解析成了非 dict（比如奇怪字符串），避免 requests 处理异常
            if params is not None and not isinstance(params, dict):
                print(f"[WARN] params is not dict after parse: {params!r}. Forcing to None.")
                params = None
            if headers is not None and not isinstance(headers, dict):
                print(f"[WARN] headers is not dict after parse: {headers!r}. Forcing to None.")
                headers = None

            # 保持原项目语义：type=json 就发 JSON；否则走 data（表单/普通）
            if req_type == "json":
                resp = s.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=body_data,
                    verify=False,
                )
            else:
                resp = s.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    data=body_data,
                    verify=False,
                )

            return resp

        except Exception as e:
            print("SendRequests Exception:", e)
            traceback.print_exc()
            return None
