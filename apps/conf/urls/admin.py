#!/usr/bin/env python
# coding: utf-8

from apps.conf.views import (WebsiteConfigAPI)
from django.conf.urls import url

urlpatterns = [
    url(r"^website/?$", WebsiteConfigAPI.as_view(), name="website_config_api"),
]
