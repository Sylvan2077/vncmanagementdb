import logging

import user_management

from apps.novncdb import settings

logger = logging.getLogger(__name__)
configuration = user_management.Configuration(settings.USER_MANAGEMENT_HOST)


def login(server_data):
    """
    测试管理员帐号信息
    """

    with user_management.ApiClient(configuration) as api_client:
        api_instance = user_management.UserManagerApi(api_client)
        try:
            # 测试管理员帐号信息
            response = api_instance.try_login(server_data)
            if response.data:
                msg = response.data.get("msg")
                return msg
        except Exception as e:
            msg = "错误：调用用户管理服务[测试管理员帐号信息]出现异常，请确认服务是否启动！"
            logger.error("{}  错误信息: {}".format(msg, e))
            return msg


def register(form_data):
    """
    注册用户
    """

    with user_management.ApiClient(configuration) as api_client:
        api_instance = user_management.UserManagerApi(api_client)
        try:
            # 注册用户
            response = api_instance.register(form_data)
            if response.data:
                msg = response.data.get("msg")
                return msg
        except Exception as e:
            msg = "错误：调用用户管理服务[注册用户]出现异常，请确认服务是否启动！"
            logger.error("{}  错误信息: {}".format(msg, e))
            return msg


def modify(form_data):
    """
    修改用户信息
    """

    with user_management.ApiClient(configuration) as api_client:
        api_instance = user_management.UserManagerApi(api_client)

        try:
            # 修改用户信息
            response = api_instance.modify_user_info(form_data)
            if response.data:
                msg = response.data.get("msg")
                return msg
        except Exception as e:
            msg = "错误：调用用户管理服务[修改用户信息]出现异常，请确认服务是否启动！"
            logger.error("{}  错误信息: {}".format(msg, e))
            return msg


def change_passwd(form_data):
    """
    用户修改密码
    """

    with user_management.ApiClient(configuration) as api_client:
        api_instance = user_management.UserManagerApi(api_client)
        try:
            # 用户修改密码
            response = api_instance.user_change_passwd(form_data)
            if response.data:
                msg = response.data.get("msg")
                return msg
        except Exception as e:
            msg = "错误：调用用户管理服务[修改用户密码]出现异常，请确认服务是否启动！"
            logger.error("{}  错误信息: {}".format(msg, e))
            return msg


def delete(form_data):
    """
    删除用户
    """

    with user_management.ApiClient(configuration) as api_client:
        api_instance = user_management.UserManagerApi(api_client)
        try:
            # 删除用户
            response = api_instance.delete_user(form_data)
            return response.data
        except Exception as e:
            msg = "错误：调用用户管理服务[删除用户]出现异常，请确认服务是否启动！"
            logger.error("{}  错误信息: {}".format(msg, e))
            data = {"msg": msg, "data": []}
            return data


def update(form_data):
    """
    同步用户
    """

    with user_management.ApiClient(configuration) as api_client:
        api_instance = user_management.UserManagerApi(api_client)
        try:
            # 同步用户
            response = api_instance.update_user(form_data)
            return response.data
        except Exception as e:
            msg = "错误：调用用户管理服务[同步用户]出现异常，请确认服务是否启动！"
            logger.error("{}  错误信息: {}".format(msg, e))
            data = {"msg": msg, "data": []}
            return data
