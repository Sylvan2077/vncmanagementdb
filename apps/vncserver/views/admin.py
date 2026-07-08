#!/usr/bin/env python
# coding: utf-8

import datetime
import json
import logging
import os
import shutil
import subprocess
from threading import Thread

from django.conf import settings
from django.db import transaction
from django.http import JsonResponse

from apps.account.decorators import manager_admin_required
from apps.account.models import AdminType
from apps.utils.api import APIView
from apps.utils.api.api import CSRFExemptAPIView, validate_serializer
from apps.utils.client.vnc_session_client import update_otp, close_session
from apps.utils.shortcuts import rand_str, process_uploadFiles, next_caseID
from apps.vncserver.models import VNCSession, AppManager
from apps.vncserver.serializers import (
    VncSessionListSerializer,
    AppManagerListSerializer,
    CreateAppManagerSerializer,
)

logger = logging.getLogger(__name__)


class VncServerManagement(APIView):
    """VNC Server Manager"""

    @manager_admin_required
    def get(self, request):
        """查询启动的vncserver的信息"""
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
        vncservers = all_vncservers.order_by("add_time")
        data = self.paginate_data(request, vncservers, VncSessionListSerializer)
        return self.success(data)

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


class VncServerOTPGenerater(APIView):
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


def generate_app_startup_script(install_path, bin_path, app_name):
    """构造App启动脚本"""

    execute_path = os.path.dirname(os.path.dirname(__file__))
    templates_path = os.path.join(execute_path, "templates")
    run_bash_tmp_path = os.path.join(templates_path, "app_run_tmp.sh")
    vncserver_script_path = settings.VNCSERVER_SCRIPT_PATH
    openbox_dir = settings.OPENBOX_DIR
    virtualgl_dir = settings.VIRTUALGL_DIR
    error_msg = ""
    if not os.path.exists(vncserver_script_path):
        os.mkdir(vncserver_script_path)
    # 读取App运行脚本模板
    with open(run_bash_tmp_path, "r", encoding="utf-8") as f:
        bash_data = f.read()
    # 可执行文件路径
    executable_file_path = install_path + "/" + bin_path
    # 删除可执行文件路径中多余的"/"号
    while executable_file_path.find("//") != -1:
        executable_file_path = executable_file_path.replace("//", "/")
    # 构造脚本内容
    bash_data = (
        bash_data.replace("OD", openbox_dir)
        .replace("VD", virtualgl_dir)
        .replace("BP", executable_file_path)
    )
    # 写入App运行脚本
    run_bash_name = "run_" + app_name + ".sh"
    run_bash_path = os.path.join(vncserver_script_path, run_bash_name)
    with open(run_bash_path, "w", encoding="utf-8") as f:
        for line in bash_data:
            f.write(line)
    add_execute_permission_cmd = "chmod +x {}".format(run_bash_path)
    p = subprocess.Popen(
        add_execute_permission_cmd,
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return error_msg


def decrypt_App(auth_code, app_package):
    """GPG解密APP压缩包"""
    pkg_file_id = app_package.get("pkg_file_id")
    app_name = app_package.get("info")[0].get("name")
    App_pkg_path = os.path.join(settings.PKG_DIR, pkg_file_id)
    app_real_path = os.path.join(App_pkg_path, app_name)
    error_msg = ""
    if auth_code:
        decrypt_pkg_path = app_real_path.split(".gpg")[0]
        decrypt_app = "/bin/sh -c 'gpg --batch --passphrase {} -o {} -d {}'".format(
            auth_code, decrypt_pkg_path, app_real_path
        )
        return_code = subprocess.call(decrypt_app, shell=True)
        if return_code:
            error_msg = "安装包解密错误！"
            logger.error(error_msg)
        return decrypt_pkg_path, error_msg
    else:
        return app_real_path, error_msg


def run_task(f, *args, **kwargs):
    t = Thread(target=f, args=args, kwargs=kwargs)
    t.start()


def install_App(auth_code, app_package, install_path, new_app_id):
    """执行APP安装"""
    pkg_path, error_msg = decrypt_App(auth_code, app_package)
    install_log_id = rand_str()
    install_log_path = os.path.join(settings.INSTALL_LOG_DIR, install_log_id)
    os.makedirs(install_log_path, exist_ok=True)
    logFile = os.path.join(install_log_path, "install_log.log")
    install_log_name = install_log_id + "/install_log.log"
    # 是否解密成功
    if error_msg == "":
        install_new_app = "bash {} -bfp {} >> {} 2>&1".format(
            pkg_path, install_path, logFile
        )
        # install_new_app = "/bin/sh {} > {} 2>&1".format(pkg_path, logFile)
        return_code = subprocess.call(install_new_app, shell=True)
        if return_code:
            install_status = 2
        else:
            install_status = 3
    else:
        with open(logFile, "w", encoding="utf-8") as f:
            f.write(error_msg)
        install_status = 2

    # 安装完成后修改APP安装状态和安装日志ID
    AppInfo = AppManager.objects.get(id=new_app_id)
    if os.path.exists(AppInfo.complete_path):
        complete_path = AppInfo.complete_path
        bin_path = AppInfo.bin_path
        install_status = 4
    else:
        complete_path = ""
        bin_path = ""
        install_status = 3
    editData = {"install_status": install_status, "install_log": install_log_name}
    with transaction.atomic():
        for k, v in editData.items():
            setattr(AppInfo, k, v)
        AppInfo.bin_path = bin_path
        AppInfo.complete_path = complete_path
        AppInfo.change_time = datetime.datetime.today()
        AppInfo.save()


class AppManagerConfig(APIView):
    """App管理配置"""

    def get(self, request):
        pass

    @manager_admin_required
    @validate_serializer(CreateAppManagerSerializer)
    def post(self, request):
        """录入App配置信息"""
        data = request.data
        install_path = data.get("install_path")
        auth_code = data.get("auth_code")
        app_version = data.get("version")
        app_name = data.get("name")
        full_name = app_name + '-' + app_version
        if not auth_code:
            auth_code = ""

        fields = ("id", "full_name")
        # 筛选id-val
        internal_APP_fields = AppManager.objects.all().values_list(*fields)
        # 取消id自增
        new_app_id = next_caseID(internal_APP_fields)

        # 获取已有app名称-版本列表
        if len(list(zip(*internal_APP_fields))) > 0:
            app_names = list(zip(*internal_APP_fields))[1]
        else:
            app_names = []
        if full_name in app_names:
            error_msg = "APP 名称及版本: {} 已存在，请修改后保存！".format(full_name)
            logger.error(error_msg)
            return self.error(error_msg)

        app_package = data.get("app_package")
        if app_package.get("pkg_file_id"):
            if os.path.exists(install_path):
                error_msg = " APP安装路径: {} 已经存在，可点击添加APP！".format(install_path)
                logger.error(error_msg)
                return self.error(error_msg)
            install_status = 1
        else:
            if not os.path.exists(install_path):
                error_msg = " APP安装路径: {} 不存在，请安装后添加APP！".format(install_path)
                logger.error(error_msg)
                return self.error(error_msg)
            install_status = 3

        # 存入数据库
        with transaction.atomic():
            AppManager.objects.create(
                id=new_app_id,
                version=app_version,
                name=app_name,
                full_name=full_name,
                install_path=install_path,
                install_status=install_status,
                app_package=app_package,
                auth_code=auth_code,
                visible=data.get("visible"),
                App_creator=request.user,
            )

        # 异步执行安装函数
        if app_package.get("pkg_file_id"):
            run_task(
                install_App,
                auth_code=auth_code,
                app_package=app_package,
                install_path=install_path,
                new_app_id=new_app_id,
            )

        return self.success()

    def patch(self, request):
        """对App做局部修改"""

        data = request.data
        App_id = data.get("id")
        app_version = data.get("version")
        app_name = data.get("name")
        full_name = app_name + '-' + app_version

        # 检查app信息是否存在
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

        # 检查已存在的app名称
        exists_name = AppManager.objects.values_list("full_name", flat=True).exclude(
            id=App_id
        )
        if full_name in exists_name:
            error_msg = "APP 名称版本: {} 已存在，请修改后保存！".format(full_name)
            logger.error(error_msg)
            return self.error(error_msg)

        # 检查App安装路径是否修改，如果修改则重新生成启动脚本
        install_path = data.get("install_path")
        bin_path = data.get("bin_path")
        complete_path = install_path + "/" + bin_path
        old_app_name = AppInfo.full_name
        if isinstance(bin_path, list):
            bin_path = "/".join(bin_path)
        # 是否修改了APP名称
        if old_app_name != full_name:
            # 是否修改了二进制路径
            if bin_path != AppInfo.bin_path:
                # 构造App启动脚本
                error_msg = generate_app_startup_script(
                    install_path, bin_path, full_name
                )
                if error_msg:
                    return self.error(error_msg)
            elif bin_path != "":
                # 将原启动脚本以新app名称命名
                vncserver_script_path = settings.VNCSERVER_SCRIPT_PATH
                error_msg = ""
                if not vncserver_script_path:
                    error_msg = " APP启动脚本路径不存在，请先确认系统配置是否完成！"
                    logger.error(error_msg)
                    return self.error(error_msg)
                new_app_run_script_path = os.path.join(
                    vncserver_script_path, "run_{}.sh".format(full_name)
                )
                old_app_run_script_path = os.path.join(
                    vncserver_script_path, "run_{}.sh".format(old_app_name)
                )
                os.rename(old_app_run_script_path, new_app_run_script_path)
        # 没有修改app名称
        else:
            if bin_path != AppInfo.bin_path:
                # 构造App启动脚本
                error_msg = generate_app_startup_script(
                    install_path, bin_path, full_name
                )
                if error_msg:
                    return self.error(error_msg)
        # 首先复制需要修改的内容，然后执行修改
        editData = {}
        for attr in ["name", "version", "user_manual", "install_path", "complete_path", "visible"]:
            if data.get(attr) is not None:
                editData[attr] = data.get(attr)

        with transaction.atomic():
            for k, v in editData.items():
                setattr(AppInfo, k, v)
            AppInfo.install_status = 4
            AppInfo.bin_path = bin_path
            AppInfo.complete_path = complete_path
            AppInfo.change_time = datetime.datetime.today()
            AppInfo.full_name = full_name
            AppInfo.save()
            print(" Patch AppManager id = {}".format(AppInfo.id))
            return self.success()

    def delete(self, request):
        """删除App"""

        App_id = request.GET.get("id")
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
        # 删除运行脚本
        vncserver_script_path = settings.VNCSERVER_SCRIPT_PATH
        error_msg = ""
        if vncserver_script_path:
            run_bash_path = os.path.join(
                vncserver_script_path, "run_{}.sh".format(AppInfo.name)
            )
            if os.path.exists(run_bash_path):
                os.remove(run_bash_path)
        # 删除用户手册
        user_manual_info = AppInfo.user_manual
        if user_manual_info.get("manaul_file_id") is not None:
            user_manual_path = os.path.join(
                settings.MANUAL_DIR, user_manual_info.get("manaul_file_id")
            )
            if os.path.exists(user_manual_path):
                shutil.rmtree(user_manual_path)
        # 删除APP安装包
        app_package_info = AppInfo.app_package
        if app_package_info.get("pkg_file_id") is not None:
            app_package_path = os.path.join(
                settings.PKG_DIR, app_package_info.get("pkg_file_id")
            )
            if os.path.exists(app_package_path):
                shutil.rmtree(app_package_path)
        # 删除APP安装日志
        install_log_info = AppInfo.install_log
        if install_log_info is not None:
            install_log_path = os.path.join(
                settings.INSTALL_LOG_DIR, install_log_info.split("/")[0]
            )
            if os.path.exists(install_log_path):
                shutil.rmtree(install_log_path)
        AppInfo.delete()

        return self.success()


class ReinstallApp(APIView):
    """重新安装APP"""

    def patch(self, request):
        data = request.data
        app_package = data.get("app_package")
        install_path = data.get("install_path")
        auth_code = data.get("auth_code")
        App_id = data.get("id")

        AppInfo = AppManager.objects.get(id=App_id)
        with transaction.atomic():
            AppInfo.install_status = 1
            AppInfo.visible = False
            AppInfo.change_time = datetime.datetime.today()
            AppInfo.save()
            print(" Patch AppManager id = {}".format(AppInfo.id))
        if os.path.exists(install_path):
            shutil.rmtree(install_path)
        # 异步执行安装函数
        if app_package.get("pkg_file_id"):
            run_task(
                install_App,
                auth_code=auth_code,
                app_package=app_package,
                install_path=install_path,
                new_app_id=App_id,
            )

        return self.success()


class AppConfigList(APIView):
    """获取App软件列表，按修改时间排序"""

    @manager_admin_required
    def get(self, request):
        # 按修改时间排序
        if request.user.admin_type == AdminType.SUPER_ADMIN:
            App_manager_list_info = AppManager.objects.all().order_by("-change_time")
            # 分页
            data = self.paginate_data(
                request, App_manager_list_info, AppManagerListSerializer
            )

            return self.success(data)


class CheckAppConfig(APIView):
    """校验App配置是否正确"""

    def post(self, request):
        data = request.data

        install_path = data.get("install_path")
        bin_path = data.get("bin_path")
        app_name = data.get("name")
        App_id = data.get("id")
        if isinstance(bin_path, list):
            bin_path = "/".join(bin_path)
        # 可执行文件路径
        executable_file_path = install_path + "/" + bin_path
        # 删除可执行文件路径中多余的"/"号
        while executable_file_path.find("//") != -1:
            executable_file_path = executable_file_path.replace("//", "/")

        # 检查APP完整路径是否已存在
        complete_path_list = AppManager.objects.values_list(
            "complete_path", flat=True
        ).exclude(id=App_id)
        if executable_file_path in complete_path_list:
            error_msg = "APP 可执行路径已存在，请修改后保存！".format(app_name)
            logger.error(error_msg)
            return self.error(error_msg)

        if executable_file_path is not None:
            # 是否存在该APP
            if not os.path.isfile(executable_file_path):
                error_msg = "找不到APP {}".format(os.path.basename(executable_file_path))
                logger.error(error_msg)
                return self.error(error_msg)
            else:
                # 是否所有用户都有执行权限
                exec_number = oct(os.stat(executable_file_path).st_mode)[-3:]
                for i in list(exec_number):
                    if int(i) < 5:
                        error_msg = "该文件没有执行权限！"
                        logger.error(error_msg)
                        return self.error(error_msg)
                return self.success()
        else:
            error_msg = "APP安装路径需要填写"
            return self.error(error_msg)


class UploadManual(CSRFExemptAPIView):
    """上传用户手册"""

    request_parsers = ()

    def get(self, request):
        pass

    def post(self, request):
        files = request.FILES.get("file")
        fileName = files.name

        if len(files) == 0:
            error_msg = "Error, no file found !"
            logger.error(error_msg)
            return self.error(error_msg)

        tempDir = os.path.join(settings.TMP_DIR, rand_str())
        if os.path.exists(tempDir):
            shutil.rmtree(tempDir)
        os.makedirs(tempDir, exist_ok=True)

        uploadFile = os.path.join(tempDir, fileName)
        # 创建子目录
        os.makedirs(os.path.dirname(uploadFile), exist_ok=True)
        # 写入数据
        with open(uploadFile, "wb") as f:
            for chunk in files:
                f.write(chunk)

        manual_file_id, info = process_uploadFiles(
            settings.MANUAL_DIR, uploadFile
        )  # noqa
        shutil.rmtree(tempDir)

        return self.success({"manual_file_id": manual_file_id, "info": info})


class UploadApp(UploadManual):
    """上传APP安装包"""

    def post(self, request):
        files = request.FILES.get("pkg")
        fileName = files.name

        if len(files) == 0:
            error_msg = "Error, no file found !"
            logger.error(error_msg)
            return self.error(error_msg)

        tempDir = os.path.join(settings.TMP_DIR, rand_str())
        if os.path.exists(tempDir):
            shutil.rmtree(tempDir)
        os.makedirs(tempDir, exist_ok=True)

        uploadFile = os.path.join(tempDir, fileName)
        # 创建子目录
        os.makedirs(os.path.dirname(uploadFile), exist_ok=True)
        # 写入数据
        with open(uploadFile, "wb") as f:
            for chunk in files:
                f.write(chunk)

        pkg_file_id, info = process_uploadFiles(settings.PKG_DIR, uploadFile)  # noqa
        shutil.rmtree(tempDir)

        return self.success({"pkg_file_id": pkg_file_id, "info": info})


class GetInstallLog(APIView):
    """获取APP安装日志"""

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

        install_log = AppInfo.install_log
        if install_log:
            install_log_url = "/public/novncfiles/installlogs/" + str(install_log)
            return self.success({"install_log_url": install_log_url})
        else:
            error_msg = "安装日志不存在，请确认APP是否通过本系统安装！"
            return self.error(error_msg)


class GetPkgSubdir(APIView):
    """获取APP安装路径下文件列表"""

    def post(self, request):
        bin_path = request.data.get("path")

        # 列出指定根目录下的所有文件和文件夹
        file_list = get_file_list(bin_path)
        ret_data = {"error": None, "data": {"cascader_file_list": file_list}}

        return JsonResponse(ret_data, safe=False)


def get_file_list(path):
    """获取目标目录下文件列表"""

    file_list = []
    if path:
        parent = os.listdir(path)
        for child in parent:
            child_path = os.path.join(path, child)
            # 如果是目录
            if os.path.isdir(child_path):
                # child_file_list = get_file_list(child_path)
                file_list.append({"value": child, "label": child, "children": []})
            else:
                file_list.append({"value": child, "label": child})

    return file_list
