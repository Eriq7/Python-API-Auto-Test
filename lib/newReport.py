#!/usr/bin/env python
# _*_ coding:utf-8 _*_
__author__ = 'YinJia'

import os

def new_report(testreport):
    lists = os.listdir(testreport)
    lists.sort(key=lambda fn: os.path.getmtime(os.path.join(testreport, fn)))
    file_new = os.path.join(testreport, lists[-1])
    return file_new
