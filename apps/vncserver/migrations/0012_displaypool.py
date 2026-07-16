#!/usr/bin/env python
# coding: utf-8

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vncserver', '0011_appmanager_full_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='DisplayPool',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField(help_text='预分配的 display number', unique=True)),
                ('is_used', models.BooleanField(default=False, help_text='是否已被使用')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='创建时间')),
            ],
            options={
                'db_table': 'display_pool',
                'ordering': ['number'],
                'verbose_name': 'Display预分配池',
                'verbose_name_plural': 'Display预分配池',
            },
        ),
    ]