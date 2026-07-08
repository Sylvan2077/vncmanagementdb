#!/usr/bin/env python
# coding: utf-8

import json
from unittest import mock

from apps.conf.options import SysOptions
from apps.utils.api.tests import APITestCase


class WebsiteConfigAPITest(APITestCase):
    """对网站的配置做测试"""

    def test_create_website_config(self):
        self.create_super_admin()
        url = self.reverse("website_config_api")
        data = {
            "website_name": "test name",
            "website_name_shortcut": "test vvcasedb",
            "website_footer": "<a>test test</a>",
        }
        resp = self.client.post(url, data=data)
        self.assertSuccess(resp)

    def test_edit_website_config(self):
        self.create_super_admin()
        url = self.reverse("website_config_api")
        data = {
            "website_name": "test name",
            "website_name_shortcut": "test oj",
            "website_footer": "<img onerror=alert(1) src=#>",
        }
        resp = self.client.post(url, data=data)
        self.assertSuccess(resp)

    def test_get_website_config(self):
        # 不需要登录
        url = self.reverse("website_info_api")
        resp = self.client.get(url)
        self.assertSuccess(resp)


class DashboardInfoAPITest(APITestCase):
    """对面板信息做测试"""

    def setUp(self):
        self.url = self.reverse("dashboard_info_api")
        self.create_admin()

    def test_get_info(self):
        resp = self.client.get(self.url)
        self.assertSuccess(resp)
        self.assertEqual(resp.data["data"]["user_count"], 1)

