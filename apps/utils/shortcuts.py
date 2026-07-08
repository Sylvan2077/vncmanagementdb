#!/usr/bin/env python
# coding: utf-8

import datetime
import hashlib
import json
import os
import random
import re
import shutil
import time
from base64 import b64encode, b64decode
from functools import wraps
from io import BytesIO

from django.conf import settings
from django.utils.crypto import get_random_string
from envelopes import Envelope


def rand_str(length=32, type="lower_hex"):
    """生成指定长度的随机字符串或者数字, 可以用于密钥等安全场景

    :param length=32: 字符串或者数字的长度，默认 32
    :param type="lower_hex": str 代表随机字符串，num 代表随机数字
    """
    if type == "str":
        return get_random_string(
            length,
            allowed_chars="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789",
        )
    elif type == "lower_str":
        return get_random_string(
            length, allowed_chars="abcdefghijklmnopqrstuvwxyz0123456789"
        )
    elif type == "lower_hex":
        return random.choice("123456789abcdef") + get_random_string(
            length - 1, allowed_chars="0123456789abcdef"
        )
    else:
        return random.choice("123456789") + get_random_string(
            length - 1, allowed_chars="0123456789"
        )


def build_query_string(kv_data, ignore_none=True):
    """eg. {"a": 1, "b": "test"} -> "?a=1&b=test
    :param kv_data: 输入的字段
    :param ignore_none=True: 是否忽略空的查询键值
    """
    query_string = ""
    for k, v in kv_data.items():
        if ignore_none is True and kv_data[k] is None:
            continue
        if query_string != "":
            query_string += "&"
        else:
            query_string = "?"
        query_string += k + "=" + str(v)
    return query_string


def img2base64(img):
    """将图像转换为 base64 格式"""
    with BytesIO() as buf:
        img.save(buf, "gif")
        buf_str = buf.getvalue()
    img_prefix = "data:image/png;base64,"
    b64_str = img_prefix + b64encode(buf_str).decode("utf-8")
    return b64_str


def base642img(base64_data):
    """将base64编码后的图片进行解码"""
    img_name = rand_str(10) + ".jpg"
    img_path = os.path.join(settings.UPLOAD_DIR, img_name)
    base64_data += "="
    base64_data = base64_data[22:]
    with open(img_path, 'wb') as file:
        img = b64decode(base64_data)
        file.write(img)
    return img_path


def datetime2str(value, format="iso-8601"):
    """将 datetime 转换为 str"""
    if format.lower() == "iso-8601":
        value = value.isoformat()
        if value.endswith("+00:00"):
            value = value[:-6] + "Z"
        return value
    return value.strftime(format)


def timestamp2utcstr(value):
    """将 timestamp 转换为 utc str 格式"""
    return datetime.datetime.utcfromtimestamp(value).isoformat()


def natural_sort_key(s, _nsre=re.compile(r"(\d+)")):
    """自然排序"""
    return [
        int(text) if text.isdigit() else text.lower() for text in re.split(_nsre, s)
    ]


def get_env(name, default=""):
    """获取环境变量，如果没有就设置为给定的默认值"""
    return os.environ.get(name, default)


def DRAMATIQ_WORKER_ARGS(time_limit=3600_000, max_retries=0, max_age=7200_000):
    """dramatiq worker 设置的参数"""
    return {"max_retries": max_retries, "time_limit": time_limit, "max_age": max_age}


def check_is_id(value):
    """检测给定值是否为正整数"""
    try:
        return int(value) > 0
    except Exception:
        return False


def timefn(fn):
    """获取函数执行时间的装饰器

    参数: fn {function} -- 待装饰的函数
    """

    @wraps(fn)
    def mesure_time(*args, **kwargs):
        t0 = time.time()
        result = fn(*args, **kwargs)
        t1 = time.time()
        # print("\n@timefn: {} took {:.10f} s".format(fn.__name__, t1 - t0))
        return result

    return mesure_time


def humansize(nbytes):
    """以可读方式返回文件的大小"""
    suffixes = ["B", "KB", "MB", "GB", "TB", "PB"]
    i = 0
    while nbytes >= 1024 and i < len(suffixes) - 1:
        nbytes /= 1024.0
        i += 1
    # ref: https://pyformat.info/
    f = ("{:.2f}".format(nbytes)).rstrip("0").rstrip(".")
    return "{} {}".format(f, suffixes[i])


def md5_for_file(path, block_size=256 * 128, hr=False):
    """计算文件的 md5 校验和"""
    md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(block_size), b""):
            md5.update(chunk)
    if hr:
        return md5.hexdigest()
    return md5.digest()


def next_caseID(case_data):
    """取消id自增"""

    if len(list(zip(*case_data))) > 0:
        existIDs = set(list(zip(*case_data))[0])
        maxID = max(existIDs)
        expectedNumbers = set(range(1, maxID + 1))
        diffNumbers = sorted(expectedNumbers.difference(existIDs))

        if len(diffNumbers) > 0:
            return diffNumbers[0]
        else:
            return maxID + 1
    else:
        return 1


