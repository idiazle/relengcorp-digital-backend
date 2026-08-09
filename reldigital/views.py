from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import get_object_or_404
from django.db.models import OuterRef, Subquery, Q
from django.utils import timezone
from django.contrib.auth.models import Group
from datetime import timedelta

from .models import User, Entity, Report, Notice
from .serializers import UserSerializer, EntitySerializer, ReportSerializer, NoticeSerializer, GroupSerializer, LoginSerializer


# ======================
#      PAGINATION
# ======================
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# ======================
#        AUTH
# ======================
class LoginAPIView(TokenObtainPairView):
    """Endpoint de login personalizado que retorna tokens con info del usuario"""
    serializer_class = LoginSerializer


class CurrentUserAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ======================
#        USER
# ======================
class UserAPIView(APIView):
    # pagination_class = StandardResultsSetPagination
    
    def get(self, request, pk=None):
        if pk:
            # Obtener solo usuarios no eliminados
            user = get_object_or_404(User.objects.filter(deleted=False), pk=pk)
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            # Listar solo usuarios no eliminados
            users = User.objects.filter(deleted=False)
            
            # Filtros opcionales
            position = request.query_params.get('position', None)
            if position:
                users = users.filter(position__icontains=position)
            
            # Búsqueda por múltiples campos
            search = request.query_params.get('search', None)
            if search:
                users = users.filter(
                    Q(username__icontains=search) |
                    Q(name__icontains=search) |
                    Q(last_name__icontains=search) |
                    Q(email__icontains=search) |
                    Q(code__icontains=search) |
                    Q(dui__icontains=search)
                )
            
            # Ordenamiento (por defecto: más recientes primero)
            ordering = request.query_params.get('ordering', '-created_at')
            users = users.order_by(ordering)
            
            # Paginación
            # paginator = self.pagination_class()
            # page = paginator.paginate_queryset(users, request)
            # if page is not None:
            #     serializer = UserSerializer(page, many=True)
            #     return paginator.get_paginated_response(serializer.data)
            
            serializer = UserSerializer(users, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk=None):
        # Solo actualizar usuarios no eliminados
        user = get_object_or_404(User.objects.filter(deleted=False), pk=pk)
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None):
        # Eliminación lógica: solo marcar como eliminado
        user = get_object_or_404(User.objects.filter(deleted=False), pk=pk)
        user.deleted = True
        user.save()  # La señal actualizará deleted_at automáticamente
        return Response({"message": "Usuario eliminado correctamente"}, status=status.HTTP_204_NO_CONTENT)


# ======================
#       GROUP
# ======================
class GroupAPIView(APIView):
    """Endpoint para listar grupos disponibles (roles de usuario)"""
    
    def get(self, request):
        """Listar todos los grupos disponibles"""
        groups = Group.objects.all().order_by('name')
        serializer = GroupSerializer(groups, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ======================
#       ENTITY
# ======================
class EntityAPIView(APIView):
    # pagination_class = StandardResultsSetPagination
    
    def get(self, request, pk=None):
        if pk:
            # Obtener solo entidades no eliminadas
            entity = get_object_or_404(Entity.objects.filter(deleted=False), pk=pk)
            serializer = EntitySerializer(entity)
            return Response(serializer.data)
        else:
            # Listar solo entidades no eliminadas de tipo Planta (1) o Área (2)
            entities = Entity.objects.filter(deleted=False, type__in=[1, 2, 3])
            
            # Filtros opcionales
            entity_type = request.query_params.get('type', None)
            if entity_type:
                entities = entities.filter(type=entity_type)
            
            parent_id = request.query_params.get('parent', None)
            if parent_id:
                if parent_id.lower() == 'null':
                    entities = entities.filter(parent__isnull=True)
                else:
                    entities = entities.filter(parent_id=parent_id)
            
            # Búsqueda por nombre o tag
            search = request.query_params.get('search', None)
            if search:
                entities = entities.filter(
                    Q(name__icontains=search) |
                    Q(tag__icontains=search)
                )
            
            # Ordenamiento (por defecto: tipo descendente, luego por nombre)
            ordering = request.query_params.get('ordering', None)
            if ordering:
                entities = entities.order_by(ordering)
            else:
                entities = entities.order_by('-type', 'name')
            
            # Paginación
            # paginator = self.pagination_class()
            # page = paginator.paginate_queryset(entities, request)
            # if page is not None:
            #     serializer = EntitySerializer(page, many=True)
            #     return paginator.get_paginated_response(serializer.data)
            
            serializer = EntitySerializer(entities, many=True)
            return Response(serializer.data)

    def post(self, request):
        serializer = EntitySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user if request.user.is_authenticated else None)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk=None):
        # Solo actualizar entidades no eliminadas
        entity = get_object_or_404(Entity.objects.filter(deleted=False), pk=pk)
        serializer = EntitySerializer(entity, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None):
        # Eliminación lógica: solo marcar como eliminado
        entity = get_object_or_404(Entity.objects.filter(deleted=False), pk=pk)
        entity.deleted = True
        entity.save()  # La señal actualizará deleted_at automáticamente
        return Response({"message": "Entidad eliminada correctamente"}, status=status.HTTP_204_NO_CONTENT)


