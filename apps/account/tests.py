#!/usr/bin/env python
# coding: utf-8

import os
import time
from copy import deepcopy
from datetime import timedelta
from unittest import mock

from apps.account.models import AdminType, CasePermission, User
from apps.conf.options import SysOptions
from apps.utils.api.tests import APIClient, APITestCase
from apps.utils.shortcuts import rand_str
from django.conf import settings
from django.contrib import auth
from django.utils.timezone import now
from otpauth import OtpAuth
from rest_framework import status


class PermissionDecoratorTest(APITestCase):
    """权限装饰器的测试"""

    def setUp(self):
        self.regular_user = User.objects.create(username="regular_user")
        self.admin = User.objects.create(username="admin")
        self.super_admin = User.objects.create(username="super_admin")
        self.request = mock.MagicMock()
        self.request.user.is_authenticated = mock.MagicMock()

    def test_login_required(self):
        self.request.user.is_authenticated.return_value = False

    def test_admin_required(self):
        pass

    def test_super_admin_required(self):
        pass


class CaptchaAPITest(APITestCase):
    """测试获取验证码"""

    def setUp(self):
        self.user = self.create_super_admin()
        self.url = self.reverse("show_captcha")

    def get_captcha(self):
        # 直接访问获取
        resp = self.client.get(self.url)
        self.assertSuccess(resp)


class DuplicateUserCheckAPITest(APITestCase):
    """检测用户相关信息是否重复"""

    def setUp(self):
        user = self.create_user("test", "test123", login=False)
        user.email = "test@test.com"
        user.save()
        self.url = self.reverse("check_username_or_email")

    def test_duplicate_username(self):
        # 测试用户名重复的情况
        # 首先先创建一个用户
        resp = self.client.post(self.url, data={"username": "test"})
        data = resp.data["data"]
        self.assertEqual(data["username"], True)
        # 再次创建一个用户名一样的用户
        resp = self.client.post(self.url, data={"username": "Test"})
        self.assertEqual(resp.data["data"]["username"], False)

    def test_ok_username(self):
        # 测试用户名正常的情况
        resp = self.client.post(self.url, data={"username": "test1"})
        data = resp.data["data"]
        self.assertFalse(data["username"])

        # 测试 logout
        self.logout_url = self.reverse("user_logout_api")
        resp = self.client.get(self.logout_url)
        self.assertSuccess(resp)

    def test_duplicate_email(self):
        # 测试邮箱重复的情况
        resp = self.client.post(self.url, data={"email": "test@test.com"})
        self.assertEqual(resp.data["data"]["email"], True)
        resp = self.client.post(self.url, data={"email": "Test@Test.com"})
        self.assertFalse(resp.data["data"]["email"])

    def test_ok_email(self):
        # 测试邮件正常的情况
        resp = self.client.post(self.url, data={"email": "aa@test.com"})
        self.assertFalse(resp.data["data"]["email"])


class UserLoginAPITest(APITestCase):
    """用户登录测试"""

    def setUp(self):
        self.username = self.password = "test"
        self.user = self.create_user(
            username=self.username, password=self.password, login=False
        )
        self.login_url = self.reverse("user_login_api")

    def test_login_with_correct_info(self):
        # 测试正确登录的情况
        response = self.client.post(
            self.login_url, data={"username": self.username, "password": self.password}
        )
        self.assertDictEqual(response.data, {"error": None, "data": "Succeeded"})

        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

    def test_login_with_correct_info_upper_username(self):
        # 测试用户名大写的情况
        resp = self.client.post(
            self.login_url,
            data={"username": self.username.upper(), "password": self.password},
        )
        self.assertDictEqual(resp.data, {"error": None, "data": "Succeeded"})
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

    def test_login_with_wrong_info(self):
        # 测试用户信息错误的情况
        response = self.client.post(
            self.login_url,
            data={"username": self.username, "password": "invalid_password"},
        )
        self.assertDictEqual(
            response.data, {"error": "error", "data": "Invalid username or password"}
        )

        user = auth.get_user(self.client)
        self.assertFalse(user.is_authenticated)

    def test_user_disabled(self):
        # 测试 当用户被禁用的情况
        self.user.is_disabled = True
        self.user.save()
        resp = self.client.post(
            self.login_url, data={"username": self.username, "password": self.password}
        )
        self.assertDictEqual(
            resp.data, {"error": "error", "data": "Your account has been disabled"}
        )


