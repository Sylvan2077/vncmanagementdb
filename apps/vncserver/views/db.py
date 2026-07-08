#!/usr/bin/env python
# coding: utf-8

import logging
import os
import re

from django.conf import settings
from django.db import transaction

from apps.conf.options import SysOptions
from apps.utils.api import APIView
from apps.utils.client.vnc_session_client import (
    start_vnc_session,
    update_otp,
    close_session,
)
from apps.vncserver.models import VNCSession, AppManager
from apps.vncserver.serializers import (
    VncSessionListSerializer,
    AppManagerListSerializer, AppManagerNameIdSerializer, AppManagerNameSerializer,
)
import json

logger = logging.getLogger(__name__)


def next_display_number(vnc_session_data):
    if len(list(zip(*vnc_session_data))) > 0:
        existIDs = set(list(zip(*vnc_session_data))[0])
        maxID = max(existIDs)
        expectedNumbers = set(range(1, maxID + 1))
        diffNumbers = sorted(expectedNumbers.difference(existIDs))

        if len(diffNumbers) > 0:
            return diffNumbers[0]
        else:
            return maxID + 1
    else:
        return 1


class VncServerManager(APIView):
    """VNC Session 管理类"""

    def get(self, request):
        """查询VNC Server 网址"""
        # 1.请求带display number时，校验此vncserver是否还存在。
        displayNum = request.GET.get("display_number")
        if displayNum:
            try:
                existVncserver = VNCSession.objects.get(display_number=displayNum)
            except VNCSession.DoesNotExist:
                error_msg = "该APP已经关闭！"
                logger.error(error_msg)
                return self.error(error_msg)
        # 2.请求不带任何参数时，返回所有启动的vncserver信息
        all_vncservers = VNCSession.objects.all()
        vncservers = all_vncservers.filter(server_starter=request.user)
        vncservers = vncservers.order_by("add_time")
        data = self.paginate_data(request, vncservers, VncSessionListSerializer)
        return self.success(data)

    def post(self, request):
        vncuser = request.user.username
        if not vncuser:
            error_msg = "用户名不存在，请联系管理员！"
            logger.error(error_msg)
            return self.error(error_msg)
        data = request.data
        App_id = data.get("app_id")
        # 查询APP信息
        if not App_id:
            error_msg = "APP不存在，请联系管理员！"
            logger.error(error_msg)
            return self.error(error_msg)
        try:
            AppInfo = AppManager.objects.get(id=App_id)
        except AppInfo.DoesNotExist:
            error_msg = "AppManager id = {} does not exists".format(App_id)
            logger.error(error_msg)
            return self.error(error_msg)
        # 根据软件选择启动脚本
        vncserver_script_path = settings.VNCSERVER_SCRIPT_PATH
        run_bash_name = "run_{}.sh".format(AppInfo.full_name)
        start_script = os.path.join(vncserver_script_path, run_bash_name)
        start_software = AppInfo.full_name

        # 以登录用户的账号启动远程桌面并返回url和otp密码
        username = "caep_" + vncuser
        if request.data.get("display_number"):
            display_number = request.data.get("display_number")
        else:
            fields = ("display_number", "id")
            vnc_sessions_info = VNCSession.objects.all().values_list(*fields)
            display_number = next_display_number(vnc_sessions_info)

        # 启动 VNC 会话
        pramas = {
            "username": username,
            "display_number": display_number,
            "custom_script_path": start_script,
        }
        try:
            data = start_vnc_session(pramas)
            if msg := data.get("msg"):
                logger.error(msg)
                return self.error("VNC session 服务启动失败！")
        except Exception as e:
            return self.error(str(e))
        vnc_session_info = data.get("vnc_session_info")
        server_ip = SysOptions.server_ip
        session_id = vnc_session_info.get("session_id")
        vnc_otp = vnc_session_info.get("otp_value")
        novnc_url = vnc_session_info.get("novnc_url")
        host_port_match = re.search(r"host=([^&]+)&port=(\d+)", novnc_url)
        hostname = host_port_match.group(1)
        novnc_url = novnc_url.replace(hostname, server_ip)
        no_vnc_url = novnc_url + "&resize=scale"

        server_exists = VNCSession.objects.all().filter(display_number=display_number)
        if server_exists:
            VNCSession.objects.filter(display_number=display_number).delete()
        with transaction.atomic():
            VNCSession.objects.create(
                session_id=session_id,
                display_number=display_number,
                run_software=start_software,
                novnc_url=no_vnc_url,
                server_starter=request.user,
            )
        print(
            " Started a new VNCSession Display. Display number is : {} ".format(
                display_number
            )
        )
        vnc_info = {
            "display_number": int(display_number),
            "vnc_otp": vnc_otp,
            "vnc_url": no_vnc_url,
        }
        return self.success(vnc_info)

    def delete(self, request):
        display_number = int(request.GET.get("display_number"))
        if not display_number:
            error_msg = "Invalid parameter, display_number is required"
            logger.error(error_msg)
            return self.error(error_msg)
        try:
            vnc_session = VNCSession.objects.get(display_number=display_number)
        except VNCSession.DoesNotExist:
            error_msg = " Display_number id = {} does not exists".format(display_number)
            logger.error(error_msg)
            return self.error(error_msg)
        session_id = vnc_session.session_id
        try:
            close_session(session_id)
        except Exception as e:
            return self.error(str(e))
        with transaction.atomic():
            vnc_session.delete()
            print(" Closed VNC Session, Display number is {}".format(display_number))
            return self.success()


