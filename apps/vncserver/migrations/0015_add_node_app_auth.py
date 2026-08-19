#!/usr/bin/env python
# coding: utf-8

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('vncserver', '0014_add_vnc_urls'),
    ]

    operations = [
        migrations.CreateModel(
            name='NodeAppAuth',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_enabled', models.BooleanField(default=True, help_text='是否启用')),
                ('add_time', models.DateTimeField(auto_now_add=True, help_text='授权时间')),
                ('app', models.ForeignKey(help_text='APP', on_delete=django.db.models.deletion.CASCADE, to='vncserver.appmanager')),
                ('vnc_url', models.ForeignKey(help_text='VNC节点', on_delete=django.db.models.deletion.CASCADE, to='vncserver.vncurl')),
            ],
            options={
                'verbose_name': '节点APP授权',
                'verbose_name_plural': '节点APP授权',
                'db_table': 'node_app_auth',
                'unique_together': {('vnc_url', 'app')},
            },
        ),
        migrations.AddField(
            model_name='vncurl',
            name='apps',
            field=models.ManyToManyField(blank=True, help_text='授权APP', related_name='vnc_nodes', through='vncserver.nodeappauth', to='vncserver.appmanager', verbose_name='授权APP'),
        ),
    ]