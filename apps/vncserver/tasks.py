#!/usr/bin/env python
# coding: utf-8

import logging
import os
import re

from celery import shared_task
from django.conf import settings
from django.db import transaction

from apps.conf.options import SysOptions
from apps.utils.client.vnc_session_client import (
    start_vnc_session,
    update_otp,
    close_session,
)
from django.contrib.auth import get_user_model
from apps.vncserver.models import VNCSession, AppManager

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


@shared_task(bind=True, max_retries=3, default_retry_delay=10, name='vnc.create_session')
def create_vnc_session(self, username, app_id, user_id=None, display_number=None):
    """异步创建 VNC 会话"""
    try:
        AppInfo = AppManager.objects.get(id=app_id)
    except AppInfo.DoesNotExist:
        logger.error(f"AppManager id = {app_id} does not exists")
        raise

    # 获取用户对象
    User = get_user_model()
    server_starter = None
    if user_id:
        try:
            server_starter = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.warning(f"User id = {user_id} does not exists")

    vncserver_script_path = settings.VNCSERVER_SCRIPT_PATH
    run_bash_name = "run_{}.sh".format(AppInfo.full_name)
    start_script = os.path.join(vncserver_script_path, run_bash_name)
    start_software = AppInfo.full_name

    if not display_number:
        fields = ("display_number", "id")
        vnc_sessions_info = VNCSession.objects.all().values_list(*fields)
        display_number = next_display_number(vnc_sessions_info)

    params = {
        "username": username,
        "display_number": display_number,
        "custom_script_path": start_script,
    }

    try:
        data = start_vnc_session(params)
        if msg := data.get("msg"):
            logger.error(msg)
            raise Exception("VNC session 服务启动失败！")
    except Exception as e:
        logger.error(f"Failed to create VNC session: {str(e)}")
        raise

    vnc_session_info = data.get("vnc_session_info")
    server_ip = SysOptions.server_ip
    session_id = vnc_session_info.get("session_id")
    node_url = data.get("node_url")

    #拼接节点Ip和vnc端口，端口根据display_number，vnc端口=display_number+5900
    vnc_port = display_number + 5900
    token_file_content = f"{node_url}:{vnc_port}"

    # 根据session_id在novnc的target目录创建token文件
    token_file_path = os.path.join(settings.NOVNC_TARGET_PATH, session_id)
    with open(token_file_path, "w") as f:
        f.write(token_file_content)
    
    vnc_otp = vnc_session_info.get("otp_value")
    novnc_url = vnc_session_info.get("novnc_url")

    # TODO: 不在使用该NoVNC URL拼接方式，改为直接使用session_id拼接websokify_url
    host_port_match = re.search(r"host=([^&]+)&port=(\d+)", novnc_url)
    hostname = host_port_match.group(1)
    novnc_url = novnc_url.replace(hostname, server_ip)
    no_vnc_url = novnc_url + "&resize=scale"

    # 拼接websokify_url，格式为localhost:5801/vnc.html?path=?token=session_id
    no_vnc_url = f"{server_ip}:5801/vnc.html?path=?token={session_id}"

    server_exists = VNCSession.objects.all().filter(display_number=display_number)
    if server_exists:
        VNCSession.objects.filter(display_number=display_number).delete()

    with transaction.atomic():
        VNCSession.objects.create(
            session_id=session_id,
            node_url=node_url,
            display_number=display_number,
            run_software=start_software,
            novnc_url=no_vnc_url,
            server_starter=server_starter,
        )

    logger.info(f"Started a new VNCSession Display. Display number is: {display_number}")
    return {
        "display_number": display_number,
        "novnc_url": no_vnc_url,
        "session_id": session_id,
        "vnc_otp": vnc_otp,
    }


@shared_task(bind=True, max_retries=2, name='vnc.close_session')
def close_vnc_session(self, session_id):
    """异步关闭 VNC 会话"""
    try:
        close_session(session_id)
        logger.info(f"Closed VNC session: {session_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to close VNC session {session_id}: {str(e)}")
        raise


@shared_task(bind=True, max_retries=2, default_retry_delay=5, name='vnc.update_otp')
def update_vnc_otp(self, session_id):
    """异步更新 VNC OTP"""
    try:
        data = update_otp(session_id)
        if msg := data.get("msg"):
            logger.error(msg)
            raise Exception("Failed to update OTP")
        return data.get("otp_value")
    except Exception as e:
        logger.error(f"Failed to update OTP for session {session_id}: {str(e)}")
        raise