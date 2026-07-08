#!/usr/bin/env python
# coding: utf-8

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser

# django 自带的user类
from django.db import models

# 这里的 josn field 只是一个包装，可以用 PostgreSQL 的原生格式或者其他软件包的格式
from apps.utils.models import JSONField


class AdminType(object):
    """配置用户类别"""

    # 常规用户
    REGULAR_USER = "Regular User"
    # 管理员用户
    ADMIN = "Admin"
    # 内部管理员
    INTERNAL_ADMIN = "Internal Admin"
    # 超级管理员用户
    SUPER_ADMIN = "Super Admin"


class CasePermission(object):
    """配置用户对输入算例的权限"""

    # 没有权限
    NONE = "None"
    # 只拥有自己创建的对象的权限
    OWN = "Own"
    # 拥有所有对象的权限
    ALL = "All"


class UserManager(models.Manager):
    # 自定义 用户 model
    use_in_migrations = True

    def get_by_natural_key(self, username):
        # 排序，抑制终端中输出的警告
        return self.get(**{"{}__iexact".format(self.model.USERNAME_FIELD): username})


class User(AbstractBaseUser):
    """自定义 User model"""

    username = models.TextField(unique=True)
    email = models.TextField(null=True)
    enterprise = models.TextField(null=True)
    encrypt_passwd = models.TextField(null=True)
    create_time = models.DateTimeField(auto_now_add=True, null=True)
    last_update_time = models.DateTimeField(auto_now=True, help_text="用户信息最近修改时间")
    # 管理员类别
    admin_type = models.TextField(default=AdminType.ADMIN)
    # TODO: 对超级管理员的个数做限定！
    # 权限的类别
    case_permission = models.TextField(default=CasePermission.OWN)
    # SSO auth token
    session_keys = JSONField(default=list)
    # 是否被禁用
    is_disabled = models.BooleanField(default=False)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def is_admin(self):
        return self.admin_type == AdminType.ADMIN

    def is_super_admin(self):
        return self.admin_type == AdminType.SUPER_ADMIN

    def is_internal_admin(self):
        return self.admin_type == AdminType.INTERNAL_ADMIN

    def is_admin_role(self):
        return self.admin_type in [
            AdminType.ADMIN,
            AdminType.SUPER_ADMIN,
            AdminType.INTERNAL_ADMIN,
        ]

    def is_manager_role(self):
        return self.admin_type in [AdminType.SUPER_ADMIN, AdminType.INTERNAL_ADMIN]

    def can_mgmt_all_db(self):
        return self.case_permission == CasePermission.ALL

    class Meta:
        # 修改数据库中的表名为 user
        verbose_name = verbose_name_plural = "用户"
        db_table = "user"
        ordering = ("-last_update_time",)


class UserProfile(models.Model):
    """用户的简历，在用户详情页展示"""

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    create_time = models.DateTimeField(auto_now_add=True, help_text="用户简历创建时间")
    last_update_time = models.DateTimeField(auto_now=True, help_text="用户简历最近修改时间")
    real_name = models.TextField(null=True)
    # 用户的头像
    avatar = models.TextField(
        default="{}/default.png".format(settings.AVATAR_URI_PREFIX)
    )
    blog = models.URLField(null=True)
    # 用来设置该用户所使用的界面语言
    language = models.TextField(null=True)
    # 用来记录用户当前启动的桌面数
    started_display_count = models.BigIntegerField(default=0)

    class Meta:
        verbose_name = verbose_name_plural = "用户简历"
        db_table = "user_profile"
        ordering = ("-last_update_time",)
