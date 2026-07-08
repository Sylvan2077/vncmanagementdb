#!/usr/bin/env python
# coding: utf-8

from apps.account.models import AdminType, CasePermission, User, UserProfile
from django.test.testcases import TestCase
from django.urls import reverse
from rest_framework.test import APIClient


class APITestCase(TestCase):
    client_class = APIClient

    def create_user(
        self,
        username,
        password,
        admin_type=AdminType.REGULAR_USER,
        login=True,
        case_permission=CasePermission.NONE,
    ):
        user = User.objects.create(
            username=username, admin_type=admin_type, case_permission=case_permission
        )
        user.set_password(password)
        UserProfile.objects.create(user=user)
        user.save()
        if login:
            self.client.login(username=username, password=password)
        return user

    def create_admin(self, username="admin", password="admin", login=True):
        return self.create_user(
            username=username,
            password=password,
            admin_type=AdminType.ADMIN,
            case_permission=CasePermission.OWN,
            login=login,
        )

    def create_super_admin(self, username="root", password="root", login=True):
        return self.create_user(
            username=username,
            password=password,
            admin_type=AdminType.SUPER_ADMIN,
            case_permission=CasePermission.ALL,
            login=login,
        )
    # 调用django的reverse函数，根据url_name获取url，从而不经过浏览器向后端发送请求
    def reverse(self, url_name, *args, **kwargs):
        return reverse(url_name, *args, **kwargs)

    def assertSuccess(self, response):
        if not response.data["error"] is None:
            raise AssertionError(
                "response with errors, response: " + str(response.data)
            )

    def assertFailed(self, response, msg=None):
        self.assertTrue(response.data["error"] is not None)
        if msg:
            self.assertEqual(response.data["data"], msg)