class CaptchaTest(APITestCase):
    def _set_captcha(self, session):
        captcha = rand_str(4)
        session["_django_captcha_key"] = captcha
        session["_django_captcha_expires_time"] = int(time.time()) + 30
        session.save()
        return captcha


class UserRegisterAPITest(CaptchaTest):
    """测试用户注册相关功能"""

    def setUp(self):
        self.client = APIClient()
        self.register_url = self.reverse("user_register_api")
        self.captcha = rand_str(4)

        self.data = {
            "username": "test_user",
            "password": "testuserpassword",
            "real_name": "real_name",
            "email": "test@abc.com",
            "captcha": self._set_captcha(self.client.session),
        }

    def test_invalid_captcha(self):
        # 测试验证码错误的情况
        self.data["captcha"] = "****"
        response = self.client.post(self.register_url, data=self.data)
        self.assertDictEqual(
            response.data, {"error": "error", "data": "Invalid captcha"}
        )

        self.data.pop("captcha")
        response = self.client.post(self.register_url, data=self.data)
        self.assertTrue(response.data["error"] is not None)

    def test_register_with_correct_info(self):
        # 测试正常注册的情况
        response = self.client.post(self.register_url, data=self.data)
        self.assertDictEqual(response.data, {"error": None, "data": "Succeeded"})

    def test_username_already_exists(self):
        # 测试用户名存在的情况
        self.test_register_with_correct_info()

        self.data["captcha"] = self._set_captcha(self.client.session)
        self.data["email"] = "test1@abc.com"
        response = self.client.post(self.register_url, data=self.data)
        self.assertDictEqual(
            response.data, {"error": "error", "data": "Username already exists"}
        )

    def test_email_already_exists(self):
        # 测试邮箱存在的情况
        self.test_register_with_correct_info()

        self.data["captcha"] = self._set_captcha(self.client.session)
        self.data["username"] = "test_user1"
        response = self.client.post(self.register_url, data=self.data)
        self.assertDictEqual(
            response.data, {"error": "error", "data": "Email already exists"}
        )


class SessionManagementAPITest(APITestCase):
    def setUp(self):
        self.user = self.create_user("test", "test123")
        self.url = self.reverse("session_management_api")
        # 启动一个请求来提供 session 数据
        login_url = self.reverse("user_login_api")
        self.client.post(login_url, data={"username": "test", "password": "test123"})

    def test_get_sessions(self):
        # 测试获取 session
        resp = self.client.get(self.url)
        self.assertSuccess(resp)
        data = resp.data["data"]
        self.assertEqual(len(data), 1)

    def test_delete_session_key(self):
        # 测试参数错误的情况
        resp = self.client.delete(self.url + "?abc=")
        self.assertFailed(resp)
        resp = self.client.delete(self.url + "?session_key= ")
        self.assertFailed(resp)

    def test_delete_session_with_invalid_key(self):
        # 测试删除 session
        resp = self.client.delete(self.url + "?session_key=aaaaaaaaaa")
        self.assertDictEqual(
            resp.data, {"error": "error", "data": "Invalid session_key"}
        )


class UserProfileAPITest(APITestCase):
    """测试用户详情功能"""

    def setUp(self):
        self.url = self.reverse("user_profile_api")

    def test_get_profile_without_login(self):
        # 测试在未登录的情况下，获取用户详情
        resp = self.client.get(self.url)
        self.assertDictEqual(resp.data, {"error": None, "data": None})

    def test_get_profile(self):
        # 测试获取用户详情
        self.create_user("test", "test123")
        resp = self.client.get(self.url)
        self.assertSuccess(resp)

        # 测试参数中有 username 的情况
        resp = self.client.get(self.url, data={"username": "test"})
        self.assertSuccess(resp)

        # 测试 username 错误的情况
        resp = self.client.get(self.url, data={"username": "adkjflwe"})
        self.assertFailed(resp)

    def test_update_profile(self):
        # 测试更新用户详情
        self.create_user("test", "test123")
        update_data = {"real_name": "zemal", "language": "en-US"}
        resp = self.client.put(self.url, data=update_data)
        self.assertSuccess(resp)
        # 检验数据是否一致
        data = resp.data["data"]
        self.assertEqual(data["real_name"], "zemal")
        self.assertEqual(data["language"], "en-US")


