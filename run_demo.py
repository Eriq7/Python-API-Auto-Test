#!/usr/bin/env python3
# _*_ coding:utf-8 _*_
__author__ = "Qun Li"

import os
import sys
import time
import unittest
import shutil
import argparse
import requests

sys.path.append(os.path.dirname(__file__))

from config import setting
from package.HTMLTestRunner import HTMLTestRunner


def add_case(test_path: str, pattern: str) -> unittest.TestSuite:
    return unittest.defaultTestLoader.discover(test_path, pattern=pattern)


def env(name: str, default: str) -> str:
    v = os.getenv(name)
    return v if v and v.strip() else default


def reset_test_data(base_url: str, reset_path: str) -> bool:
    reset_url = base_url.rstrip("/") + reset_path
    try:
        r = requests.post(reset_url, timeout=5)
        r.raise_for_status()
        print(f"[INFO] reset OK -> {reset_url}")
        return True
    except Exception as e:
        print(f"[WARN] reset failed -> {e} (url={reset_url})")
        return False


def run_case(suite: unittest.TestSuite, report_dir: str, title: str, description: str, tester: str):
    os.makedirs(report_dir, exist_ok=True)

    now = time.strftime("%Y-%m-%d_%H_%M_%S")
    report_path = os.path.join(report_dir, f"{now}_result.html")
    latest_path = os.path.join(report_dir, "latest.html")

    with open(report_path, "wb") as fp:
        runner = HTMLTestRunner(stream=fp, title=title, description=description, tester=tester)
        result = runner.run(suite)

    try:
        shutil.copyfile(report_path, latest_path)
        print(f"[INFO] latest report -> {os.path.abspath(latest_path)}")
    except Exception as e:
        print(f"[WARN] Failed to write latest.html: {e}")

    return result, report_path, latest_path


def dump_result_details(result, max_lines=80):
    # 把 errors/failures 的 traceback 打出来（否则 Jenkins 控制台只看到一堆 E）
    def _tail(tb: str) -> str:
        lines = (tb or "").splitlines()
        return "\n".join(lines[-max_lines:])

    if getattr(result, "errors", None):
        print("----- ERROR DETAILS (tail) -----")
        for test, tb in result.errors:
            try:
                tid = test.id()
            except Exception:
                tid = str(test)
            print(f"[ERROR] {tid}")
            print(_tail(tb))
            print("-" * 60)

    if getattr(result, "failures", None):
        print("----- FAILURE DETAILS (tail) -----")
        for test, tb in result.failures:
            try:
                tid = test.id()
            except Exception:
                tid = str(test)
            print(f"[FAIL] {tid}")
            print(_tail(tb))
            print("-" * 60)


def parse_args():
    p = argparse.ArgumentParser(description="DemoAPI test runner (CI-friendly)")
    p.add_argument("--test-path", default=getattr(setting, "TEST_CASE", "testcase"))
    p.add_argument("--pattern", default="*API.py")
    p.add_argument("--report-dir", default=env("REPORT_DIR", getattr(setting, "TEST_REPORT", "report")))
    p.add_argument("--title", default="E-commerce API Automation Test Report")
    p.add_argument("--description", default="Python Requests + Unittest + DDT + Excel (Data-Driven)")
    p.add_argument("--tester", default="Qun Li")
    return p.parse_args()


def main() -> int:
    base_url = env("BASE_URL", "http://127.0.0.1:8000")
    reset_path = env("RESET_PATH", "/api/test/reset")

    print(f"BASE_URL={base_url}")
    print(f"RESET_PATH={reset_path}")

    args = parse_args()

    # reset 放最前面（CI 下需要保证可重复跑）
    reset_test_data(base_url, reset_path)

    try:
        suite = add_case(args.test_path, args.pattern)
    except Exception as e:
        print(f"[ERROR] Failed to discover tests: {e}")
        return 2

    try:
        result, report_path, latest_path = run_case(
            suite, args.report_dir, args.title, args.description, args.tester
        )
    except Exception as e:
        print(f"[ERROR] Failed to run tests / generate report: {e}")
        return 2

    failures = len(getattr(result, "failures", []))
    errors = len(getattr(result, "errors", []))
    tests_run = getattr(result, "testsRun", 0)

    print("----- SUMMARY -----")
    print(f"TESTS_RUN={tests_run}")
    print(f"FAILURES={failures}")
    print(f"ERRORS={errors}")
    print(f"REPORT_PATH={os.path.abspath(report_path)}")
    print(f"LATEST_REPORT_PATH={os.path.abspath(latest_path)}")

    # ✅ 关键：把异常细节打印到 Jenkins console
    dump_result_details(result)

    ok = (failures == 0 and errors == 0)
    print(f"RESULT={'SUCCESS' if ok else 'FAILED'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
