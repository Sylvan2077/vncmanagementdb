import logging
import threading
import time
from vnc_session_client import VncApi, ApiClient, Configuration

logger = logging.getLogger(__name__)

_round_robin_lock = threading.Lock()
_round_robin_index = 0

_urls_cache = None
_urls_cache_time = 0
_URLS_CACHE_TTL = 60


def get_vnc_session_manager_urls():
    """从数据库获取所有启用的 VNC Session Manager 节点 URL（带缓存）"""
    global _urls_cache, _urls_cache_time
    now = time.time()
    if _urls_cache is not None and (now - _urls_cache_time) < _URLS_CACHE_TTL:
        return _urls_cache
    from apps.vncserver.models import VncUrl
    vnc_urls = list(VncUrl.objects.filter(is_enabled=True).order_by('id'))
    _urls_cache = [v.url for v in vnc_urls]
    _urls_cache_time = now
    return _urls_cache


def invalidate_urls_cache():
    """手动失效URL缓存"""
    global _urls_cache, _urls_cache_time
    _urls_cache = None
    _urls_cache_time = 0


def get_round_robin_config(app_id=None):
    """轮询选择下一个配置（线程安全），可按APP授权过滤"""
    global _round_robin_index

    vnc_urls = get_vnc_session_manager_urls()
    if not vnc_urls:
        msg = "没有可用的 VNC session manager 节点，请在数据库中配置节点信息"
        logger.error(msg)
        raise Exception(msg)

    if app_id is not None:
        from apps.vncserver.models import NodeAppAuth, VncUrl
        authorized_ids = list(
            NodeAppAuth.objects.filter(
                app_id=app_id, is_enabled=True, vnc_url__is_enabled=True
            ).values_list("vnc_url_id", flat=True)
        )
        authorized_urls = list(
            VncUrl.objects.filter(id__in=authorized_ids).order_by("id").values_list("url", flat=True)
        )
        configs = [Configuration(host=url) for url in authorized_urls]
        if not configs:
            from apps.vncserver.models import AppManager
            try:
                app_obj = AppManager.objects.get(id=app_id)
                app_name = app_obj.full_name
            except AppManager.DoesNotExist:
                app_name = str(app_id)
            msg = f"APP [{app_name}] 未授权任何节点，无法启动桌面"
            logger.error(msg)
            raise Exception(msg)
    else:
        configs = [Configuration(host=url) for url in vnc_urls]

    total_nodes = len(configs)
    max_desktops_per_node = 8

    with _round_robin_lock:
        start_index = _round_robin_index % total_nodes
        _round_robin_index = (_round_robin_index + 1) % total_nodes

    from apps.vncserver.models import VNCSession

    for offset in range(total_nodes):
        idx = (start_index + offset) % total_nodes
        config = configs[idx]
        node_url = config.host

        desktop_count = VNCSession.objects.filter(node_url=node_url).count()

        if desktop_count < max_desktops_per_node:
            logger.debug(f"Selected node {node_url} with {desktop_count}/{max_desktops_per_node} desktops")
            return config

        logger.debug(f"Skipping node {node_url} - full ({desktop_count}/{max_desktops_per_node} desktops)")

    msg = f"All {total_nodes} VNC session manager nodes are full (max {max_desktops_per_node} desktops each)"
    logger.error(msg)
    raise Exception(msg)


def start_vnc_session(params: dict, app_id=None):
    config = get_round_robin_config(app_id=app_id)
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