class EntityTreeAPIView(APIView):
    def get(self, request):
        type_labels = dict(Entity.TYPE_CHOICES)
        entities = list(
            Entity.objects.filter(deleted=False)
            .order_by('parent_id', 'name', 'id')
            .values('id', 'name', 'type', 'tag', 'parent_id')
        )

        nodes = {
            entity['id']: {
                'id': entity['id'],
                'name': entity['name'],
                'type': entity['type'],
                'type_name': type_labels.get(entity['type'], 'Unknown'),
                'tag': entity['tag'],
                'parent_id': entity['parent_id'],
                'children': [],
            }
            for entity in entities
        }

        roots = []
        for entity in entities:
            node = nodes[entity['id']]
            parent_id = entity['parent_id']

            if parent_id and parent_id != entity['id'] and parent_id in nodes:
                nodes[parent_id]['children'].append(node)
            else:
                roots.append(node)

        def sort_children(node):
            node['children'].sort(key=lambda child: (child['name'], child['id']))
            for child in node['children']:
                sort_children(child)

        roots.sort(key=lambda node: (node['name'], node['id']))
        for root in roots:
            sort_children(root)

        return Response(roots, status=status.HTTP_200_OK)


# ======================
#    AREAS & EQUIPMENTS
# ======================
class AreasAPIView(APIView):
    """Vista específica para listar solo áreas (type=2)"""
    # pagination_class = StandardResultsSetPagination
    
    def get(self, request):
        # Listar solo áreas no eliminadas
        areas = Entity.objects.filter(deleted=False, type=2)
        
        # Filtros opcionales
        parent_id = request.query_params.get('parent', None)
        if parent_id:
            if parent_id.lower() == 'null':
                areas = areas.filter(parent__isnull=True)
            else:
                areas = areas.filter(parent_id=parent_id)
        
        # Búsqueda por nombre o tag
        search = request.query_params.get('search', None)
        if search:
            areas = areas.filter(
                Q(name__icontains=search) |
                Q(tag__icontains=search)
            )
        
        # Ordenamiento (por defecto: por nombre)
        ordering = request.query_params.get('ordering', 'name')
        areas = areas.order_by(ordering)
        
        # Paginación
        # paginator = self.pagination_class()
        # page = paginator.paginate_queryset(areas, request)
        # if page is not None:
        #     serializer = EntitySerializer(page, many=True)
        #     return paginator.get_paginated_response(serializer.data)
        
        serializer = EntitySerializer(areas, many=True)
        return Response(serializer.data)


class EquipmentsAPIView(APIView):
    """Vista específica para listar solo equipos (type=4)"""
    # pagination_class = StandardResultsSetPagination
    
    def get(self, request):
        # Listar solo equipos no eliminados (con optimización para traer el parent)
        equipments = Entity.objects.filter(deleted=False, type__in=[4,5]).select_related('parent')
        
        # Filtros opcionales
        parent_id = request.query_params.get('parent', None)
        if parent_id:
            if parent_id.lower() == 'null':
                equipments = equipments.filter(parent__isnull=True)
            else:
                equipments = equipments.filter(parent_id=parent_id)
        
        # Búsqueda por nombre o tag
        search = request.query_params.get('search', None)
        if search:
            equipments = equipments.filter(
                Q(name__icontains=search) |
                Q(tag__icontains=search)
            )
        
        # Ordenamiento (por defecto: por id de ruta descendente, luego por nombre de equipo)
        ordering = request.query_params.get('ordering', None)
        if ordering:
            equipments = equipments.order_by(ordering)
        else:
            equipments = equipments.order_by('parent_id', 'name')
        
        # Paginación
        # paginator = self.pagination_class()
        # page = paginator.paginate_queryset(equipments, request)
        # if page is not None:
        #     serializer = EntitySerializer(page, many=True)
        #     return paginator.get_paginated_response(serializer.data)
        
        serializer = EntitySerializer(equipments, many=True)
        return Response(serializer.data)


