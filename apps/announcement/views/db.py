#!/usr/bin/env python
# coding: utf-8

from apps.announcement.models import Announcement
from apps.announcement.serializers import AnnouncementSerializer
from apps.utils.api import APIView
from django.db import transaction


class AnnouncementAPI(APIView):
    def get(self, request):
        """
        获取公告信息
        """
        # 限定只获取公开公告
        announcements = Announcement.objects.filter(visible=True)
        announcements = announcements.order_by("-create_time")
        return self.success(self.paginate_data(request, announcements, AnnouncementSerializer))

    def patch(self, request):
        """
        部分修改公告的内容
        """
        data = request.data
        announcement_id = data.get("announcement_id")
        try:
            announcement = Announcement.objects.get(id=announcement_id)
        except Announcement.DoesNotExist:
            return self.error("Announcement does not exist.")

        # 修改公告阅读量，点击一次增加1
        editData = {}
        editData["read_count"] = announcement.read_count + 1

        with transaction.atomic():
            for k, v in editData.items():
                setattr(announcement, k, v)
            announcement.save()
            print(" Patch Announcement id = {}".format(announcement.id))
            return self.success(AnnouncementSerializer(announcement).data)
