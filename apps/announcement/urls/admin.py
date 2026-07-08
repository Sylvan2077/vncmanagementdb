#!/usr/bin/env python
# coding: utf-8

from apps.announcement.views.admin import AnnouncementAdminAPI
from django.conf.urls import url

urlpatterns = [
    url(
        r"^announcement/?$",
        AnnouncementAdminAPI.as_view(),
        name="announcement_admin_api",
    ),
]