class VncServerOTPManager(APIView):
    """VNC Session OTP 管理类"""

    def get(self, request):
        # 更新 vnc session 访问的一次性密码
        display_number = int(request.GET.get("display_number"))
        if not display_number:
            error_msg = "Invalid parameter, display_number is required"
            logger.error(error_msg)
            return self.error(error_msg)
        try:
            vnc_session = VNCSession.objects.get(display_number=display_number)
        except VNCSession.DoesNotExist:
            error_msg = " Display_number id = {} does not exists".format(display_number)
            logger.error(error_msg)
            return self.error(error_msg)
        session_id = vnc_session.session_id
        try:
            data = update_otp(session_id)
            if msg := data.get("msg"):
                logger.error(msg)
                return self.error("server_error")
        except Exception as e:
            return self.error(str(e))
        new_otp_value = data.get("otp_value")
        vnc_info = {"display_number": display_number, "vnc_otp": new_otp_value}
        return self.success(vnc_info)


class AppConfigList(APIView):
    """获取App软件列表，按修改时间排序"""

    def get(self, request):
        App_manager_list_info = AppManager.objects.order_by("name").filter(visible=True).distinct("name")

        # 分页
        data = self.paginate_data(
            request, App_manager_list_info, AppManagerNameSerializer
        )

        return self.success(data)


class AppNameId(APIView):
    """获取App名称的id列表，按修改时间排序"""

    def get(self, request):
        data = request.data
        app_name = data.get("name")
        try:
            name_id_list_info = AppManager.objects.filter(name=app_name).filter(visible=True)
        except name_id_list_info.DoesNotExist:
            error_msg = "AppVersion does not exists"
            logger.error(error_msg)
            return self.error(error_msg)

        # 分页
        data = self.paginate_data(
            request, name_id_list_info, AppManagerNameIdSerializer
        )

        return self.success(data)


class GetUserManual(APIView):
    """获取APP用户手册url"""

    def post(self, request):
        App_id = request.data.get("id")
        if not App_id:
            error_msg = "APP不存在，请联系管理员！"
            logger.error(error_msg)
            return self.error(error_msg)
        try:
            AppInfo = AppManager.objects.get(id=App_id)
        except AppManager.DoesNotExist:
            error_msg = " AppManager id = {} does not exists".format(App_id)
            logger.error(error_msg)
            return self.error(error_msg)

        manual_file_id = request.data.get("manual_file_id")
        manual_name = request.data.get("name")

        manual_url = (
                "/public/novncfiles/manualfiles/" + str(manual_file_id) + "/" + manual_name
        )

        return self.success({"manual_url": manual_url})
