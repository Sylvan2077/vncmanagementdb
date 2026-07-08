import logging

from django.conf import settings

from vnc_session_client import VncApi, ApiClient, Configuration

logger = logging.getLogger(__name__)

service_config = Configuration(host=(settings.VNC_SESSION_MANAGER_URL))


def start_vnc_session(pramas):
    with ApiClient(service_config) as api_client:
        vnc_server_api = VncApi(api_client)
        try:
            response = vnc_server_api.start_session(pramas)
            return response.get("data")
        except Exception:
            msg = "调用VNC session管理服务[启动vnc session]出现异常，请确认服务是否启动！"
            logger.error(msg)
            raise Exception(msg)


def update_otp(session_id):
    with ApiClient(service_config) as api_client:
        vnc_server_api = VncApi(api_client)
        try:
            response = vnc_server_api.update_otp(session_id)
            return response.get("data")
        except Exception:
            msg = "调用VNC session管理服务[更新 otp]出现异常，请确认服务是否启动！"
            logger.error(msg)
            raise Exception(msg)


def close_session(session_id):
    with ApiClient(service_config) as api_client:
        vnc_server_api = VncApi(api_client)
        try:
            vnc_server_api.close_session(session_id)
        except Exception as e:
            msg = "调用VNC session管理服务[关闭vnc session]出现异常，请确认服务是否启动！"
            logger.error(msg)
            raise Exception(msg)
