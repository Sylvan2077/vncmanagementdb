#!/usr/bin/env python
# coding: utf-8


from apps.account.decorators import super_admin_required, manager_admin_required
from apps.announcement.models import Announcement
from apps.announcement.serializers import (
    AnnouncementSerializer,
    CreateAnnouncementSerializer,
    EditAnnouncementSerializer,
)
from apps.utils.api import APIView, validate_serializer
from django.db import transaction
from django.db.models import Q
from django.conf import settings

from bs4 import BeautifulSoup
import base64


class AnnouncementAdminAPI(APIView):
    # python 装饰器,调用了super_admin_required类,调用类时是调用其__call__方法
    @manager_admin_required
    def get(self, request):
        """
        获取公告列表 或者 获取某个公告
        """
        announcement_id = request.GET.get("id")
        if announcement_id:
            try:
                announcement = Announcement.objects.get(id=announcement_id)
                return self.success(AnnouncementSerializer(announcement).data)
            except Announcement.DoesNotExist:
                return self.error("Announcement does not exist")

        # 公告以创建时间来排序
        announcement = Announcement.objects.all().order_by("-create_time")
        if request.GET.get("visible") == "true":
            announcement = announcement.filter(visible=True)

        # 按照关键字查询
        keyword = request.GET.get("keyword", None)
        if keyword:
            announcement = announcement.filter(
                Q(title__icontains=keyword) | Q(content__icontains=keyword)
            ).distinct()  # noqa
            # “Q”是Django的筛选函数，.distinct()是筛选结果去重
        return self.success(self.paginate_data(request, announcement, AnnouncementSerializer))

    @validate_serializer(CreateAnnouncementSerializer)
    @super_admin_required
    def post(self, request):
        """
        发布公告
        """
        data = request.data
        with transaction.atomic():
            announcement = Announcement.objects.create(
                title=data["title"],
                category=data["category"],
                content=data["content"],
                submitter=request.user,
                visible=data["visible"],
            )
            return self.success(AnnouncementSerializer(announcement).data)

    @validate_serializer(EditAnnouncementSerializer)
    @super_admin_required
    def put(self, request):
        """
        修改公告内容
        """
        data = request.data
        try:
            announcement = Announcement.objects.get(id=data.pop("id"))
        except Announcement.DoesNotExist:
            return self.error("Announcement does not exist.")

        # 避免同时操作数据，造成逻辑出错，有待深究
        editData = {}
        for attr in ["title", "category", "content", "visible"]:
            if data.get(attr) is not None:
                editData[attr] = data.get(attr)
        with transaction.atomic():
            for k, v in editData.items():
                setattr(announcement, k, v)
            announcement.save()

            return self.success()

    @super_admin_required
    def patch(self, request):
        """
        部分修改公告的内容
        """
        data = request.data
        try:
            announcement = Announcement.objects.get(id=data.pop("id"))
        except Announcement.DoesNotExist:
            return self.error("Announcement does not exist.")

        # 当前只允许修改是否可见以及算editData例的名称
        editData = {}
        for attr in ["title", "visible"]:
            if data.get(attr) != None:
                editData[attr] = data.get(attr)
        # 添加对提交人的更新
        editData["submitter"] = request.user

        with transaction.atomic():
            for k, v in editData.items():
                setattr(announcement, k, v)
            announcement.save()
            print(" Patch Announcement id = {}".format(announcement.id))
            return self.success(AnnouncementSerializer(announcement).data)

    @super_admin_required
    def delete(self, request):
        """
        删除公告
        """
        if request.GET.get("id"):
            with transaction.atomic():
                Announcement.objects.filter(id=request.GET["id"]).delete()
                return self.success()
