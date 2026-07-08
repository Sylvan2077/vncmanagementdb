#!/usr/bin/env python
# coding: utf-8

import logging
import os
import base64

from apps.account.serializers import FileUploadForm, ImageUploadForm
from apps.utils.api import CSRFExemptAPIView
from apps.utils.shortcuts import rand_str
from django.conf import settings

logger = logging.getLogger(__name__)


class SimditorImageUploadAPIView(CSRFExemptAPIView):
    request_parsers = ()

    def post(self, request):
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            img = form.cleaned_data["image"]
        else:
            return self.response(
                {"success": False, "msg": "Upload failed", "file_path": ""}
            )

        suffix = os.path.splitext(img.name)[-1].lower()
        if suffix not in [".gif", ".jpg", ".jpeg", ".bmp", ".png"]:
            return self.response(
                {"success": False, "msg": "Unsupported file format", "file_path": ""}
            )
        img_name = rand_str(10) + suffix
        if not os.path.exists(settings.UPLOAD_DIR):
            return self.response(
                {"success": False, "msg": "文件目录：{} 不存在".format(settings.UPLOAD_DIR), "file_path": ""}
            )
        try:
            with open(os.path.join(settings.UPLOAD_DIR, img_name), "wb") as imgFile:
                for chunk in img:
                    imgFile.write(chunk)
            img_abspath = os.path.join(settings.UPLOAD_DIR, img_name)
            if img_abspath:
                with open(img_abspath, 'rb') as f:
                    img_data = f.read()
                    base64_data = base64.b64encode(img_data)
                    base64_str = str(base64_data, 'utf-8')
                    front_str = "data:image/jpeg;base64,"
                    base64_cont = front_str + base64_str
        except IOError as e:
            logger.error(e)
            return self.response(
                {"success": False, "msg": "Upload Error", "file_path": ""}
            )
        return self.response(
            {
                "success": True,
                "msg": "Success",
                "file_path": "{}/{}".format(settings.UPLOAD_PREFIX, img_name),
                "uploadImgInfo": {"imagewithbase64": base64_cont, "realname": img.name, "finalname": img_name}
            }
        )


class SimditorFileUploadAPIView(CSRFExemptAPIView):
    request_parsers = ()

    def post(self, request):
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data["file"]
        else:
            return self.response({"success": False, "msg": "Upload failed"})

        suffix = os.path.splitext(file.name)[-1].lower()
        file_name = rand_str(10) + suffix
        try:
            with open(os.path.join(settings.UPLOAD_DIR, file_name), "wb") as f:
                for chunk in file:
                    f.write(chunk)
        except IOError as e:
            logger.error(e)
            return self.response({"success": False, "msg": "Upload Error"})
        return self.response(
            {
                "success": True,
                "msg": "Success",
                "file_path": "{}/{}".format(settings.UPLOAD_PREFIX, file_name),
                "file_name": file.name,
            }
        )
