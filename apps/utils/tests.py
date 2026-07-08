#!/usr/bin/env python
# coding: utf-8

import datetime
import os
import socket
import time
import unittest
from collections import namedtuple

import qrcode
from apps.utils.api.tests import APITestCase
from apps.utils.json.json2csv import Json2csv
from apps.utils.json.json2input import Json2Input
from apps.utils.shortcuts import (build_query_string, check_is_id,
                                  datetime2str, humansize, img2base64,
                                  md5_for_file, natural_sort_key, rand_str,
                                  send_email, timestamp2utcstr)
from apps.utils.xss_filter import XSSHtml
from django.conf import settings
from rest_framework import status


class TestXSSHtml(unittest.TestCase):
    """测试对富文本进行 XSS 过滤"""

    def test_xsshtml(self):
        self.XSS_DATA = """<p><img src=1 onerror=alert(/xss/)></p><div class="left">
            <a href='javascript:prompt(1)'><br />hehe</a></div>
            <p id="test" onmouseover="alert(1)">&gt;M<svg>
            <a href="https://www.baidu.com" target="self">MM</a></p>
            <embed src='javascript:alert(/hehe/)' allowscriptaccess=always />
            <img onerror=alert(1) src=#>"""

        self.DATA = """<p><img src="1" /></p><div class="left">
            <a href="http://javascript:prompt(1)" target="_blank"><br />hehe</a></div>
            <p>&gt;M
            <a href="https://www.baidu.com">MM</a></p>
            <embed src="http://javascript:alert(/hehe/)" allowscriptaccess="never" allownetworking="none" />
            <img src="#" />"""

        with XSSHtml() as parser:
            return_data = parser.clean(self.XSS_DATA)
            self.assertEqual(return_data, self.DATA)


class Testshortcuts(unittest.TestCase):
    def test_rand_str(self):
        rand_str(type="str")
        rand_str(type="lower_str")
        rand_str(type="lower_hex")
        rand_str(type="abc")


class TestBuild_query(unittest.TestCase):
    def test_build_query(self):
        ret = build_query_string({"a": 1, "b": "test"})
        self.assertEqual(ret, "?a=1&b=test")
        build_query_string({})


class Testimg2base64(unittest.TestCase):
    def test_img2base64(self):
        image = qrcode.make("abcdef")
        img2base64(image)


class TestDatetime(unittest.TestCase):
    def test_timestamp2utcstr(self):
        datetime2str(datetime.time(hour=12, minute=34, second=56, microsecond=0))
        datetime2str(datetime.time(hour=12, minute=34, second=56, microsecond=0), "%Z")

    def test_datetime2str(self):
        timestamp2utcstr(time.time())


class Testidsort(unittest.TestCase):
    def test_natural_sort_key(self):
        natural_sort_key("skd1dk3dkj4")

    def test_check_is_id(self):
        check_is_id(500)
        check_is_id("weiwe")


class TestFileSizeMd5(unittest.TestCase):
    def test_humansize(self):
        humansize(os.path.getsize(os.path.abspath(__file__)))

    def test_md5(self):
        md5_for_file(os.path.abspath(__file__), block_size=256 * 128, hr=False)
        md5_for_file(os.path.abspath(__file__), block_size=256 * 128, hr=True)


class SimditorUploadTest(APITestCase):
    """对 Simditor 上传文件、图像进行测试"""

    def setUp(self):
        self.image_url = self.reverse("upload_image")
        self.file_url = self.reverse("upload_file")
        self.user = self.create_admin()

    def test_upload_image(self):
        with open(os.path.join(settings.BASE_DIR, "TEST/test/hue.png"), "rb") as f:
            resp = self.client.post(
                self.image_url, data={"image": f}, format="multipart"
            )
            self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # 测试错误的图片格式
        with open(os.path.join(settings.BASE_DIR, "TEST/test/restore.json"), "rb") as f:
            resp = self.client.post(
                self.image_url, data={"image": f}, format="multipart"
            )
            self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # 测试错误的关键字
        with open(os.path.join(settings.BASE_DIR, "TEST/test/restore.json"), "rb") as f:
            resp = self.client.post(
                self.image_url, data={"fjwel": f}, format="multipart"
            )
            self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_upload_file(self):
        with open(os.path.join(settings.BASE_DIR, "TEST/test/restore.json"), "rb") as f:
            resp = self.client.post(self.file_url, data={"file": f}, format="multipart")
            self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # 测试错误的参数
        with open(os.path.join(settings.BASE_DIR, "TEST/test/restore.json"), "rb") as f:
            resp = self.client.post(
                self.file_url, data={"dfjkwe": f}, format="multipart"
            )
            self.assertEqual(resp.status_code, status.HTTP_200_OK)


class JsonTest(unittest.TestCase):
    """
    对 json 转换代码做测试，分别测试从 json 到 csv 和 json 到 input 文件
    """

    def test_json2input(self):
        jsonFileName = os.path.join(settings.BASE_DIR, "TEST/test/restore.json")
        options = namedtuple("OPTION", "InputFileName JsonFileName")
        option = options(InputFileName="run.input", JsonFileName=jsonFileName)
        json2input = Json2Input(option)
        json2input.write()
        os.remove("run.input")

    def test_json2csv(self):
        jsonFileName = os.path.join(settings.BASE_DIR, "TEST/test/restore.json")
        options = namedtuple("OPTION", "JsonFileName CSVFileName inputID skipNull")
        option = options(
            JsonFileName=jsonFileName, CSVFileName="run.csv", inputID=3, skipNull=True
        )
        json2csv = Json2csv(option)
        json2csv.write()
        os.remove("run.csv")
