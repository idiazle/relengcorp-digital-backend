"""
URL configuration for coredigital project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import UserAPIView, EntityAPIView, ReportAPIView, NoticeAPIView, NoticesByReportApiView

urlpatterns = [
    path('api/admin', admin.site.urls),
        # USER
    path('api/users', UserAPIView.as_view()),
    path('api/users/<int:pk>', UserAPIView.as_view()),

    # ENTITY
    path('api/entities', EntityAPIView.as_view()),
    path('api/entities/<int:pk>', EntityAPIView.as_view()),

    # REPORT
    path('api/reports', ReportAPIView.as_view()),
    path('api/reports/<int:pk>', ReportAPIView.as_view()),

    # NOTICE
    path('api/notices', NoticeAPIView.as_view()),
    path('api/notices/<int:pk>', NoticeAPIView.as_view()),
    
    #OTHERS
    path('api/notices-by-report/<int:pk>', NoticesByReportApiView.as_view()),
    
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)