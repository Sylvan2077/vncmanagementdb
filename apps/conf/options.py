#!/usr/bin/env python
# coding: utf-8

import functools
import threading
import time

from django.db import IntegrityError, transaction

from apps.conf.models import SysOptions as SysOptionsModel


class my_property:
    """
    在 metaclass 中使用，以实现：
    1. ttl = None，不缓存
    2. ttl is callable，条件缓存
    3. 缓存 ttl 秒
    """

    def __init__(self, func=None, fset=None, ttl=None):
        self.fset = fset
        self.local = threading.local()
        self.ttl = ttl
        self._check_ttl(ttl)
        self.func = func
        functools.update_wrapper(self, func)

    def _check_ttl(self, value):
        if value is None or callable(value):
            return
        return self._check_timeout(value)

    def _check_timeout(self, value):
        if not isinstance(value, int):
            raise ValueError("Invalid timeout type: {}".format(type(value)))
        if value < 0:
            raise ValueError("Invalid timeout value, it must >= 0")

    def __get__(self, obj, cls):
        if obj is None:
            return self

        now = time.time()
        if self.ttl:
            if hasattr(self.local, "value"):
                value, expire_at = self.local.value
                if now < expire_at:
                    return value

            value = self.func(obj)

            # 如果定义了条件缓存, ttl 是一个函数，返回要缓存多久；返回 0 代表不要缓存
            if callable(self.ttl):
                # 而且条件缓存若不要缓存，那就直接返回，不要设置 local
                timeout = self.ttl(value)
                self._check_timeout(timeout)

                if timeout == 0:
                    return value
                elif timeout > 0:
                    self.local.value = (value, now + timeout)
            else:
                # ttl 是一个数字
                self.local.value = (value, now + self.ttl)
            return value
        else:
            return self.func(obj)

    def __set__(self, obj, value):
        if not self.fset:
            raise AttributeError("can't set attribute")
        self.fset(obj, value)
        if hasattr(self.local, "value"):
            del self.local.value

    def setter(self, func):
        self.fset = func
        return self

    def __call__(self, func, *args, **kwargs) -> "my_property":
        if self.func is None:
            self.func = func
            functools.update_wrapper(self, func)
        return self


DEFAULT_SHORT_TTL = 2


class OptionKeys:
    """
    系统配置的选项
    """

    website_name = "website_name"
    website_name_shortcut = "website_name_shortcut"
    website_footer = "website_footer"
    throttling = "throttling"
    allow_users_file_browser = "allow_users_file_browser"
    install_path = "install_path"
    server_ip = "server_ip"
    display_count = "display_count"
    filebrowser_username = "filebrowser_username"
    filebrowser_password = "filebrowser_password"


class OptionDefaultValue:
    """定义系统选项的默认值"""

    website_name = "中物院软件产品试用平台"
    website_name_shortcut = "TestPlatformFE"
    website_footer = "Remote test platform Footer"
    # 是否允许注册
    allow_users_file_browser = False
    # 各服务管理员账户初始信息
    filebrowser_username = ""
    filebrowser_password = ""

    install_path = ""
    server_ip = ""
    display_count = 3

    # 对资源的限制
    throttling = {
        "ip": {"capacity": 1000, "fill_rate": 0.1, "default_capacity": 100},
        "user": {"capacity": 1000, "fill_rate": 0.1, "default_capacity": 100},
    }


class _SysOptionsMeta(type):
    @classmethod
    def _get_keys(cls):
        return [key for key in OptionKeys.__dict__ if not key.startswith("__")]

    @classmethod
    def _init_option(mcs):
        for item in mcs._get_keys():
            if not SysOptionsModel.objects.filter(key=item).exists():
                default_value = getattr(OptionDefaultValue, item)
                if callable(default_value):
                    default_value = default_value()
                try:
                    SysOptionsModel.objects.create(key=item, value=default_value)
                except IntegrityError:
                    pass

    @classmethod
    def _get_option(mcs, option_key):
        try:
            option = SysOptionsModel.objects.get(key=option_key)
            value = option.value
            return value
        except SysOptionsModel.DoesNotExist:
            mcs._init_option()
            return mcs._get_option(option_key)

    @classmethod
    def _set_option(mcs, option_key: str, option_value):
        try:
            with transaction.atomic():
                option = SysOptionsModel.objects.select_for_update().get(key=option_key)
                option.value = option_value
                option.save()
        except SysOptionsModel.DoesNotExist:
            mcs._init_option()
            mcs._set_option(option_key, option_value)

    @classmethod
    def _increment(mcs, option_key):
        try:
            with transaction.atomic():
                option = SysOptionsModel.objects.select_for_update().get(key=option_key)
                value = option.value + 1
                option.value = value
                option.save()
        except SysOptionsModel.DoesNotExist:
            mcs._init_option()
            return mcs._increment(option_key)

    @classmethod
    def set_options(mcs, options):
        for key, value in options:
            mcs._set_option(key, value)

    @classmethod
    def get_options(mcs, keys):
        result = {}
        for key in keys:
            result[key] = mcs._get_option(key)
        return result

    @my_property(ttl=DEFAULT_SHORT_TTL)
    def website_name(cls):
        return cls._get_option(OptionKeys.website_name)

    @website_name.setter
    def website_name(cls, value):
        cls._set_option(OptionKeys.website_name, value)

    @my_property(ttl=DEFAULT_SHORT_TTL)
    def website_name_shortcut(cls):
        return cls._get_option(OptionKeys.website_name_shortcut)

    @website_name_shortcut.setter
    def website_name_shortcut(cls, value):
        cls._set_option(OptionKeys.website_name_shortcut, value)

    @my_property(ttl=DEFAULT_SHORT_TTL)
    def website_footer(cls):
        return cls._get_option(OptionKeys.website_footer)

    @website_footer.setter
    def website_footer(cls, value):
        cls._set_option(OptionKeys.website_footer, value)

    @my_property
    def allow_users_file_browser(cls):
        return cls._get_option(OptionKeys.allow_users_file_browser)

    @allow_users_file_browser.setter
    def allow_users_file_browser(cls, value):
        cls._set_option(OptionKeys.allow_users_file_browser, value)

    @my_property
    def install_path(cls):
        return cls._get_option(OptionKeys.install_path)

    @install_path.setter
    def install_path(cls, value):
        cls._set_option(OptionKeys.install_path, value)

    @my_property
    def server_ip(cls):
        return cls._get_option(OptionKeys.server_ip)

    @server_ip.setter
    def server_ip(cls, value):
        cls._set_option(OptionKeys.server_ip, value)

    @my_property
    def display_count(cls):
        return cls._get_option(OptionKeys.display_count)

    @display_count.setter
    def display_count(cls, value):
        cls._set_option(OptionKeys.display_count, value)

    @my_property
    def filebrowser_username(cls):
        return cls._get_option(OptionKeys.filebrowser_username)

    @filebrowser_username.setter
    def filebrowser_username(cls, value):
        cls._set_option(OptionKeys.filebrowser_username, value)

    @my_property
    def filebrowser_password(cls):
        return cls._get_option(OptionKeys.filebrowser_password)

    @filebrowser_password.setter
    def filebrowser_password(cls, value):
        cls._set_option(OptionKeys.filebrowser_password, value)

    @my_property
    def throttling(cls):
        return cls._get_option(OptionKeys.throttling)

    @throttling.setter
    def throttling(cls, value):
        cls._set_option(OptionKeys.throttling, value)


class SysOptions(metaclass=_SysOptionsMeta):
    pass
