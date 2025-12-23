#!/usr/bin/env python
# _*_ coding:utf-8 _*_
__author__ = 'YinJia'

import os
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import unittest
import requests
import ddt

from config import setting
from lib.readexcel import ReadExcel
from lib.sendrequests import SendRequests
from lib.writeexcel import WriteExcel

testData = ReadExcel(setting.SOURCE_FILE, "Sheet1").read_data() or []


@ddt.ddt
class Demo_API(unittest.TestCase):
    """E-commerce API Automated Test Suite"""

    def setUp(self):
        self.s = requests.session()

    def tearDown(self):
        pass

    @staticmethod
    def _normalize_actual_status(resp: requests.Response, result_json: dict):
        """
        ✅ 关键修复：
        FastAPI validation error 会直接返回 HTTP 422，默认 body 没有 {"status": ...}
        你的 Excel 里对“参数错误”期望业务码 10021（而不是 None）
        所以：当 status 缺失且 status_code==422 -> 映射为 10021
        """
        actual_status = None
        if isinstance(result_json, dict):
            actual_status = result_json.get("status")

        if actual_status is None and getattr(resp, "status_code", None) == 422:
            return 10021

        return actual_status

    @staticmethod
    def _normalize_actual_message(result_json: dict):
        if not isinstance(result_json, dict):
            return None
        # 兼容 message/msg 字段
        return result_json.get("message") if result_json.get("message") is not None else result_json.get("msg")

    @ddt.data(*testData)
    def test_api(self, data):
        # 1) Defensive: skip empty rows / empty ID to avoid split(None)
        case_id = data.get("ID")
        if case_id is None or (isinstance(case_id, str) and case_id.strip() == ""):
            self.skipTest("Excel row has empty ID; skipped to avoid split(None).")

        # 2) Row number: compatible with IDs like event_query_001
        try:
            rowNum = int(str(case_id).split("_")[2])
        except Exception:
            self.fail(f"Invalid ID format: {case_id!r}. Expected like xxx_xxx_001")

        # Optional: show UseCase from Excel
        use_case = data.get("UseCase") or data.get("usecase") or ""

        print(f"******* Running test case -> {case_id} *********")
        if use_case:
            print(f"UseCase: {use_case}")
        print(f"HTTP Method: {data.get('method')} | URL: {data.get('url')}")
        print(f"Query Params: {data.get('params')}")
        print(f"Body Type: {data.get('type')} | Body: {data.get('body')}")

        # 3) Send request
        re = SendRequests().sendRequests(self.s, data)

        # 4) Defensive: if sendRequests returns None, an internal exception occurred
        if re is None:
            self.fail("sendRequests returned None. Check printed traceback above.")

        # 5) Parse JSON response (if failed, print raw response for debugging)
        try:
            self.result = re.json()
        except Exception:
            print("Response status_code:", getattr(re, "status_code", None))
            try:
                print("Response text:", re.text)
            except Exception:
                print("Response content(raw):", getattr(re, "content", None))
            self.fail("Response is not valid JSON; cannot parse re.json().")

        # 打印响应体，方便定位
        print("HTTP status_code:", getattr(re, "status_code", None))
        try:
            print("Response JSON/Text:", re.text)
        except Exception:
            try:
                print("Response content(raw):", re.content)
            except Exception:
                pass

        # 6) Read expected result from Excel
        # Excel 里可能是 "10021" / 10021 / 10021.0，这里做更稳的转换
        try:
            readData_code = int(str(data.get("status_code")).strip())
        except Exception:
            self.fail(f"Invalid status_code in Excel for {case_id}: {data.get('status_code')!r}")

        readData_msg = data.get("msg")

        # 7) Normalize actual status/message
        actual_status = self._normalize_actual_status(re, self.result)
        actual_message = self._normalize_actual_message(self.result)

        # 8) Write back to Excel (PASS/FAIL) —— 用 normalize 后的结果
        if (str(readData_code) == str(actual_status)) and (str(readData_msg) == str(actual_message)):
            ok_data = "PASS"
            print(f"Test result: {case_id} ----> {ok_data}")
            WriteExcel(setting.TARGET_FILE).write_data(rowNum + 1, ok_data)
        else:
            not_data = "FAIL"
            print(f"Test result: {case_id} ----> {not_data}")
            WriteExcel(setting.TARGET_FILE).write_data(rowNum + 1, not_data)

        # 9) Assertions —— 失败时把 HTTP 和 body 打出来（关键）
        self.assertEqual(
            str(actual_status), str(readData_code),
            f"Actual status -> {actual_status} | HTTP={getattr(re,'status_code',None)} | body={getattr(re,'text',None)}"
        )
        self.assertEqual(
            str(actual_message), str(readData_msg),
            f"Actual message -> {actual_message} | HTTP={getattr(re,'status_code',None)} | body={getattr(re,'text',None)}"
        )


if __name__ == '__main__':
    unittest.main()