# ======================
#        REPORT
# ======================
class NoticesByReportApiView(APIView):
    """Obtener avisos de un reporte específico"""
    # pagination_class = StandardResultsSetPagination
    
    def get(self, request, pk=None):
        # Obtener solo avisos no eliminados del reporte
        notices = Notice.objects.filter(report=pk, deleted=False)
        
        # Filtros adicionales opcionales
        status_filter = request.query_params.get('status', None)
        if status_filter:
            notices = notices.filter(status=status_filter)
        
        ot_status = request.query_params.get('ot_status', None)
        if ot_status:
            notices = notices.filter(ot_status=ot_status)
        
        # Ordenamiento (por defecto: más recientes primero)
        ordering = request.query_params.get('ordering', '-created_at')
        notices = notices.order_by(ordering)
        
        # Paginación
        # paginator = self.pagination_class()
        # page = paginator.paginate_queryset(notices, request)
        # if page is not None:
        #     notices_serialized = NoticeSerializer(page, many=True)
        #     return paginator.get_paginated_response(notices_serialized.data)
        
        notices_serialized = NoticeSerializer(notices, many=True)
        return Response(notices_serialized.data)


class ReportAPIView(APIView):
    # pagination_class = StandardResultsSetPagination
    
    def get(self, request, pk=None):
        if pk:
            # Obtener solo reportes no eliminados
            report = get_object_or_404(Report.objects.filter(deleted=False), pk=pk)
            serializer = ReportSerializer(report)
            return Response(serializer.data)
        else:
            # Listar solo reportes no eliminados
            reports = Report.objects.filter(deleted=False)
            
            # Filtros opcionales
            entity_id = request.query_params.get('entity', None)
            if entity_id:
                reports = reports.filter(entity_id=entity_id)
            
            work_type = request.query_params.get('work_type', None)
            if work_type:
                reports = reports.filter(work_type=work_type)
            
            service_type = request.query_params.get('service_type', None)
            if service_type:
                reports = reports.filter(service_type=service_type)
            
            condition = request.query_params.get('condition', None)
            if condition:
                reports = reports.filter(condition=condition)
            
            program = request.query_params.get('program', None)
            if program:
                reports = reports.filter(program=program)
            
            execution_status = request.query_params.get('execution_status', None)
            if execution_status:
                reports = reports.filter(execution_status=execution_status)
            
            is_active = request.query_params.get('is_active', None)
            if is_active is not None:
                reports = reports.filter(is_active=is_active.lower() in ['true', '1', 'yes'])
            
            # Búsqueda por múltiples campos
            search = request.query_params.get('search', None)
            if search:
                reports = reports.filter(
                    Q(name__icontains=search) |
                    Q(observations__icontains=search) |
                    Q(diagnostic__icontains=search) |
                    Q(recomendations__icontains=search)
                )
            
            # Ordenamiento (por defecto: más recientes primero)
            ordering = request.query_params.get('ordering', '-created_at')
            reports = reports.order_by(ordering)
            
            # Paginación
            # paginator = self.pagination_class()
            # page = paginator.paginate_queryset(reports, request)
            # if page is not None:
            #     serializer = ReportSerializer(page, many=True)
            #     return paginator.get_paginated_response(serializer.data)
            
            serializer = ReportSerializer(reports, many=True)
            return Response(serializer.data)

    def post(self, request):
        serializer = ReportSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user if request.user.is_authenticated else None)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk=None):
        # Solo actualizar reportes no eliminados
        report = get_object_or_404(Report.objects.filter(deleted=False), pk=pk)
        serializer = ReportSerializer(report, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None):
        # Eliminación lógica: solo marcar como eliminado
        report = get_object_or_404(Report.objects.filter(deleted=False), pk=pk)
        report.deleted = True
        report.save()  # La señal actualizará deleted_at automáticamente
        return Response({"message": "Reporte eliminado correctamente"}, status=status.HTTP_204_NO_CONTENT)


