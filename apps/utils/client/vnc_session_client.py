import logging
from itertools import cycle
from django.conf import settings
from vnc_session_client import VncApi, ApiClient, Configuration

logger = logging.getLogger(__name__)

# 从配置中获取多个 VNC session 服务节点
VNC_SESSION_MANAGER_URLS = settings.VNC_SESSION_MANAGER_URLS

# 创建配置循环器（用于轮询）
_configs = [Configuration(host=url) for url in VNC_SESSION_MANAGER_URLS]
_config_cycle = cycle(_configs)


def get_round_robin_config():
    """轮询选择下一个配置"""
    from apps.vncserver.models import VNCSession
    
    max_desktops_per_node = 8
    total_nodes = len(_configs)
    attempts = 0
    
    while attempts < total_nodes:
        config = next(_config_cycle)
        node_url = config.host
        
        # 查询该节点上已创建的桌面数量
        desktop_count = VNCSession.objects.filter(node_url=node_url).count()
        
        if desktop_count < max_desktops_per_node:
            # 该节点还有容量，返回此配置
            logger.debug(f"Selected node {node_url} with {desktop_count}/{max_desktops_per_node} desktops")
            return config
        
        # 该节点已满，跳过
        logger.debug(f"Skipping node {node_url} - full ({desktop_count}/{max_desktops_per_node} desktops)")
        attempts += 1
    
    # 所有节点都已满
    msg = f"All {total_nodes} VNC session manager nodes are full (max {max_desktops_per_node} desktops each)"
    logger.error(msg)
    raise Exception(msg)


def start_vnc_session(params: dict):
    config = get_round_robin_config()
    with ApiClient(config) as api_client:
        vnc_server_api = VncApi(api_client)
        try:
            response = vnc_server_api.start_session(params)
            data = response.get("data")
            # 添加创建session的节点URL到返回数据中
            if data:
                data["node_url"] = config.host
            return data
        except Exception:
            msg = f"调用VNC session管理服务[{config.host}]出现异常，请确认服务是否启动！"
            logger.error(msg)
            raise Exception(msg)



def update_otp(session_id):
    from apps.vncserver.models import VNCSession
    try:
        vnc_session = VNCSession.objects.get(session_id=session_id)
        node_url = vnc_session.node_url
        config = Configuration(host=node_url)
    except VNCSession.DoesNotExist:
        msg = f"未找到session_id={session_id}对应的VNC会话记录！"
        logger.error(msg)
        raise Exception(msg)
    
    with ApiClient(config) as api_client:
        vnc_server_api = VncApi(api_client)
        try:
            response = vnc_server_api.update_otp(session_id)
            return response.get("data")
        except Exception:
            msg = f"调用VNC session管理服务[{config.host}]出现异常！"
            logger.error(msg)
            raise Exception(msg)


def close_session(session_id):
    """关闭 session，需要保持与创建 session 时相同的节点"""
    from apps.vncserver.models import VNCSession
    try:
        vnc_session = VNCSession.objects.get(session_id=session_id)
        node_url = vnc_session.node_url
        config = Configuration(host=node_url)
    except VNCSession.DoesNotExist:
        msg = f"未找到session_id={session_id}对应的VNC会话记录！"
        logger.error(msg)
        raise Exception(msg)
    
    with ApiClient(config) as api_client:
        vnc_server_api = VncApi(api_client)
        try:
            vnc_server_api.close_session(session_id)
        except Exception as e:
            msg = f"调用VNC session管理服务[{config.host}]出现异常！"
            logger.error(msg)
            raise Exception(msg)