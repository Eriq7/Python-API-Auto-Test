#!/usr/bin/env python
# _*_ coding:utf-8 _*_
__author__ = 'Qun Li'

import os
import sys
import time
import unittest
import shutil
import webbrowser

import requests  # ✅ NEW: for reset endpoint

sys.path.append(os.path.dirname(__file__))

from config import setting
from package.HTMLTestRunner import HTMLTestRunner
from lib.sendmail import send_mail
from lib.newReport import new_report
from db_fixture import test_data


def add_case(test_path=setting.TEST_CASE):
    """Load all test cases"""
    discover = unittest.defaultTestLoader.discover(test_path, pattern='*API.py')
    return discover


def reset_test_data():
    """
    ✅ Best practice for stable, repeatable runs (no data pollution):
    Try to reset data via API endpoint before running tests.

    This avoids relying on local MySQL (which may not exist on demo machines).
    If reset endpoint is not available, we DO NOT crash the run.
    """
    reset_url = "http://127.0.0.1:8000/api/test/reset"
    headers = {"X-TEST-KEY": "local-dev-only"}  # you can change/remove if your backend doesn't check it

    try:
        resp = requests.post(reset_url, headers=headers, timeout=3)
        resp.raise_for_status()
        print(f"[INFO] Test data reset via API OK -> {reset_url}")
        return True
    except Exception as e:
        print(f"[WARN] Test data reset via API skipped/failed: {e}")
        print("[WARN] Continuing without reset. Create-type cases may become non-idempotent.")
        return False


def run_case(all_case, result_path=setting.TEST_REPORT):
    """Run all test cases"""

    # ✅ NEW: reset test data via API (recommended)
    reset_test_data()

    # (Optional) Old DB reset approach (requires local MySQL). Keep it off for demos.
    # test_data.init_data()

    now = time.strftime("%Y-%m-%d %H_%M_%S")
    filename = os.path.join(result_path, f"{now}result.html")

    # 1) Generate timestamped report
    with open(filename, "wb") as fp:
        runner = HTMLTestRunner(
            stream=fp,
            title='E-commerce API Automation Test Report',
            description='Macbook Air M3 | Python Requests + Unittest + DDT + Excel (Data-Driven)',
            tester='Qun Li'
        )
        runner.run(all_case)

    # 2) Generate fixed entry: report/latest.html
    latest_html = os.path.join(result_path, "latest.html")
    shutil.copyfile(filename, latest_html)
    print(f"[INFO] latest report -> {latest_html}")

    # 3) Auto-open latest.html (for demo)
    webbrowser.open(f"file://{os.path.abspath(latest_html)}")

    # 4) Keep your original logic: find latest report + send email
    report = new_report(setting.TEST_REPORT)
    send_mail(report)


if __name__ == "__main__":
    cases = add_case()
    run_case(cases)
