#!/usr/bin/env python
# coding: utf-8

from apps.utils.xss_filter import XSSHtml
from django.contrib.postgres.fields import JSONField  # NOQA
from django.db import models


class RichTextField(models.TextField):
    def get_prep_value(self, value):
        with XSSHtml() as parser:
            return parser.clean(value or "")
