#!/usr/bin/env python
# coding: utf-8

from apps.account.models import User
from apps.utils.api import JSONResponse
from django.conf import settings
from django.db import connection
from django.utils.deprecation import MiddlewareMixin
from django.utils.timezone import now


class SessionRecordMiddleware(MiddlewareMixin):
    """记录用户登录的相关信息，例如浏览器、ip 等"""

    def process_request(self, request):
        request.ip = request.META.get(
            settings.IP_HEADER, request.META.get("REMOTE_ADDR")
        )  # noqa
        if request.user.is_authenticated:
            session = request.session
            # 从 session 中获取相关的信息，以便展示在 dashboard 中
            session["user_agent"] = request.META.get("HTTP_USER_AGENT", "")
            session["ip"] = request.ip
            session["last_activity"] = now()
            user_sessions = request.user.session_keys
            if session.session_key not in user_sessions:
                user_sessions.append(session.session_key)
                request.user.save()


class AdminRoleRequiredMiddleware(MiddlewareMixin):
    """定义哪些页面需要管理员身份才能进入"""

    def process_request(self, request):
        path = request.path_info
        # 下列页面必须由管理员类别的人才能进入，否则必须登录
        if path.startswith("/admin/") or path.startswith("/api/admin/"):
            if not (request.user.is_authenticated and request.user.is_admin_role()):
                return JSONResponse.response(
                    {"error": "login-required", "data": "Please login in first"}
                )


class LogSqlMiddleware(MiddlewareMixin):
    """对执行的 sql 语句做记录"""

    def process_response(self, request, response):
        # 对终端的输出进行染色
        print("\033[94m", "#" * 30, "\033[0m")
        # 对查询时间做个设定
        time_threshold = 0.03
        for query in connection.queries:
            if float(query["time"]) > time_threshold:
                print("\033[93m", query, "\n", "-" * 30, "\033[0m")
            else:
                print(query, "\n", "-" * 30)
        return response
