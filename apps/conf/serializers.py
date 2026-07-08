#!/usr/bin/env python
# coding: utf-8

from apps.utils.api import serializers


class CreateEditWebsiteConfigSerializer(serializers.Serializer):
    # 创建 更改网站配置
    website_name = serializers.CharField(max_length=64)
    website_name_shortcut = serializers.CharField(max_length=64)
    website_footer = serializers.CharField(max_length=1024 * 1024)
    # 创建App管理配置
    install_path = serializers.CharField(max_length=1024)
    server_ip = serializers.CharField(max_length=1024)
    display_count = serializers.IntegerField(min_value=0)
    # 关联服务配置
    allow_users_file_browser = serializers.BooleanField()
    filebrowser_username = serializers.CharField(max_length=1024)
    filebrowser_password = serializers.CharField(max_length=1024)
