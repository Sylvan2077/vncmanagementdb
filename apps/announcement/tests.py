#!/usr/bin/env python
# coding: utf-8

import copy

from apps.announcement.models import Announcement
from apps.utils.api.tests import APITestCase


class AnnouncementAdminTest(APITestCase):
    """测试在后台对公告做各类操作"""

    def setUp(self):
        # 基本设定
        self.user = self.create_super_admin()
        self.url = self.reverse("announcement_admin_api")
        self.CommonData = {"title": "test", "content": "test", "visible": True}
        resp = self.client.post(self.url, data=self.CommonData)
        self.announcement = Announcement.objects.get(id=resp.data["data"]["id"])
        self.assertEqual(
            self.announcement.__str__(),
            "Announcement[ title: {title} ]".format(title=self.announcement.title),
        )

    def test_announcement_list(self):
        # 测试获取公告列表
        response = self.client.get(self.url)
        self.assertSuccess(response)
        # 测试获取单个公告
        # 正常获取
        resp = self.client.get(self.url, data={"id": self.announcement.id})
        self.assertSuccess(resp)
        # 错误获取
        resp = self.client.get(self.url, data={"id": 100})
        self.assertFailed(resp)
        # 筛选 visible
        resp = self.client.get(self.url, data={"visible": "true"})
        self.assertSuccess(resp)

    def test_create_announcement(self):
        # 测试创建公告
        NewData = copy.deepcopy(self.CommonData)
        NewData["title"] = "a test"
        NewData["content"] = "another test"
        NewData["visible"] = False
        resp = self.client.post(self.url, data=NewData)
        self.assertSuccess(resp)

        resp_data = resp.data["data"]
        self.assertEqual(resp_data["title"], NewData["title"])
        self.assertEqual(resp_data["content"], NewData["content"])
        self.assertEqual(resp_data["visible"], NewData["visible"])

    def test_edit_announcement(self):
        # 测试全局更新公告
        data = {
            "id": self.announcement.id,
            "title": "ahaha",
            "content": "test content",
            "visible": False,
        }
        resp = self.client.put(self.url, data=data)
        self.assertSuccess(resp)

        resp_data = resp.data["data"]
        self.assertEqual(resp_data["title"], data["title"])
        self.assertEqual(resp_data["content"], data["content"])
        self.assertEqual(resp_data["visible"], data["visible"])

        # put 失败的情形，没有找到 id
        WrongDatabase = copy.deepcopy(data)
        WrongDatabase["id"] = 100
        resp = self.client.put(self.url, data=WrongDatabase)
        self.assertFailed(resp)

    def test_patch_announcement(self):
        # 测试局部更新公告
        data = {"id": self.announcement.id, "title": "bjbjb", "visible": False}
        resp = self.client.patch(self.url, data=data)
        self.assertSuccess(resp)

        resp_data = resp.data["data"]
        self.assertEqual(resp_data["title"], data["title"])
        self.assertEqual(resp_data["visible"], data["visible"])

        # patch 失败的情况
        # put 失败的情形，没有找到 id
        WrongDatabase = copy.deepcopy(data)
        WrongDatabase["id"] = 100
        resp = self.client.patch(self.url, data=WrongDatabase)
        self.assertFailed(resp)

    def test_delete_announcement(self):
        # 测试删除公告
        id = self.announcement.id
        resp = self.client.delete(self.url + "?id=" + str(id))
        self.assertSuccess(resp)
        self.assertFalse(Announcement.objects.filter(id=id).exists())


class AnnouncementAPITest(APITestCase):
    """测试前台获取公告信息"""

    def setUp(self):
        self.user = self.create_super_admin()
        Announcement.objects.create(
            title="title", content="content", visible=True, submitter=self.user
        )
        self.url = self.reverse("announcement_api")

    def test_get_announcement_list(self):
        # 获取公告列表
        resp = self.client.get(self.url)
        self.assertSuccess(resp)
