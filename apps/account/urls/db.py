#!/usr/bin/env python
# coding: utf-8

from apps.account.views.db import (AvatarUploadAPI,
                                   SessionManagementAPI,
                                   UserChangeEmailAPI, UserChangePasswordAPI,
                                   UserLoginAPI, UserLogoutAPI,
                                   UsernameOrEmailCheck, UserProfileAPI,
                                   UserRegisterAPI)
from apps.utils.captcha.views import CaptchaAPIView
from django.conf.urls import url

urlpatterns = [
    url(r"^login/?$", UserLoginAPI.as_view(), name="user_login_api"),
    url(r"^logout/?$", UserLogoutAPI.as_view(), name="user_logout_api"),
    url(r"^register/?$", UserRegisterAPI.as_view(), name="user_register_api"),
    url(r"^captcha/?$", CaptchaAPIView.as_view(), name="show_captcha"),
    url(
        r"^change_password/?$",
        UserChangePasswordAPI.as_view(),
        name="user_change_password_api",
    ),
    url(
        r"^change_email/?$", UserChangeEmailAPI.as_view(), name="user_change_email_api"
    ),
    url(
        r"^check_username_or_email",
        UsernameOrEmailCheck.as_view(),
        name="check_username_or_email",
    ),
    url(r"^profile/?$", UserProfileAPI.as_view(), name="user_profile_api"),
    url(r"^upload_avatar/?$", AvatarUploadAPI.as_view(), name="avatar_upload_api"),
    url(r"^sessions/?$", SessionManagementAPI.as_view(), name="session_management_api"),
]
