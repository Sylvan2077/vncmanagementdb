"""VNC URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf.urls import include, url

urlpatterns = [
    # account APP
    url(r"^api/", include("apps.account.urls.db")),
    url(r"^api/admin/", include("apps.account.urls.admin")),
    # announcement APP
    url(r"^api/", include("apps.announcement.urls.db")),
    url(r"^api/admin/", include("apps.announcement.urls.admin")),
    # conf APP
    url(r"^api/", include("apps.conf.urls.db")),
    url(r"^api/admin/", include("apps.conf.urls.admin")),
    # vncserver APP
    url(r"^api/", include("apps.vncserver.urls.db")),
    url(r"^api/admin/", include("apps.vncserver.urls.admin")),
    # utils APP
    url(r"^api/admin/", include("apps.utils.urls")),
]
