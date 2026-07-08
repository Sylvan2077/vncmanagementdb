#!/usr/bin/env python
# coding: utf-8

from django.contrib.postgres.fields import JSONField
from django.db import models


class SysOptions(models.Model):
    """定义系统选项，使用 json 实现，主要是键值对的形式"""

    key = models.TextField(unique=True, db_index=True)
    value = JSONField()

    class Meta:
        verbose_name = verbose_name_plural = r"系统选项"
        db_table = "sysoptions"
        ordering = ["id"]