class AvatarUploadAPITest(APITestCase):
    """测试上传用户头像的功能"""

    def setUp(self):
        self.url = self.reverse("avatar_upload_api")
        self.user = self.create_admin()

    def test_upload_avatar(self):
        # 测试正常上传的情况
        with open(os.path.join(settings.BASE_DIR, "TEST/test/hue.png"), "rb") as f:
            resp = self.client.post(self.url, data={"image": f}, format="multipart")
            self.assertSuccess(resp)

        # 测试错误的图片格式
        with open(os.path.join(settings.BASE_DIR, "TEST/test/restore.json"), "rb") as f:
            resp = self.client.post(self.url, data={"image": f}, format="multipart")
            self.assertFailed(resp)

        # 测试错误的 参数
        with open(os.path.join(settings.BASE_DIR, "TEST/test/restore.json"), "rb") as f:
            resp = self.client.post(self.url, data={"abc": f}, format="multipart")
            self.assertFailed(resp)

        # 测试错误的图片大小
        with open(os.path.join(settings.BASE_DIR, "TEST/test/bigPic.jpg"), "rb") as f:
            resp = self.client.post(self.url, data={"image": f}, format="multipart")
            self.assertFailed(resp)


@mock.patch("apps.account.views.db.send_email_async.send")
class ApplyResetPasswordAPITest(CaptchaTest):
    """测试执行重置密码功能"""

    def setUp(self):
        self.create_user("test", "test123", login=False)
        user = User.objects.first()
        user.email = "test@abc.com"
        user.save()
        self.url = self.reverse("apply_reset_password_api")
        self.data = {
            "email": "test@abc.com",
            "captcha": self._set_captcha(self.client.session),
        }

    def _refresh_captcha(self):
        # 刷新验证码
        self.data["captcha"] = self._set_captcha(self.client.session)

    def test_apply_reset_password(self, send_email_send):
        # 测试重置密码
        resp = self.client.post(self.url, data=self.data)
        self.assertSuccess(resp)
        send_email_send.assert_called()

    def test_apply_reset_password_twice_in_20_mins(self, send_email_send):
        # 测试在 20 分钟内再次重置密码
        self.test_apply_reset_password()
        send_email_send.reset_mock()
        self._refresh_captcha()
        resp = self.client.post(self.url, data=self.data)
        self.assertDictEqual(
            resp.data,
            {
                "error": "error",
                "data": "You can only reset password once per 20 minutes",
            },
        )
        send_email_send.assert_not_called()


class UserChangeEmailAPITest(APITestCase):
    """测试修改邮箱功能"""

    def setUp(self):
        self.url = self.reverse("user_change_email_api")
        self.user = self.create_user("test", "test123")
        self.new_mail = "test@abc.com"
        self.data = {"password": "test123", "new_email": self.new_mail}

    def test_change_email_success(self):
        # 测试正常修改邮箱的情况
        resp = self.client.post(self.url, data=self.data)
        self.assertSuccess(resp)

    def test_wrong_password(self):
        # 测试使用错误的密码的情况
        self.data["password"] = "aaaa"
        resp = self.client.post(self.url, data=self.data)
        self.assertDictEqual(resp.data, {"error": "error", "data": "Wrong password"})

    def test_duplicate_email(self):
        # 测试邮箱重复的情况
        u = self.create_user("aa", "bb", login=False)
        u.email = self.new_mail
        u.save()
        resp = self.client.post(self.url, data=self.data)
        self.assertDictEqual(
            resp.data, {"error": "error", "data": "The email is owned by other account"}
        )


