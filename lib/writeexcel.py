#!/usr/bin/env python
# _*_ coding:utf-8 _*_
__author__ = 'YinJia'

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import shutil
import configparser as cparser

from config import setting
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment

# openpyxl 3.x 不再提供 RED/GREEN/DARKYELLOW 常量，这里手动定义 ARGB 色值
# 8位 ARGB: FF 表示不透明
RED = "FFFF0000"
GREEN = "FF00FF00"
DARKYELLOW = "FFB8860B"

# --------- 读取 config.ini 配置文件 ---------------
cf = cparser.ConfigParser()
cf.read(setting.TEST_CONFIG, encoding='UTF-8')
name = cf.get("tester", "name")


class WriteExcel():
    """文件写入数据"""
    def __init__(self, fileName):
        self.filename = fileName

        # 文件不存在，则拷贝模板文件至指定报告目录下
        if not os.path.exists(self.filename):
            # 这里保持你原项目逻辑：拷贝 SOURCE_FILE 到 TARGET_FILE
            # 注意：fileName 可能就是 TARGET_FILE，也可能不是；这里不改你原来的意图
            shutil.copyfile(setting.SOURCE_FILE, setting.TARGET_FILE)

        self.wb = load_workbook(self.filename)
        self.ws = self.wb.active

    def write_data(self, row_n, value):
        """
        写入测试结果
        :param row_n: 数据所在行数
        :param value: 测试结果值（PASS/FAIL）
        :return: 无
        """
        font_GREEN = Font(name='宋体', color=GREEN, bold=True)
        font_RED = Font(name='宋体', color=RED, bold=True)
        font_YELLOW = Font(name='宋体', color=DARKYELLOW, bold=True)
        align = Alignment(horizontal='center', vertical='center')

        # 结果列 L，测试人列 M（你原逻辑）
        L_n = "L" + str(row_n)
        M_n = "M" + str(row_n)

        # 写入 PASS/FAIL 到第12列（L列）
        if value == "PASS":
            self.ws.cell(row_n, 12, value)
            self.ws[L_n].font = font_GREEN
        elif value == "FAIL":
            self.ws.cell(row_n, 12, value)
            self.ws[L_n].font = font_RED
        else:
            # 如果传入的 value 不是 PASS/FAIL，也写入但用黄字提示（不改变你的列结构）
            self.ws.cell(row_n, 12, value)
            self.ws[L_n].font = font_YELLOW

        # 写入 tester name 到第13列（M列）
        self.ws.cell(row_n, 13, name)

        # 设置对齐与样式
        self.ws[L_n].alignment = align
        self.ws[M_n].font = font_YELLOW
        self.ws[M_n].alignment = align

        self.wb.save(self.filename)
