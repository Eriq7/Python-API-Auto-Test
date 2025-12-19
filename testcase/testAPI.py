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

    @ddt.data(*testData)
    def test_api(self, data):
        # 1) Defensive: skip empty rows / empty ID to avoid split(None)
        case_id = data.get("ID")
        if case_id is None or (isinstance(case_id, str) and case_id.strip() == ""):
            self.skipTest("Excel row has empty ID; skipped to avoid split(None).")

        # 2) Row number: compatible with IDs like event_query_001
        #    If the ID format is wrong, fail with a clear message
        try:
            rowNum = int(str(case_id).split("_")[2])
        except Exception:
            self.fail(f"Invalid ID format: {case_id!r}. Expected like xxx_xxx_001")

        # Optional: show UseCase from Excel (helps HR/reader)
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

        try:
            print("Response JSON:", re.content.decode("utf-8"))
        except Exception:
            print("Response content (cannot decode):", re.content)

        # 6) Read expected result from Excel
        readData_code = int(data.get("status_code"))
        readData_msg = data.get("msg")

        # 7) Write back to Excel (PASS/FAIL)
        actual_status = self.result.get("status")
        actual_message = (
            self.result.get("message")
            if self.result.get("message") is not None
            else self.result.get("msg")
        )

        if readData_code == actual_status and readData_msg == actual_message:
            ok_data = "PASS"
            print(f"Test result: {case_id} ----> {ok_data}")
            WriteExcel(setting.TARGET_FILE).write_data(rowNum + 1, ok_data)
        else:
            not_data = "FAIL"
            print(f"Test result: {case_id} ----> {not_data}")
            WriteExcel(setting.TARGET_FILE).write_data(rowNum + 1, not_data)

        # 8) Assertions
        self.assertEqual(actual_status, readData_code, f"Actual status -> {actual_status}")
        self.assertEqual(actual_message, readData_msg, f"Actual message -> {actual_message}")


if __name__ == '__main__':
    unittest.main()
