#!/usr/bin/env python
# coding: utf-8

from django.conf.urls import url

from apps.account.views.admin import (
    GenerateUserAPI,
    UserAdminAPI,
    DleteServerUsers,
    UploadLogoAPI,
    UploadRegisterData,
    SynchronizeAPI,
)

urlpatterns = [
    url(r"^user/?$", UserAdminAPI.as_view(), name="user_admin_api"),
    url(r"^generate_user/?$", GenerateUserAPI.as_view(), name="generate_user_api"),
    url(
        r"^upload_register_data/?$",
        UploadRegisterData.as_view(),
        name="upload_register_data",
    ),
    url(r"^server_user/?$", DleteServerUsers.as_view(), name="server_user_api"),
    url(r"^upload_logo/?$", UploadLogoAPI.as_view(), name="upload_logo_api"),
    url(r"^synchronize/?$", SynchronizeAPI.as_view(), name="synchronize_api"),
]
