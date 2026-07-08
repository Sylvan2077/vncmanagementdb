#!/usr/bin/env python
# coding: utf-8

from apps.announcement.models import Announcement
from apps.utils.api._serializers import UsernameSerializer
from rest_framework import serializers


class AnnouncementSerializer(serializers.ModelSerializer):
    submitter = UsernameSerializer()

    class Meta:
        model = Announcement
        fields = "__all__"


class CreateAnnouncementSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=64)
    category = serializers.CharField(max_length=64)
    content = serializers.CharField(max_length=1024 * 1024 * 8)
    visible = serializers.BooleanField()


class EditAnnouncementSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField(max_length=64)
    category = serializers.CharField(max_length=64)
    content = serializers.CharField(max_length=1024 * 1024 * 8)
    visible = serializers.BooleanField()
