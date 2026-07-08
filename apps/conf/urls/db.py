#!/usr/bin/env python
# coding: utf-8

from django.conf.urls import url

from apps.conf.views import WebsiteConfigAPI

urlpatterns = [
    url(r"^website/?$", WebsiteConfigAPI.as_view(), name="website_info_api"),
]
