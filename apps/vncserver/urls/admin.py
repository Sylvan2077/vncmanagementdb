#!/usr/bin/env python
# coding: utf-8

from apps.vncserver.views.admin import (VncServerManagement,VncServerOTPGenerater,AppManagerConfig,AppConfigList,UploadManual,CheckAppConfig,UploadApp,GetInstallLog,GetPkgSubdir,ReinstallApp)
from django.conf.urls import url

urlpatterns = [
    url(r"^manager_vncserver/?$", VncServerManagement.as_view(), name="admin_manager_vncserver"),
    url(r"^generate_otp/?$", VncServerOTPGenerater.as_view(), name="admin_generate_otp"),
    url(r"^app_config/?$", AppManagerConfig.as_view(), name="app_manager_config"),
    url(r"^app_config_list/?$", AppConfigList.as_view(), name="get_app_config_list"),
    url(r"^upload_manual/?$", UploadManual.as_view(), name="upload_manual"),
    url(r"^upload_pkg/?$", UploadApp.as_view(), name="upload_pkg"),
    url(r"^check_app_config/?$", CheckAppConfig.as_view(), name="check_app_config"),
    url(r"^get_install_log/?$", GetInstallLog.as_view(), name="get_install_log"),
    url(r"^get_pkg_subdir/?$", GetPkgSubdir.as_view(), name="get_pkg_subdir"),
    url(r"^reinstall_app/?$", ReinstallApp.as_view(), name="reinstall_app")
]