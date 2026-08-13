#!/usr/bin/env python
# coding: utf-8

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vncserver', '0013_add_session_id_and_node_url'),
    ]

    operations = [
        migrations.CreateModel(
            name='VncUrl',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip', models.CharField(help_text='节点IP地址', max_length=255)),
                ('port', models.IntegerField(help_text='节点端口')),
                ('description', models.CharField(blank=True, help_text='节点描述', max_length=1024, null=True)),
                ('is_enabled', models.BooleanField(default=True, help_text='是否启用')),
                ('add_time', models.DateTimeField(auto_now_add=True, help_text='添加时间')),
            ],
            options={
                'verbose_name': 'VNC节点配置',
                'verbose_name_plural': 'VNC节点配置',
                'db_table': 'vnc_urls',
                'ordering': ['id'],
            },
        ),
    ]