#!/usr/bin/env python
# coding: utf-8

import logging
import os
from importlib import import_module

import magic
from django.conf import settings
from django.contrib import auth
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie

from apps.account.decorators import login_required, manager_admin_required
from apps.account.models import User, UserProfile
from apps.account.serializers import (
    EditUserProfileSerializer,
    ImageUploadForm,
    UserChangeEmailSerializer,
    UserChangePasswordSerializer,
    UserLoginSerializer,
    UsernameOrEmailCheckSerializer,
    UserProfileSerializer,
    UserRegisterSerializer,
)
from apps.utils.client import user_manager_client
from apps.utils.api import APIView, validate_serializer
from apps.utils.captcha import Captcha
from apps.utils.handle_passwd import encode_passwd
from apps.utils.shortcuts import datetime2str, rand_str
from apps.vncserver.models import VNCSession

logger = logging.getLogger(__name__)


class UserProfileAPI(APIView):
    @method_decorator(ensure_csrf_cookie)
    def get(self, request, **kwargs):
        """
        判断是否登录， 若登录返回用户信息
        """
        user = request.user
        if not user.is_authenticated:
            return self.success()
        show_real_name = False
        username = request.GET.get("username")
        try:
            if username:
                user = User.objects.get(username=username, is_disabled=False)
            else:
                user = request.user
                # api 返回的是自己的信息，可以返 real_name
                show_real_name = True
            profile = user.userprofile
            profile.started_display_count = VNCSession.objects.filter(
                server_starter=user.id
            ).count()
            profile.save()
        except User.DoesNotExist:
            return self.error("User does not exist")
        return self.success(
            UserProfileSerializer(user.userprofile, show_real_name=show_real_name).data
        )

    @validate_serializer(EditUserProfileSerializer)
    @login_required
    def put(self, request):
        """
        修改用户的详情
        """
        data = request.data
        user_profile = request.user.userprofile
        # 更新各个属性
        for k, v in data.items():
            setattr(user_profile, k, v)
        user_profile.save()
        return self.success(
            UserProfileSerializer(user_profile, show_real_name=True).data
        )


class AvatarUploadAPI(APIView):
    request_parsers = ()

    @login_required
    def post(self, request):
        """
        上传用户的头像
        """
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            avatar = form.cleaned_data["image"]
        else:
            return self.error("Invalid file content")
        # 图像大小限制
        if avatar.size > 2 * 1024 * 1024:
            return self.error("Picture is too large")
        # 图像格式的限制
        tempImage = os.path.join(settings.TMP_DIR, "tmpImg")
        with open(tempImage, "wb") as tempImg:
            for chunk in avatar:
                tempImg.write(chunk)
        upFileType = magic.from_file(tempImage, mime=True)
        if upFileType not in [
            "image/gif",
            "image/jpeg",
            "image/png",
            "image/bmp",
            "image/svg+xml",
        ]:
            return self.error("Unsupported file format")
        os.remove(tempImage)

        suffix = os.path.splitext(avatar.name)[-1]
        name = rand_str(10) + suffix
        avatarFileName = os.path.join(settings.AVATAR_UPLOAD_DIR, name)
        with open(avatarFileName, "wb") as img:
            for chunk in avatar:
                img.write(chunk)
        user_profile = request.user.userprofile

        user_profile.avatar = os.path.join(settings.AVATAR_URI_PREFIX, name)
        user_profile.save()
        return self.success("Succeeded")


class UserLoginAPI(APIView):
    @validate_serializer(UserLoginSerializer)
    @method_decorator(csrf_exempt)
    def post(self, request):
        """
        用户登录的 API
        """
        data = request.data
        user = auth.authenticate(username=data["username"], password=data["password"])
        # 假如用户名或密码错误时返回 None
        if user:
            if user.is_disabled:
                return self.error("Your account has been disabled")
            else:
                auth.login(request, user)
                return self.success("Succeeded")
        else:
            return self.error("帐号或密码错误!")


class UserLogoutAPI(APIView):
    """
    用户退出
    """

    def get(self, request):
        # 直接登出
        auth.logout(request)
        return self.success()


class UsernameOrEmailCheck(APIView):
    @validate_serializer(UsernameOrEmailCheckSerializer)
    def post(self, request):
        """
        检查用户名或者邮箱是否重复
        """
        data = request.data
        # True 就意味着已经存在
        result = {"username": False, "email": False}
        # 检验用户名
        if data.get("username"):
            result["username"] = User.objects.filter(username=data["username"]).exists()
        # 检验邮箱
        if data.get("email"):
            result["email"] = User.objects.filter(email=data["email"]).exists()
        return self.success(result)


