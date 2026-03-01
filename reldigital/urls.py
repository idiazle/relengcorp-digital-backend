"""
URLs de la aplicación reldigital
"""
from django.urls import path
from .views import (
    UserAPIView,
    GroupAPIView,
    EntityAPIView,
    ReportAPIView,
    NoticeAPIView,
    NoticesByReportApiView,
    EquipmentConditionSummaryAPIView,
    EquipmentConditionByMonthAPIView,
)

app_name = 'reldigital'

urlpatterns = [
    # USER
    path('users', UserAPIView.as_view(), name='user-list'),
    path('users/<int:pk>', UserAPIView.as_view(), name='user-detail'),
    
    # GROUPS
    path('groups', GroupAPIView.as_view(), name='group-list'),

    # ENTITY
    path('entities', EntityAPIView.as_view(), name='entity-list'),
    path('entities/<int:pk>', EntityAPIView.as_view(), name='entity-detail'),

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
