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
    if _is_blank(x):
        return None

    if isinstance(x, (dict, list, int, float, bool)):
        return x

    if isinstance(x, str):
        s = x.strip()
        if s == "":
            return None

        # 1) JSON
        try:
            return json.loads(s)
        except Exception:
            pass

        # 2) Python literal
        try:
            return ast.literal_eval(s)
        except Exception:
            pass

        # 3) querystring -> dict
        try:
            if "=" in s:
                kv_pairs = parse_qsl(s, keep_blank_values=True)
                if kv_pairs:
                    return dict(kv_pairs)
        except Exception:
            pass

        return s

    return x


def _running_in_docker() -> bool:
    return os.path.exists("/.dockerenv")


def _rewrite_url_for_docker(url: str) -> str:
    """
    在 CI / docker compose 场景：
      容器里访问 target-api 应该用 service name：target-api
    允许通过环境变量 DOCKER_URL_HOST 覆盖（默认 target-api）
    """
    if not url or not _running_in_docker():
        return url

    docker_host = os.getenv("DOCKER_URL_HOST", "target-api")

    try:
        p = urlparse(url)
        if p.hostname in ("127.0.0.1", "localhost"):
            new_netloc = p.netloc.replace(p.hostname, docker_host)
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

            # ✅ Docker 下自动改写 localhost/127.0.0.1 -> target-api
            url = _rewrite_url_for_docker(url)

            params = safe_parse(apiData.get("params"))
            headers = safe_parse(apiData.get("headers"))
            body_data = safe_parse(apiData.get("body"))
            req_type = (apiData.get("type") or "").strip().lower()

            if params is not None and not isinstance(params, dict):
                print(f"[WARN] params is not dict after parse: {params!r}. Forcing to None.")
                params = None
            if headers is not None and not isinstance(headers, dict):
                print(f"[WARN] headers is not dict after parse: {headers!r}. Forcing to None.")
                headers = None

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
