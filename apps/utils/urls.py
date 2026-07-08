#!/usr/bin/env python
# coding: utf-8

from django.conf.urls import url

from .views import SimditorFileUploadAPIView, SimditorImageUploadAPIView

urlpatterns = [
    url(r"^upload_image/?$", SimditorImageUploadAPIView.as_view(), name="upload_image"),
    url(r"^upload_file/?$", SimditorFileUploadAPIView.as_view(), name="upload_file"),
]