class UserRegisterAPI(APIView):
    @validate_serializer(UserRegisterSerializer)
    @manager_admin_required
    def post(self, request):
        """
        用户注册 API
        """

        # 设定相关数据
        data = request.data
        captcha = Captcha(request)
        # 检测验证码
        if not captcha.check(data["captcha"]):
            return self.error("验证码错误！")
        # 检测用户名
        if User.objects.filter(username=data["username"]).exists():
            return self.error("用户名已经存在！")
        # 创建远程试用系统用户
        user = User.objects.create(username=data["username"])
        user.set_password(data["password"])
        encrypt_passwd = encode_passwd(data["password"])
        user.encrypt_passwd = encrypt_passwd
        user.save()
        # 创建用户详情
        UserProfile.objects.create(user=user)
        # 创建关联服务用户
        form_data = {"user_name": data["username"], "user_passwd": data["password"]}
        msg = user_manager_client.register(form_data)
        if msg:
            # 删除远程试用系统用户
            User.objects.filter(username=data["username"]).delete()
            return self.error(msg)
        return self.success("感谢注册，现在你可以登录了！")


class UserChangeEmailAPI(APIView):
    @validate_serializer(UserChangeEmailSerializer)
    @login_required
    def post(self, request):
        """
        用户改变其邮箱
        """
        data = request.data
        user = auth.authenticate(
            username=request.user.username, password=data["password"]
        )
        if user:
            # 执行各类检验
            data["new_email"] = data["new_email"]
            if User.objects.filter(email=data["new_email"]).exists():
                return self.error("The email is owned by other account")
            user.email = data["new_email"]
            user.save()
            return self.success("Succeeded")
        else:
            return self.error("Wrong password")


class UserChangePasswordAPI(APIView):
    @validate_serializer(UserChangePasswordSerializer)
    @login_required
    def post(self, request):
        """
        用户改变其登录密码
        """
        data = request.data
        username = request.user.username
        user = auth.authenticate(username=username, password=data["old_password"])
        if not user:
            return self.error("原密码错误！")
        if user.is_super_admin():
            is_fb_superadmin = True
        else:
            is_fb_superadmin = False
        new_password = data["new_password"]
        form_data = {
            "username": username,
            "new_password": new_password,
            "old_password": data["old_password"],
            "is_fb_superadmin": is_fb_superadmin,
        }
        msg = user_manager_client.change_passwd(form_data)
        if msg:
            return self.error(msg)
        # 修改试用系统密码
        user.set_password(data["new_password"])
        # 加密管理员密码
        encrypt_passwd = encode_passwd(new_password)
        user.encrypt_passwd = encrypt_passwd
        user.save()
        return self.success("Succeeded")


class SessionManagementAPI(APIView):
    @login_required
    def get(self, request):
        """
        获取 session
        """
        # 首先获取 session
        engine = import_module(settings.SESSION_ENGINE)
        session_store = engine.SessionStore
        current_session = request.session.session_key
        session_keys = request.user.session_keys
        result = []
        modified = False
        for key in session_keys[:]:
            session = session_store(key)
            # session does not exist or is expiry
            if not session._session or "ip" not in session._session:
                session_keys.remove(key)
                modified = True
                continue

            s = {}
            if current_session == key:
                s["current_session"] = True
            # 设定 session 的相关信息
            s["ip"] = session["ip"]
            s["user_agent"] = session["user_agent"]
            s["last_activity"] = datetime2str(session["last_activity"])
            s["session_key"] = key
            result.append(s)
        if modified:
            request.user.save()
        return self.success(result)

    @login_required
    def delete(self, request):
        """
        删除 session
        """
        session_key = request.GET.get("sessionKey")
        sessions = request.data.get("sessions")

        if session_key is None and sessions is None:
            return self.success()

        if session_key:
            # 删除单个 session
            request.session.delete(session_key)
            if session_key in request.user.session_keys:
                request.user.session_keys.remove(session_key)
                request.user.save()
                return self.success("Succeeded")
            else:
                return self.error("Invalid session_key")
        if sessions:
            # 批量删除多个 session
            to_rm_sessions = sessions.split(",")
            for session_key in to_rm_sessions:
                request.session.delete(session_key)
                if session_key in request.user.session_keys:
                    request.user.session_keys.remove(session_key)
                    request.user.save()
            return self.success("Succeeded")
