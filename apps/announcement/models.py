#!/usr/bin/env python
# coding: utf-8

from apps.account.models import User
from apps.utils.models import RichTextField
from django.db import models


class Announcement(models.Model):
    """
    公告类，用来放在主页或者管理页中。
    """

    title = models.TextField(null=False, blank=False, help_text="公告的标题")
    category = models.TextField(null=False, blank=False, default="系统公告", help_text="公告的类别")
    content = RichTextField(null=False, blank=False, help_text="公告的具体内容")
    submitter = models.ForeignKey(User, on_delete=models.CASCADE, help_text="创建人")
    visible = models.BooleanField(default=True, help_text="是否公开可见")
    read_count = models.IntegerField(default=0, help_text="公告的浏览次数")
    create_time = models.DateTimeField(auto_now_add=True, help_text="公告创建时间")
    last_update_time = models.DateTimeField(auto_now=True, help_text="公告最近修改时间")
    # TODO: 添加置顶功能，例如定义 top 值字段，默认为 1，然后以此先排序，接着再按照创建时间排序等

    def __str__(self):
        return "Announcement[ title: {title} ]".format(title=self.title)

    class Meta:
        verbose_name = verbose_name_plural = "公告"
        db_table = "announcement"
        # db_table 表单在数据库中的表名称
        ordering = ("-last_update_time",)
