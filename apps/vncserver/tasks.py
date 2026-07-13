#!/usr/bin/env python
# coding: utf-8

import logging
import os
import re

from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.contrib.auth import get_user_model

from apps.conf.options import SysOptions
from apps.utils.client.vnc_session_client import (
    start_vnc_session,
    update_otp,
    close_session,
)
from apps.vncserver.models import VNCSession, AppManager

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=10, name='vnc.start_vnc_session_async')
def start_vnc_session_async(self, username, display_number, custom_script_path, user_id=None):
    """
    异步调用 start_vnc_session 并处理结果
    
    参数：
    - username: VNC用户名
    - display_number: 显示编号
    - custom_script_path: 启动脚本路径
    - user_id: 用户ID（可选）
    """
    logger.info(f"Async task started: start_vnc_session_async with username={username}, display_number={display_number}")
    
    params = {
        "username": username,
        "display_number": display_number,
        "custom_script_path": custom_script_path,
    }

    try:
        data = start_vnc_session(params)
        if msg := data.get("msg"):
            logger.error(msg)
            return {"success": False, "error": msg}
    except Exception as e:
        logger.error(f"Failed to start VNC session: {str(e)}")
        return {"success": False, "error": str(e)}

    vnc_session_info = data.get("vnc_session_info")
    server_ip = SysOptions.server_ip
    session_id = vnc_session_info.get("session_id")
    vnc_otp = vnc_session_info.get("otp_value")
    novnc_url = vnc_session_info.get("novnc_url")
    node_url = data.get("node_url")
    # 提取node_url中的ip
    node_ip = re.search(r"host=([^&]+)", node_url).group(1)

    # 根据display_number拼接5900 + display_number
    port = 5900 + display_number

    # 根据session_id在NOVNC_TARGET_PATH目录下创建一个以session_id命名的token文件，内容为node_ip:port
    token_file_path = os.path.join(settings.NOVNC_TARGET_PATH, f"{session_id}")
    with open(token_file_path, "w") as f:
        f.write(f"{node_ip}:{port}")

    host_port_match = re.search(r"host=([^&]+)&port=(\d+)", novnc_url)
    hostname = host_port_match.group(1)
    novnc_url = novnc_url.replace(hostname, server_ip)
    no_vnc_url = novnc_url + "&resize=scale"

    # 获取用户对象
    User = get_user_model()
    server_starter = None
    if user_id:
        try:
            server_starter = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.warning(f"User id = {user_id} does not exists")

    # 获取软件名称
    run_software = os.path.basename(custom_script_path).replace("run_", "").replace(".sh", "")

    # 保存到数据库
    try:
        server_exists = VNCSession.objects.all().filter(display_number=display_number)
        if server_exists:
            VNCSession.objects.filter(display_number=display_number).delete()

        with transaction.atomic():
            VNCSession.objects.create(
                session_id=session_id,
                node_url=node_url,
                display_number=display_number,
                run_software=run_software,
                novnc_url=no_vnc_url,
                server_starter=server_starter,
            )

        logger.info(f"VNC session created successfully. Display number: {display_number}")
        
        return {
            "success": True,
            "display_number": display_number,
            "novnc_url": no_vnc_url,
            "session_id": session_id,
            "vnc_otp": vnc_otp,
            "node_url": node_url,
        }
    except Exception as e:
        logger.error(f"Failed to save VNC session to database: {str(e)}")
        return {"success": False, "error": str(e)}


@shared_task(bind=True, max_retries=2, name='vnc.close_session')
def close_vnc_session(self, session_id):
    """异步关闭 VNC 会话"""
    try:
        close_session(session_id)
        logger.info(f"Closed VNC session: {session_id}")
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to close VNC session {session_id}: {str(e)}")
        return {"success": False, "error": str(e)}


@shared_task(bind=True, max_retries=2, default_retry_delay=5, name='vnc.update_otp')
def update_vnc_otp(self, session_id):
    """异步更新 VNC OTP"""
    try:
        data = update_otp(session_id)
        if msg := data.get("msg"):
            logger.error(msg)
            return {"success": False, "error": msg}
        return {"success": True, "otp_value": data.get("otp_value")}
    except Exception as e:
        logger.error(f"Failed to update OTP for session {session_id}: {str(e)}")
        return {"success": False, "error": str(e)}