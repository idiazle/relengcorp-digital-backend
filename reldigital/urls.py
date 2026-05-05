"""
URLs de la aplicación reldigital
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    LoginAPIView,
    CurrentUserAPIView,
    UserAPIView,
    GroupAPIView,
    EntityAPIView,
    EntityTreeAPIView,
    AreasAPIView,
    EquipmentsAPIView,
    ReportAPIView,
    NoticeAPIView,
    NoticesByReportApiView,
    EquipmentConditionSummaryAPIView,
    EquipmentConditionByMonthAPIView,
)

app_name = 'reldigital'

urlpatterns = [
    # AUTH
    path('auth/login', LoginAPIView.as_view(), name='auth-login'),
    path('auth/refresh', TokenRefreshView.as_view(), name='auth-refresh'),
    path('auth/me', CurrentUserAPIView.as_view(), name='auth-me'),

    # USER
    path('users', UserAPIView.as_view(), name='user-list'),
    path('users/<int:pk>', UserAPIView.as_view(), name='user-detail'),
    
    # GROUPS
    path('groups', GroupAPIView.as_view(), name='group-list'),

    # ENTITY
    path('entities', EntityAPIView.as_view(), name='entity-list'),
    path('entities/<int:pk>', EntityAPIView.as_view(), name='entity-detail'),
    path('entities/tree', EntityTreeAPIView.as_view(), name='entity-tree'),
    path('areas', AreasAPIView.as_view(), name='areas-list'),
    path('equipments', EquipmentsAPIView.as_view(), name='equipments-list'),

    # REPORT
    path('reports', ReportAPIView.as_view(), name='report-list'),
    path('reports/<int:pk>', ReportAPIView.as_view(), name='report-detail'),

    # NOTICE
    path('notices', NoticeAPIView.as_view(), name='notice-list'),
    path('notices/<int:pk>', NoticeAPIView.as_view(), name='notice-detail'),
    
    # ADDITIONAL ENDPOINTS
    path('notices-by-report/<int:pk>', NoticesByReportApiView.as_view(), name='notices-by-report'),
    path('summary-conditions', EquipmentConditionSummaryAPIView.as_view(), name='summary-conditions'),
    path('equipments/conditions-by-month', EquipmentConditionByMonthAPIView.as_view(), name='conditions-by-month'),
]
