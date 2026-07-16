#!/usr/bin/env python
# coding: utf-8

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vncserver', '0012_displaypool'),
    ]

    operations = [
        migrations.AddField(
            model_name='vncsession',
            name='node_url',
            field=models.CharField(default='', help_text='创建session的VNC session manager节点URL', max_length=1024),
            preserve_default=False,
        ),
    ]