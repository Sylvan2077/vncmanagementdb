#!/usr/bin/env python
# coding: utf-8

from apps.account.models import AdminType, CasePermission, User, UserProfile
from django import forms
from rest_framework import serializers


class UserLoginSerializer(serializers.Serializer):
    # 用户登录需要的字段
    username = serializers.CharField()
    password = serializers.CharField()


class UsernameOrEmailCheckSerializer(serializers.Serializer):
    # 检测用户名或邮箱的字段
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)


class UserRegisterSerializer(serializers.Serializer):
    # 用户注册时需要的字段
    username = serializers.CharField(max_length=32)
    password = serializers.CharField(min_length=6)
    captcha = serializers.CharField()


class UserChangePasswordSerializer(serializers.Serializer):
    # 用户修改密码时需要的字段
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=6)


class UserChangeEmailSerializer(serializers.Serializer):
    # 用户更改邮箱时需要的字段
    password = serializers.CharField()
    new_email = serializers.EmailField(max_length=64)


class GenerateUserSerializer(serializers.Serializer):
    # 批量生成用户时需要的字段
    prefix = serializers.CharField(max_length=16, allow_blank=True)
    suffix = serializers.CharField(max_length=16, allow_blank=True)
    number_from = serializers.IntegerField()
    number_to = serializers.IntegerField()
    password_length = serializers.IntegerField(max_value=16, default=8)


class ImportUserSeralizer(serializers.Serializer):
    # 导入用户时需要的字段
    users = serializers.ListField(
        child=serializers.ListField(child=serializers.CharField(max_length=64))
    )


class UserAdminSerializer(serializers.ModelSerializer):
    # 用户信息的字段
    real_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "enterprise",
            "create_time",
            "admin_type",
            "case_permission",
            "real_name",
            "last_login",
            "is_disabled",
        ]

    def get_real_name(self, obj):
        return obj.userprofile.real_name


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "create_time",
            "admin_type",
            "case_permission",
            "last_login",
            "is_disabled",
        ]


class UserProfileSerializer(serializers.ModelSerializer):
    # 用户详情需要的字段
    user = UserSerializer()
    real_name = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        self.show_real_name = kwargs.pop("show_real_name", False)
        super(UserProfileSerializer, self).__init__(*args, **kwargs)

    def get_real_name(self, obj):
        return obj.real_name if self.show_real_name else None


class EditUserSerializer(serializers.Serializer):
    # 编辑用户时需要的字段
    id = serializers.IntegerField()
    username = serializers.CharField(max_length=32)
    real_name = serializers.CharField(max_length=32, allow_blank=True, allow_null=True)
    password = serializers.CharField(
        min_length=6, allow_blank=True, required=False, default=None
    )
    email = serializers.EmailField(max_length=64)
    enterprise = serializers.CharField(max_length=128)
    admin_type = serializers.ChoiceField(
        choices=(AdminType.REGULAR_USER, AdminType.ADMIN, AdminType.SUPER_ADMIN, AdminType.INTERNAL_ADMIN)
    )
    case_permission = serializers.ChoiceField(
        choices=(CasePermission.NONE, CasePermission.OWN, CasePermission.ALL)
    )
    is_disabled = serializers.BooleanField()


class EditUserProfileSerializer(serializers.Serializer):
    # 编辑用户详情时需要的字段
    real_name = serializers.CharField(max_length=32, allow_null=True, required=False)
    avatar = serializers.CharField(max_length=256, allow_blank=True, required=False)
    blog = serializers.URLField(max_length=256, allow_blank=True, required=False)
    language = serializers.CharField(max_length=32, allow_blank=True, required=False)


class ApplyResetPasswordSerializer(serializers.Serializer):
    # 应用重置密码时需要的字段
    email = serializers.EmailField()
    captcha = serializers.CharField()


class ResetPasswordSerializer(serializers.Serializer):
    # 重置密码时需要的字段
    token = serializers.CharField()
    password = serializers.CharField(min_length=6)
    captcha = serializers.CharField()


class SSOSerializer(serializers.Serializer):
    # 单点登录时需要的字段
    token = serializers.CharField()


class TwoFactorAuthCodeSerializer(serializers.Serializer):
    code = serializers.IntegerField()


class ImageUploadForm(forms.Form):
    image = forms.FileField()


class FileUploadForm(forms.Form):
    file = forms.FileField()
