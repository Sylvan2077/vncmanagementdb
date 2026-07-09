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
from apps.vncserver.tasks import (
    create_vnc_session,
    close_vnc_session,
    update_vnc_otp,
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
        """异步创建 VNC 会话"""
        vncuser = request.user.username
        if not vncuser:
            error_msg = "用户名不存在，请联系管理员！"
            logger.error(error_msg)
            return self.error(error_msg)
        data = request.data
        App_id = data.get("app_id")
        if not App_id:
            error_msg = "APP不存在，请联系管理员！"
            logger.error(error_msg)
            return self.error(error_msg)
        
        username = "caep_" + vncuser
        display_number = request.data.get("display_number")
        user_id = request.user.id
        
        # 异步调用创建 session 的任务
        task = create_vnc_session.delay(username, App_id, user_id, display_number)
        
        return self.success({
            "task_id": task.id,
            "message": "VNC session 创建任务已提交",
            "display_number": display_number
        })

    def delete(self, request):
        """异步关闭 VNC 会话"""
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
        
        # 异步调用关闭 session 的任务
        task = close_vnc_session.delay(session_id)
        
        # 异步删除数据库记录
        with transaction.atomic():
            vnc_session.delete()
        
        return self.success({
            "task_id": task.id,
            "message": "VNC session 关闭任务已提交",
            "display_number": display_number
        })


class VncServerOTPManager(APIView):
    """VNC Session OTP 管理类"""

    def get(self, request):
        """异步更新 VNC session OTP"""
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
        
        # 异步调用更新 OTP 的任务
        task = update_vnc_otp.delay(session_id)
        
        return self.success({
            "task_id": task.id,
            "message": "OTP 更新任务已提交",
            "display_number": display_number
        })


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