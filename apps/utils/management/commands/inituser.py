#!/usr/bin/env python
# coding: utf-8

from apps.account.models import AdminType, CasePermission, User, UserProfile
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--username", type=str)
        parser.add_argument("--password", type=str)
        parser.add_argument("--action", type=str)

    def handle(self, *args, **options):
        username = options["username"]
        password = options["password"]
        action = options["action"]

        if not (username and password and action):
            self.stdout.write(self.style.ERROR("Invalid args"))
            exit(1)

        if action == "create_super_admin":
            if User.objects.filter(id=1).exists():
                self.stdout.write(
                    self.style.SUCCESS(
                        "User {} exists, operation ignored".format(username)
                    )
                )
                exit()

            user = User.objects.create(
                username=username,
                admin_type=AdminType.SUPER_ADMIN,
                case_permission=CasePermission.ALL,
            )
            user.set_password(password)
            user.save()
            UserProfile.objects.create(user=user)

            self.stdout.write(self.style.SUCCESS("Super Admin User created"))
        elif action == "create_admin":
            if User.objects.filter(id=2).exists():
                self.stdout.write(
                    self.style.SUCCESS(
                        "User {} exists, operation ignored".format(username)
                    )
                )
                exit()

            user = User.objects.create(
                username=username,
                admin_type=AdminType.ADMIN,
                case_permission=CasePermission.OWN,
            )
            user.set_password(password)
            user.save()
            UserProfile.objects.create(user=user)

            self.stdout.write(self.style.SUCCESS("Admin User created"))
        elif action == "reset":
            try:
                user = User.objects.get(username=username)
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS("Password is rested"))
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        "User {} doesnot exist, operation ignored".format(username)
                    )
                )
                exit(1)
        else:
            raise ValueError("Invalid action")