# ======================
#        NOTICE
# ======================
class NoticeAPIView(APIView):
    # pagination_class = StandardResultsSetPagination
    
    def get(self, request, pk=None):
        if pk:
            # Obtener solo avisos no eliminados
            notice = get_object_or_404(Notice.objects.filter(deleted=False), pk=pk)
            serializer = NoticeSerializer(notice)
            return Response(serializer.data)
        else:
            # Listar solo avisos no eliminados
            notices = Notice.objects.filter(deleted=False)
            
            # Filtros opcionales
            report_id = request.query_params.get('report', None)
            if report_id:
                notices = notices.filter(report_id=report_id)
            
            status_filter = request.query_params.get('status', None)
            if status_filter:
                notices = notices.filter(status=status_filter)
            
            ot_status = request.query_params.get('ot_status', None)
            if ot_status:
                notices = notices.filter(ot_status=ot_status)
            
            status_real = request.query_params.get('status_real', None)
            if status_real:
                notices = notices.filter(status_real=status_real)
            
            # Búsqueda por múltiples campos
            search = request.query_params.get('search', None)
            if search:
                notices = notices.filter(
                    Q(name__icontains=search) |
                    Q(ot_number__icontains=search) |
                    Q(comment__icontains=search)
                )
            
            # Ordenamiento (por defecto: más recientes primero)
            ordering = request.query_params.get('ordering', '-created_at')
            notices = notices.order_by(ordering)
            
            # Paginación
            # paginator = self.pagination_class()
            # page = paginator.paginate_queryset(notices, request)
            # if page is not None:
            #     serializer = NoticeSerializer(page, many=True)
            #     return paginator.get_paginated_response(serializer.data)
            
            serializer = NoticeSerializer(notices, many=True)
            return Response(serializer.data)

    def post(self, request):
        serializer = NoticeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user if request.user.is_authenticated else None)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk=None):
        # Solo actualizar avisos no eliminados
        notice = get_object_or_404(Notice.objects.filter(deleted=False), pk=pk)
        serializer = NoticeSerializer(notice, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None):
        # Eliminación lógica: solo marcar como eliminado
        notice = get_object_or_404(Notice.objects.filter(deleted=False), pk=pk)
        notice.deleted = True
        notice.save()  # La señal actualizará deleted_at automáticamente
        return Response({"message": "Aviso eliminado correctamente"}, status=status.HTTP_204_NO_CONTENT)