def process_uploadFiles(uploadFolder, uploadFiles):
    """
    处理上传上来的文件或目录。
    默认每次生成一个新的目录；如果带有 folderID，则上传至同一个地方。

    :param uploadFolder: 待上传的目录，不包含具体的子目录；eg. setting.TESTCASE_DIR
    :param uploadFiles: 上传的文件名，单个时为 str，多个时为 list.
    """

    # 如果 uploadFolder 不存在，则创建
    os.makedirs(uploadFolder, exist_ok=True)

    folderID = rand_str()
    folder = os.path.abspath(os.path.join(uploadFolder, folderID))

    if isinstance(uploadFiles, str):
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        shutil.move(uploadFiles, folder)
    if isinstance(uploadFiles, list):
        orgi_temp_dir = os.path.commonpath(uploadFiles)
        # 注意：shutil.move函数的目标路径如果是一个不存在的文件夹路径，则会将原文件移动到该文件夹上一目录中，且以该文件夹的名字重命名，
        # 只上传了一个文件并且不是写在32位的目录中的
        if os.path.isfile(orgi_temp_dir):
            if not os.path.exists(folder):
                os.makedirs(folder, exist_ok=True)
            # 如果只上传了一个目录，获取的 commonpath 还需要处理
            # orgi_temp_dir = os.path.dirname(orgi_temp_dir)
            # fp, gp = orgi_temp_dir.split(os.path.sep + 'tmp' + os.path.sep)
            # orgi_temp_dir = os.path.join(fp, 'tmp', gp.split(os.path.sep)[0])
        shutil.move(orgi_temp_dir, folder)

    file_list = []
    for root, _, files in os.walk(folder):
        for file in files:
            file_list.append(os.path.join(root, file))

    # 临时变量
    size_cache = {}
    md5_cache = {}
    info = []
    file_info = {"files": {}}

    # 缓存每个文件的大小和 md5 值
    for item in file_list:
        with open(item) as f:
            size_cache[item] = humansize(os.path.getsize(item))
            md5_cache[item] = md5_for_file(item, hr=True)

    # 循环存入数据
    for index, item in enumerate(file_list):
        data = {
            "name": os.path.relpath(item, folder),
            "md5": md5_cache[item],
            "file_size": size_cache[item],
        }
        info.append(data)
        file_info["files"]["file_" + "{:03d}".format(index + 1)] = data

    # json 序列化数据到文件
    info_path = os.path.join(folder, "info")
    # 如果已经有 info 文件，先删除
    if os.path.exists(info_path):
        os.remove(info_path)
    # 再写入 info 信息
    with open(info_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(file_info, indent=2, ensure_ascii=False))

    return folderID, info


def check_access(file, mode):
    """检测文件的获取权限
    Args:
        file (str): 待检验文件的路径
        mode (str): 待检验的权限，有如下选项：
                    os.R_OK 检验是否可读    os.W_OK 检验是否可写
                    os.X_OK 检验是否可执行  os.F_OK 检验文件是否存在
                    不同的 mode 可以使用 `+` 连接，例如 os.R_OK + os.W_OK
    """

    if not os.access(file, mode):
        raise RuntimeError(
            'error: can not access file "{0}" with mode {1}.'.format(
                file, mode)
        )  # noqa


def search_file(path, file_name, is_recurse=True, is_find_one=True):
    """在一个目录中搜索某个特定文件
    Args:
        path (str): 待搜索的目录
        file_name (str): 待搜索的文件名称
        is_recurse (bool, optional): 是否递归搜索，默认为 True.
        is_find_one (bool, optional): 是否只找到第一个匹配项，默认为 True.
    Returns:
        file_list (list): 包含该文件所在路径的列表
    """
    file_list = []
    check_access(path, os.R_OK)

    subs = os.listdir(path)
    # 首先搜索当前子目录
    for i in range(0, len(subs)):
        f = os.path.join(path, subs[i])
        if os.path.isfile(f) and os.path.basename(f) == file_name:
            if is_find_one and len(file_list) != 0:
                return file_list
            elif is_find_one and len(file_list) == 0:
                file_list.append(f)
                return file_list
            else:
                file_list.append(f)
        else:
            continue

    # 接着递归搜索子目录
    for i in range(0, len(subs)):
        f = os.path.join(path, subs[i])
        if os.path.isdir(f) and is_recurse is True:
            if is_find_one and len(file_list) != 0:
                return file_list
            else:
                file_list += search_file(f, file_name, is_recurse, is_find_one)

    return file_list


def removeQuotes(s):
    """去除字符串的前后引号
    '"a"' --> "a"
    "'b'" --> 'b'
    """
    if not isinstance(s, str):
        print("error, {} is not a string".format(s))
    if (s.startswith("'") and s.endswith("'")) or (
        s.startswith('"') and s.endswith('"')
    ):
        return s[1:-1]


def make_zipfile(zip_fn, src):
    """创建 zip 压缩包
    ref: https://github.com/python/cpython/blob/77f0a23e7a9fb247101b9b14a060c4ba1c4b87a5/Lib/zipfile.py#L2417
    note: 当前只支持压缩一个目录

    Args:
        zip_fn (string): 将要产生的压缩包的名称或者 file-like 的对象
        src (string): 被压缩路径
    """
    import zipfile

    def addToZip(zf, path, zippath):
        if os.path.isfile(path):
            zf.write(path, zippath)
        elif os.path.isdir(path):
            if zippath:
                zf.write(path, zippath)
            for nm in os.listdir(path):
                addToZip(zf,
                         os.path.join(path, nm), os.path.join(zippath, nm))
        # else: ignore

    with zipfile.ZipFile(zip_fn, 'w') as zf:
        addToZip(zf, src, '')
        file_size = sum([zinfo.file_size for zinfo in zf.filelist])
        return file_size

def time_stamp_to_date(time_stamp):
    """
    根据文件上传的时间戳, 格式化为 2020-6-30 12:00:00
    """
    now = int(round(time_stamp * 1000))
    t = time.localtime(now / 1000)
    return time.strftime('%Y-%m-%d %H:%M:%S', t)


def file_store_path(time_stamp):
    now = int(round(time_stamp * 1000))
    t = time.localtime(now / 1000)
    return os.path.join(settings.MEDIA_ROOT, str(t[0]), str(t[1]), str(t[2]))
