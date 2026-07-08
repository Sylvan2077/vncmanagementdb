#!/usr/bin/env python
# coding: utf-8

import functools

from apps.account.models import CasePermission
from apps.utils.api import APIError, JSONResponse


class BasePermissionDecorator(object):
    """基本的权限装饰器"""

    def __init__(self, func):
        self.func = func

    def __get__(self, obj, obj_type):
        return functools.partial(self.__call__, obj)

    def error(self, data):
        return JSONResponse.response({"error": "permission-denied", "data": data})

    def __call__(self, *args, **kwargs):
        self.request = args[1]

        if self.check_permission():
            # 检测用户是否被禁用
            if self.request.user.is_disabled:
                return self.error("Your account is disabled")
            return self.func(*args, **kwargs)
        else:
            # 否则先登录
            return self.error("Sorry, You don't have permission to do that.")

    def check_permission(self):
        raise NotImplementedError()


class login_required(BasePermissionDecorator):
    """检查用户是否登录"""

    def check_permission(self):
        # 检测是否已经登录
        return self.request.user.is_authenticated


class super_admin_required(BasePermissionDecorator):
    """检查用户是否是超级管理员"""

    def check_permission(self):
        # 检测是否是超级管理员
        user = self.request.user
        return user.is_authenticated and user.is_super_admin()

class manager_admin_required(BasePermissionDecorator):
    """检查用户是否是超级管理员"""

    def check_permission(self):
        # 检测是否是超级管理员或者内部管理员
        user = self.request.user
        return user.is_authenticated and user.is_manager_role()

class admin_role_required(BasePermissionDecorator):
    """检查用户是否是管理员"""

    def check_permission(self):
        # 检测是否是管理员
        user = self.request.user
        return user.is_authenticated and user.is_admin_role()


class ensure_submitter_required(admin_role_required):
    """检查是否对 结果数据库 有相应权限"""

    def check_permission(self):
        # 检测是否有数据库相关的权限
        if not super(ensure_submitter_required, self).check_permission():
            return False
        if self.request.user.case_permission == CasePermission.NONE:
            return False
        return True


def ensure_submitter(obj, user):
    """保证对象是由该用户创建的"""

    e = APIError(msg="Sorry, you have no permission to do this!")
    if not user.is_admin_role():
        # 检测是否是管理员类别
        raise e
    if user.is_manager_role():
        # 检测是否是超级管理员
        return
    if not user.can_mgmt_all_db() and obj.submitter != user:
        raise e
