#!/usr/bin/env python
# coding: utf-8

import logging
import os

from apps.account.decorators import super_admin_required
from apps.conf.options import SysOptions
from apps.conf.serializers import (
    CreateEditWebsiteConfigSerializer,
)
from apps.utils.api import APIView, validate_serializer
from apps.utils.client import user_manager_client
from apps.utils.handle_passwd import encode_passwd, decode_passwd
from apps.utils.xss_filter import XSSHtml

logger = logging.getLogger(__name__)


class WebsiteConfigAPI(APIView):
    """
    网站配置相关方法
    """

    def get(self, request):
        # 获取网站配置信息
        ret = {
            key: getattr(SysOptions, key)
            for key in [
                "website_name",
                "website_name_shortcut",
                "website_footer",
                "install_path",
                "server_ip",
                "display_count",
                "allow_users_file_browser",
                "filebrowser_username",
            ]
        }
        if request.user.username:
            if request.user.admin_type == "Super Admin":
                ret["filebrowser_password"] = decode_passwd(
                    SysOptions.filebrowser_password
                )
        return self.success(ret)

    @super_admin_required
    @validate_serializer(CreateEditWebsiteConfigSerializer)
    def post(self, request):
        # 保存关联服务配置
        filebrowser_password = request.data.get("filebrowser_password")
        config_data = {
            "website_name": request.data.get("website_name"),
            "website_name_shortcut": request.data.get("website_name_shortcut"),
            "server_ip": request.data.get("server_ip"),
            "display_count": request.data.get("display_count"),
            "allow_users_file_browser": request.data.get("allow_users_file_browser"),
            "filebrowser_username": request.data.get("filebrowser_username"),
            "filebrowser_password": filebrowser_password,
        }
        msg = user_manager_client.login(config_data)
        if msg:
            return self.error(msg)
        if filebrowser_password:
            config_data["filebrowser_password"] = encode_passwd(
                request.data.get("filebrowser_password")
            )
        # 保存APP安装路径
        install_path = request.data.get("install_path")
        if not os.path.exists(install_path):
            os.mkdir(install_path)
        config_data["install_path"] = install_path
        # 对 footer 做 xss 过滤
        website_footer = request.data.get("website_footer")
        with XSSHtml() as parser:
            config_data["website_footer"] = parser.clean(website_footer)
        for k, v in config_data.items():
            setattr(SysOptions, k, v)
        return self.success()
