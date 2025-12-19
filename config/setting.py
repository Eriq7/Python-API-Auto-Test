#!/usr/bin/env python
# _*_ coding:utf-8 _*_
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(BASE_DIR)

# Config file (public repo safe)
# - Prefer local config.ini (ignored by git)
# - Fallback to config.ini.example (committed to repo)
TEST_CONFIG = os.path.join(BASE_DIR, "database", "config.ini")
TEST_CONFIG_EXAMPLE = os.path.join(BASE_DIR, "database", "config.ini.example")
if not os.path.exists(TEST_CONFIG) and os.path.exists(TEST_CONFIG_EXAMPLE):
    TEST_CONFIG = TEST_CONFIG_EXAMPLE

# Test case template file
SOURCE_FILE = os.path.join(BASE_DIR, "database", "DemoAPITestCase.xlsx")

# Excel test case result file (generated locally)
TARGET_FILE = os.path.join(BASE_DIR, "report", "excelReport", "DemoAPITestCase.xlsx")

# Test report output dir (generated locally)
TEST_REPORT = os.path.join(BASE_DIR, "report")

# Test case scripts dir
TEST_CASE = os.path.join(BASE_DIR, "testcase")
