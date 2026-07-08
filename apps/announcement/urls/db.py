#!/usr/bin/env python
# coding: utf-8

from apps.announcement.views.db import AnnouncementAPI
from django.conf.urls import url

urlpatterns = [
    url(r"^announcement/?$", AnnouncementAPI.as_view(), name="announcement_api"),
]
