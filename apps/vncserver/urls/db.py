#!/usr/bin/env python
# coding: utf-8

from apps.vncserver.views.db import (VncServerManager, VncServerOTPManager,
                                     AppConfigList, GetUserManual, AppNameId)
from django.conf.urls import url

urlpatterns = [
    url(r"^vncserver/?$", VncServerManager.as_view(), name="manager_vncserver"),
    url(r"^getnewOTP/?$", VncServerOTPManager.as_view(), name="manager_vncserver_otp"),
    url(r"^app_config_list/?$", AppConfigList.as_view(), name="get_app_config_list"),
    url(r"^get_user_manual/?$", GetUserManual.as_view(), name="get_user_manual"),
    url(r"^app_name_id/?$", AppNameId.as_view(), name="get_app_name_id"),
]