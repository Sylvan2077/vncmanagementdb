#!/usr/bin/env python
# coding: utf-8

from apps.vncserver.models import VNCSession, AppManager
from apps.utils.api import serializers

# VNCSession列表相关字段
VNCSessionListFields = (
    "display_number",
    "run_software",
    "novnc_url",
    "node_url",
    "add_time",
    "add_time",
    "vncserver_starter"
)

# AppManager列表相关字段
AppManagerListFields = (
    "id",
    "name",
    "version",
    "full_name",
    "install_path",
    "bin_path",
    "complete_path",
    "install_status",
    "user_manual",
    "add_time",
    "App_creator",
    "visible"
)

AppManagerNameListFields = (
    "id",
    "name",
    "visible",
    "user_manual"
)

AppManagerNameIdFields = (
    "id",
    "version"
)


class VncSessionListSerializer(serializers.ModelSerializer):
    vncserver_starter = serializers.CharField(source="server_starter.username")

    class Meta:
        model = VNCSession
        fields = VNCSessionListFields


class CreateAppManagerSerializer(serializers.Serializer):
    """创建App时，校验的serializer"""

    # App名称
    name = serializers.CharField(max_length=1024, required=True, allow_blank=False, allow_null=False,
                                 error_messages={"blank": "App名称不能为空！"})

    # App版本
    version = serializers.CharField(max_length=1024, required=True, allow_blank=False, allow_null=False,
                                    error_messages={"blank": "App版本不能为空！"})

    # App名称版本
    full_name = serializers.CharField(max_length=1024, required=False, allow_blank=True, allow_null=True)

    # App安装路径
    install_path = serializers.CharField(max_length=1024, required=True, allow_blank=False, allow_null=False,
                                         error_messages={"blank": "App安装路径不能为空！"})

    # 授权密码
    auth_code = serializers.CharField(max_length=1024, required=False, allow_blank=True, allow_null=True)

    # APP安装包
    app_package = serializers.JSONField(required=True)

    # 是否可见
    visible = serializers.BooleanField()


class AppManagerListSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppManager
        fields = AppManagerListFields


class AppManagerNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppManager
        fields = AppManagerNameListFields


class AppManagerNameIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppManager
        fields = AppManagerNameIdFields