class UserChangePasswordAPITest(APITestCase):
    """测试修改密码功能"""

    def setUp(self):
        self.url = self.reverse("user_change_password_api")

        # 首先创建一个示例用户
        self.username = "test_user"
        self.old_password = "testuserpassword"
        self.new_password = "new_password"
        self.user = self.create_user(
            username=self.username, password=self.old_password, login=False
        )

        self.data = {
            "old_password": self.old_password,
            "new_password": self.new_password,
        }

    def test_login_required(self):
        # 测试需要登录的情况
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(
            response.data,
            {
                "error": "permission-denied",
                "data": "Sorry, You don't have permission to do that.",
            },
        )

    def test_valid_old_password(self):
        # 测试使用就密码来更改密码
        self.assertTrue(
            self.client.login(username=self.username, password=self.old_password)
        )
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.data, {"error": None, "data": "Succeeded"})
        self.assertTrue(
            self.client.login(username=self.username, password=self.new_password)
        )

    def test_invalid_old_password(self):
        # 测试使用错误的旧密码来更改密码
        self.assertTrue(
            self.client.login(username=self.username, password=self.old_password)
        )
        self.data["old_password"] = "invalid"
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(
            response.data, {"error": "error", "data": "Invalid old password"}
        )


class AdminUserTest(APITestCase):
    """测试管理员相关操作"""

    def setUp(self):
        self.user = self.create_super_admin(login=True)
        self.username = self.password = "test"
        self.regular_user = self.create_user(
            username=self.username, password=self.password, login=False
        )
        self.url = self.reverse("user_admin_api")
        self.data = {
            "id": self.regular_user.id,
            "username": self.username,
            "real_name": "test_name",
            "email": "test@abc.com",
            "admin_type": AdminType.REGULAR_USER,
            "case_permission": CasePermission.OWN,
            "is_disabled": False,
        }

    def test_user_list(self):
        # 测试正常获取的情况
        response = self.client.get(self.url)
        self.assertSuccess(response)
        # 测试参数中包含关键字的情况
        response = self.client.get(self.url, data={"keyword": "te"})
        self.assertSuccess(response)

    def test_get_user(self):
        # 测试 id 存在的情况
        response = self.client.get(self.url, data={"id": self.user.id})
        self.assertSuccess(response)
        # 测试 id 不存在的情况
        response = self.client.get(self.url, data={"id": 500})
        self.assertFailed(response)

    def test_edit_user_successfully(self):
        # 测试正常编辑用户信息的情况
        response = self.client.put(self.url, data=self.data)
        self.assertSuccess(response)
        # 检验数据是否一致
        resp_data = response.data["data"]
        self.assertEqual(resp_data["username"], self.username)
        self.assertEqual(resp_data["email"], "test@abc.com")
        self.assertEqual(resp_data["is_disabled"], False)
        self.assertEqual(resp_data["case_permission"], CasePermission.NONE)
        self.assertTrue(self.regular_user.check_password("test"))

        # 测试修改用户信息错误的情况 #
        # 用户不存在的情况
        wrong_data = deepcopy(self.data)
        wrong_data["id"] = 500
        response = self.client.put(self.url, data=wrong_data)
        self.assertFailed(response)
        # 测试用户名存在的情况
        wrong_data = deepcopy(self.data)
        wrong_data["username"] = "root"
        response = self.client.put(self.url, data=wrong_data)
        self.assertFailed(response)

    def test_edit_user_password(self):
        # 测试修改用户的密码
        data = self.data
        new_password = "testpassword"
        data["password"] = new_password
        response = self.client.put(self.url, data=data)
        self.assertSuccess(response)
        user = User.objects.get(id=self.regular_user.id)
        self.assertFalse(user.check_password(self.password))
        self.assertTrue(user.check_password(new_password))

    def test_import_users(self):
        # 测试批量导入用户的情况
        data = {
            "users": [
                ["user1", "pass1", "eami1@abc.com"],
                ["user2", "pass3", "eamil3@abc.com"],
            ]
        }
        resp = self.client.post(self.url, data)
        self.assertSuccess(resp)
        # successfully created 2 users
        self.assertEqual(User.objects.all().count(), 4)

    def test_import_duplicate_user(self):
        # 测试导入重复用户的情况
        data = {
            "users": [
                ["user1", "pass1", "eami1@abc.com"],
                ["user1", "pass1", "eami1@abc.com"],
            ]
        }
        resp = self.client.post(self.url, data)
        self.assertFailed(resp, "DETAIL:  Key (username)=(user1) already exists.")
        # 用户没有被创建，所以还是 2 个用户
        self.assertEqual(User.objects.all().count(), 2)

    def test_delete_users(self):
        # 测试删除用户
        self.test_import_users()
        user_ids = User.objects.filter(username__in=["user1", "user2"]).values_list(
            "id", flat=True
        )
        user_ids = ",".join([str(id) for id in user_ids])
        resp = self.client.delete(self.url + "?id=" + user_ids)
        self.assertSuccess(resp)
        self.assertEqual(User.objects.all().count(), 2)

        # 测试删除用户的 参数 id 不存在的情况
        resp = self.client.delete(self.url)
        self.assertFailed(resp)
        # 测试删除当前用户
        user_ids = user_ids + "," + str(self.user.id)
        resp = self.client.delete(self.url + "?id=" + user_ids)
        self.assertFailed(resp)


