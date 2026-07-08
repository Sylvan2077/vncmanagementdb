#!/usr/bin/env python
# coding: utf-8

from django.contrib.auth import get_user_model
from django.db import models
from apps.utils.models import JSONField


class VNCSession(models.Model):
    """vnc session 信息"""

    # display的id
    session_id = models.CharField(max_length=1024, help_text="vnc session ID")

    # display的id
    display_number = models.IntegerField(unique=True, help_text="display的序号")

    # display中启动的软件
    run_software = models.CharField(max_length=1024,  help_text="桌面中启动的软件")

    # novnc的访问地址
    novnc_url = models.URLField(max_length=1024,  help_text="novnc访问url")

    # 桌面启动的时间
    add_time = models.DateTimeField(auto_now_add=True,  help_text="桌面启动时间")

    # 桌面的启动人
    server_starter = models.ForeignKey(
        get_user_model(),
        null=True,
        related_name="vncserver_starter",
        on_delete=models.CASCADE,
        help_text="桌面的启动人",
    )

    class Meta:
        verbose_name = verbose_name_plural = "远程桌面"
        db_table = "vnc_session_info"
        ordering = ["display_number"]


class AppManager(models.Model):
    """App 管理"""
    
    # App名称
    name = models.CharField(max_length=1024,  help_text="App名称")

    # App版本
    version = models.CharField(max_length=1024,  help_text="App版本")

    # App名称-版本
    full_name = models.CharField(max_length=1024,  help_text="App名称版本")

    # App安装路径
    install_path = models.CharField(max_length=1024,  help_text="App安装路径")

    # 可执行文件路径
    bin_path = models.CharField(max_length=1024,  help_text="可执行文件路径")

    # APP的完整路径
    complete_path = models.CharField(default="", max_length=1024,  help_text="APP的完整路径")

    # 用户手册
    user_manual = JSONField(db_index=True, null=True, blank=True, default=dict)

    # APP安装包
    app_package = JSONField(db_index=True, null=True, blank=True, default=dict)

    # 安装状态
    install_status = models.CharField(max_length=1024, help_text="安装状态")

    # 安装日志
    install_log = models.CharField(max_length=1024, help_text="安装日志")

    # 安装包授权码
    auth_code = models.CharField(max_length=1024, help_text="安装包授权码")

    # App添加时间
    add_time = models.DateTimeField(auto_now_add=True, help_text="App被添加的时间")

    # 是否可见
    visible = models.BooleanField(default=True, help_text="是否可见")

    # App更改时间
    change_time = models.DateTimeField(auto_now=True, help_text="App被更改的时间")

    # App的创建人
    App_creator = models.ForeignKey(
        get_user_model(),
        null=True,
        related_name="App_creator",
        on_delete=models.CASCADE,
        help_text="App的创建人",
    )

    class Meta:
        verbose_name = verbose_name_plural = "App"
        db_table = "App_manager"
        ordering = ["id"]
