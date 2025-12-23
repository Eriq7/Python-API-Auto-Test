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

        try:
            return json.loads(s)
        except Exception:
            pass

        try:
            return ast.literal_eval(s)
        except Exception:
            pass

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


def _get_base_url_env() -> str | None:
    """
    Scheme A control:
      export BASE_URL=http://target-api:8000
    """
    v = os.getenv("BASE_URL", "").strip()
    if not v:
        return None
    return v.rstrip("/")


def _rewrite_url_for_env_or_docker(url: str) -> str:
    """
    Priority:
    1) If BASE_URL is set, overwrite scheme+netloc using BASE_URL, keep path+query+fragment.
    2) Else if running in docker and host is localhost/127.0.0.1 -> rewrite to target-api
    3) Else return unchanged
    """
    if not url:
        return url

    try:
        p = urlparse(url)

        base = _get_base_url_env()
        if base:
            b = urlparse(base)
            # keep original path/query/fragment, replace scheme+netloc
            return urlunparse((b.scheme or p.scheme, b.netloc, p.path, p.params, p.query, p.fragment))

        if _running_in_docker() and p.hostname in ("127.0.0.1", "localhost"):
            new_netloc = p.netloc.replace(p.hostname, "target-api")
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

            # ✅ Scheme A: env override OR docker rewrite to target-api
            url = _rewrite_url_for_env_or_docker(url)

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
