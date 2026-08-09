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
