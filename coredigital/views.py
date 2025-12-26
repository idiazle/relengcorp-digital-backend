from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from reldigital.models import User, Entity, Report, Notice
from .serializers import UserSerializer, EntitySerializer, ReportSerializer, NoticeSerializer
from django.db.models import OuterRef, Subquery
from django.utils import timezone
from datetime import timedelta


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

# ======================
#       ADDITIONAL VIEWS
# ======================

class EquipmentConditionSummaryAPIView(APIView):
     def get(self, request):
        # Subquery para obtener la última condición del equipo
        last_report = (
            Report.objects
            .filter(entity=OuterRef("pk"), deleted=False)
            .order_by("-created_at")
        )

        equipos = (
            Entity.objects
            .filter(type=3, deleted=False)
            .annotate(
                last_condition=Subquery(last_report.values("condition")[:1])
            )
        )
        # Inicializar conteo
        summary = {
            "c1": 0,
            "c2": 0,
            "c3": 0,
            "c4": 0,
        }
        for equipo in equipos:
            if equipo.last_condition == 1:
                summary["c1"] += 1
            elif equipo.last_condition == 2:
                summary["c2"] += 1
            elif equipo.last_condition == 3:
                summary["c3"] += 1
            elif equipo.last_condition == 4:
                summary["c4"] += 1

        return Response(summary, status=status.HTTP_200_OK)
     

class EquipmentConditionByMonthAPIView(APIView):
    def get(self, request):
        today = timezone.now().date()

        # Generar los últimos 7 meses (YYYY-MM)
        months = []
        for i in range(6, -1, -1):
            month = (today.replace(day=1) - timedelta(days=30 * i))
            months.append(month.strftime("%Y-%m"))

        # Inicializar estructura
        result = {
            month: {
                "c1": 0,
                "c2": 0,
                "c3": 0,
                "c4": 0,
            }
            for month in months
        }

        # Equipos
        equipos = Entity.objects.filter(type=3, deleted=False)

        for month in months:
            year, m = map(int, month.split("-"))

            start_date = timezone.datetime(year, m, 1, tzinfo=timezone.get_current_timezone())

            if m == 12:
                end_date = timezone.datetime(year + 1, 1, 1, tzinfo=timezone.get_current_timezone())
            else:
                end_date = timezone.datetime(year, m + 1, 1, tzinfo=timezone.get_current_timezone())

            # Último reporte del equipo en ese mes
            last_report = (
                Report.objects
                .filter(
                    entity=OuterRef("pk"),
                    deleted=False,
                    created_at__gte=start_date,
                    created_at__lt=end_date,
                )
                .order_by("-created_at")
            )

            equipos_mes = equipos.annotate(
                last_condition=Subquery(last_report.values("condition")[:1])
            )

            for e in equipos_mes:
                if e.last_condition:
                    result[month][f"c{e.last_condition}"] += 1

        return Response(result, status=status.HTTP_200_OK)