class GenerateUserAPITest(APITestCase):
    """测试批量生成用户功能"""

    def setUp(self):
        self.create_super_admin()
        self.url = self.reverse("generate_user_api")
        self.data = {
            "number_from": 100,
            "number_to": 105,
            "prefix": "pre",
            "suffix": "suf",
            "default_email": "test@abc.com",
            "password_length": 8,
        }

    def test_error_case(self):
        # 测试错误的情形

        # 测试用户名字符太多的情况
        data = deepcopy(self.data)
        data["prefix"] = "t" * 16
        data["suffix"] = "s" * 14
        resp = self.client.post(self.url, data=data)
        self.assertEqual(
            resp.data["data"], "Username should not more than 32 characters"
        )

        # 测试前后缀错误的情况
        data2 = deepcopy(self.data)
        data2["number_from"] = 106
        resp = self.client.post(self.url, data=data2)
        self.assertEqual(
            resp.data["data"], "Start number must be lower than end number"
        )

    @mock.patch("apps.account.views.admin.xlsxwriter.Workbook")
    def test_generate_user_success(self, mock_workbook):
        # 测试直接生成用户成功的情况
        resp = self.client.post(self.url, data=self.data)
        self.assertSuccess(resp)
        mock_workbook.assert_called()

    def test_get_excel(self):
        # 测试 file_id 不存在的情况
        resp = self.client.get(self.url)
        self.assertFailed(resp)
        # 测试 file_id 格式错误的情况
        resp = self.client.get(self.url, data={"file_id": "a3-3sdifj"})
        self.assertFailed(resp)
        # 测试 file_id 对应文件不存在的情况
        resp = self.client.get(self.url, data={"file_id": "abcdefgh"})
        self.assertFailed(resp)
        # 测试正常情况
        os.popen("touch /tmp/abcd.xlsx")
        resp = self.client.get(self.url, data={"file_id": "abcd"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class SSOAPITest(APITestCase):
    """测试单点登录的功能"""

    def setUp(self):
        self.user = self.create_super_admin()
        self.url = self.reverse("sso_api")

    def test_sso_login(self):
        # 先获取 token
        resp = self.client.get(self.url)
        self.assertSuccess(resp)
        self.token = resp.data["data"]["token"]

        resp = self.client.post(self.url, data={"token": self.token})
        self.assertSuccess(resp)
        self.assertDictEqual(
            resp.data["data"],
            {
                "admin_type": "Super Admin",
                "avatar": "/public/avatar/default.png",
                "username": "root",
            },
        )

        # 测试 token 无效的情况
        resp = self.client.post(self.url, data={"token": "adfjweofkw"})
        self.assertFailed(resp)