# ======================
#   ADDITIONAL VIEWS
# ======================
class EquipmentConditionSummaryAPIView(APIView):
    """Resumen de condiciones de equipos"""
    
    def get(self, request):
        # Subquery para obtener la última condición del equipo
        last_report = (
            Report.objects
            .filter(entity=OuterRef("pk"), deleted=False)
            .order_by("-created_at")
        )

        equipos = (
            Entity.objects
            .filter(type=4, deleted=False)
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
    """Condiciones de equipos por mes (últimos 7 meses)"""
    
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
        equipos = Entity.objects.filter(type=4, deleted=False)

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

class DashboardStatsAPIView(APIView):
    """
    Endpoint para obtener datos del dashboard filtrando por work_type (1=PDM, 2=NDT) y area (Entity ID).
    Retorna la estructura json agrupada por fechas y semanas.
    """
    
    def get(self, request):
        work_type = request.query_params.get('work_type', None)
        area_id = request.query_params.get('area', None)

        reports_qs = Report.objects.filter(deleted=False)
        notices_qs = Notice.objects.filter(deleted=False)

        if work_type:
            reports_qs = reports_qs.filter(work_type=work_type)

        if area_id:
            routes = Entity.objects.filter(parent_id=area_id, type=3)
            equipments = Entity.objects.filter(parent__in=routes, type=4)
            reports_qs = reports_qs.filter(entity__in=equipments)
            notices_qs = notices_qs.filter(report__entity__in=equipments)

        today = timezone.now().date()
        
        # Generar últimos 7 días
        last_7_days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
        # Generar últimas 7 semanas (inicio de semana)
        last_7_weeks = [(today - timedelta(days=today.weekday()) - timedelta(weeks=i)) for i in range(6, -1, -1)]

        meses_es = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

        def format_date(d):
            return f"{d.day}-{meses_es[d.month - 1]}"

        # 1. equipPie (Condition breakdown total)
        equip_pie = [
            {"name": "normal", "value": reports_qs.filter(condition=1).count(), "fill": "#4CAF50"},
            {"name": "tolerable", "value": reports_qs.filter(condition=2).count(), "fill": "#FFC107"},
            {"name": "precaucion", "value": reports_qs.filter(condition=3).count(), "fill": "#FF9800"},
            {"name": "critico", "value": reports_qs.filter(condition=4).count(), "fill": "#F44336"}
        ]

        # Estructuras para datos diarios
        cond_comp_percentage = []
        cumplimiento = []
        eq_monitoreo = []
        avisos_ot = []

        # Obtener total de equipos para calcular no monitoreados
        if area_id:
            total_eq = Entity.objects.filter(parent__in=Entity.objects.filter(parent_id=area_id, type=3), type=4).count()
        else:
            total_eq = Entity.objects.filter(type=4, deleted=False).count()

        for d in last_7_days:
            start_dt = timezone.datetime.combine(d, timezone.datetime.min.time(), tzinfo=timezone.get_current_timezone())
            end_dt = start_dt + timedelta(days=1)

            day_reports = reports_qs.filter(created_at__gte=start_dt, created_at__lt=end_dt)
            day_notices = notices_qs.filter(created_at__gte=start_dt, created_at__lt=end_dt)

            name_str = format_date(d)

            # condCompPercentage
            total_cond = day_reports.count()
            if total_cond > 0:
                cond_comp_percentage.append({
                    "name": name_str,
                    "normal": round(day_reports.filter(condition=1).count() / total_cond, 2),
                    "tolerable": round(day_reports.filter(condition=2).count() / total_cond, 2),
                    "precaucion": round(day_reports.filter(condition=3).count() / total_cond, 2),
                    "critico": round(day_reports.filter(condition=4).count() / total_cond, 2),
                })
            else:
                cond_comp_percentage.append({
                    "name": name_str,
                    "normal": 0, "tolerable": 0, "precaucion": 0, "critico": 0
                })

            # cumplimiento
            total_prog = day_reports.filter(program=1).count()
            exec_prog = day_reports.filter(program=1, execution_status=1).count()
            cumplimiento.append({
                "name": name_str,
                "value": round(exec_prog / total_prog, 2) if total_prog > 0 else 0
            })

            # eqMonitoreo
            mon = day_reports.filter(execution_status=1).values('entity').distinct().count()
            eq_monitoreo.append({
                "name": name_str,
                "mon": mon,
                "no_mon": total_eq - mon
            })

            # avisosOt
            avisos_ot.append({
                "name": name_str,
                "avisos": day_notices.filter(ot_number__isnull=True).count(),
                "ot": day_notices.filter(ot_number__isnull=False).count()
            })

        # 4. noProgramWorks (por semana)
        no_program_works = []
        for i, w_start in enumerate(last_7_weeks):
            w_start_dt = timezone.datetime.combine(w_start, timezone.datetime.min.time(), tzinfo=timezone.get_current_timezone())
            w_end_dt = w_start_dt + timedelta(days=7)
            
            w_reports = reports_qs.filter(created_at__gte=w_start_dt, created_at__lt=w_end_dt)
            no_program_works.append({
                "name": f"Sem. {i+1}",
                "value": w_reports.filter(program=2).count()
            })

        # 6. avisosOtCerrAb (Total acumulado, como en el JSON)
        ots_abiertos = notices_qs.filter(ot_number__isnull=False, ot_status=1).count()
        ots_cerrados = notices_qs.filter(ot_number__isnull=False, ot_status=2).count()
        avisos_abiertos = notices_qs.filter(ot_number__isnull=True, status=1).count()
        avisos_cerrados = notices_qs.filter(ot_number__isnull=True, status=2).count()

        avisos_ot_cerr_ab = [
            {"name": "OTs", "abierto": ots_abiertos, "cerrado": ots_cerrados},
            {"name": "Avisos", "abierto": avisos_abiertos, "cerrado": avisos_cerrados}
        ]

        data = {
            "status": "success",
            "message": "Dashboard data retrieved successfully",
            "data": {
                "equipPie": equip_pie,
                "condCompPercentage": cond_comp_percentage,
                "cumplimiento": cumplimiento,
                "eqMonitoreo": eq_monitoreo,
                "noProgramWorks": no_program_works,
                "avisosOt": avisos_ot,
                "avisosOtCerrAb": avisos_ot_cerr_ab
            }
        }

        return Response(data, status=status.HTTP_200_OK)
