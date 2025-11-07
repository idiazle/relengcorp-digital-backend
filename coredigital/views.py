from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from reldigital.models import User, Entity, Report, Notice
from .serializers import UserSerializer, EntitySerializer, ReportSerializer, NoticeSerializer


# ======================
#        USER
# ======================
class UserAPIView(APIView):
    def get(self, request, pk=None):
        if pk:
            user = get_object_or_404(User, pk=pk, deleted=False)
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            users = User.objects.filter(deleted=False)
            serializer = UserSerializer(users, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk=None):
        user = get_object_or_404(User, pk=pk, deleted=False)
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None):
        user = get_object_or_404(User, pk=pk, deleted=False)
        user.deleted = True
        user.save()
        return Response({"message": "Usuario eliminado correctamente"}, status=status.HTTP_204_NO_CONTENT)


# ======================
#       ENTITY
# ======================
class EntityAPIView(APIView):
    def get(self, request, pk=None):
        if pk:
            entity = get_object_or_404(Entity, pk=pk, deleted=False)
            serializer = EntitySerializer(entity)
            return Response(serializer.data)
        else:
            entities = Entity.objects.filter(deleted=False)
            serializer = EntitySerializer(entities, many=True)
            return Response(serializer.data)

    def post(self, request):
        serializer = EntitySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user if request.user.is_authenticated else None)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk=None):
        entity = get_object_or_404(Entity, pk=pk, deleted=False)
        serializer = EntitySerializer(entity, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None):
        entity = get_object_or_404(Entity, pk=pk, deleted=False)
        entity.deleted = True
        entity.save()
        return Response({"message": "Entidad eliminada correctamente"}, status=status.HTTP_204_NO_CONTENT)


# ======================
#        REPORT
# ======================
class NoticesByReportApiView(APIView):
    def get(self, request, pk=None):
        notices = Notice.objects.filter(report=pk, deleted=False)
        notices_serialized = NoticeSerializer(notices, many=True)
        return Response(notices_serialized.data)

class ReportAPIView(APIView):
    def get(self, request, pk=None):
        if pk:
            report = get_object_or_404(Report, pk=pk, deleted=False)
            serializer = ReportSerializer(report)
            return Response(serializer.data)
        else:
            reports = Report.objects.filter(deleted=False)
            serializer = ReportSerializer(reports, many=True)
            return Response(serializer.data)

    def post(self, request):
        serializer = ReportSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user if request.user.is_authenticated else None)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk=None):
        report = get_object_or_404(Report, pk=pk, deleted=False)
        serializer = ReportSerializer(report, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None):
        report = get_object_or_404(Report, pk=pk, deleted=False)
        report.deleted = True
        report.save()
        return Response({"message": "Reporte eliminado correctamente"}, status=status.HTTP_204_NO_CONTENT)


# ======================
#        NOTICE
# ======================
class NoticeAPIView(APIView):
    def get(self, request, pk=None):
        if pk:
            notice = get_object_or_404(Notice, pk=pk, deleted=False)
            serializer = NoticeSerializer(notice)
            return Response(serializer.data)
        else:
            notices = Notice.objects.filter(deleted=False)
            serializer = NoticeSerializer(notices, many=True)
            return Response(serializer.data)

    def post(self, request):
        serializer = NoticeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user if request.user.is_authenticated else None)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk=None):
        notice = get_object_or_404(Notice, pk=pk, deleted=False)
        serializer = NoticeSerializer(notice, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None):
        notice = get_object_or_404(Notice, pk=pk, deleted=False)
        notice.deleted = True
        notice.save()
        return Response({"message": "Aviso eliminado correctamente"}, status=status.HTTP_204_NO_CONTENT)
