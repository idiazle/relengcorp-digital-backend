from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import OuterRef, Subquery, Q
from django.utils import timezone
from django.contrib.auth.models import Group
from datetime import timedelta
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from .models import User, Entity, Report, Notice
from .serializers import UserSerializer, EntitySerializer, ReportSerializer, NoticeSerializer, GroupSerializer


# ======================
#      PAGINATION
# ======================
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# ======================
#        USER
# ======================
class UserAPIView(APIView):
    pagination_class = StandardResultsSetPagination
    
    @extend_schema(
        tags=['Users'],
        operation_id='list_users',
        summary='Listar usuarios',
        description='Obtiene la lista de usuarios no eliminados con soporte para paginación, búsqueda, filtros y ordenamiento.',
        parameters=[
            OpenApiParameter(name='page', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description='Número de página'),
            OpenApiParameter(name='page_size', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description='Elementos por página (max: 100)'),
            OpenApiParameter(name='search', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description='Buscar en username, name, last_name, email, code, dui'),
            OpenApiParameter(name='position', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description='Filtrar por posición'),
            OpenApiParameter(name='ordering', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description='Campo para ordenar (ej: username, -created_at)', default='-created_at'),
        ],
        responses={200: UserSerializer(many=True)},
    )
    @extend_schema(
        tags=['Users'],
        operation_id='get_user',
        summary='Obtener usuario',
        description='Obtiene los detalles de un usuario específico por su ID.',
        responses={200: UserSerializer, 404: None},
    )
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
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(users, request)
            if page is not None:
                serializer = UserSerializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)
            
            serializer = UserSerializer(users, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=['Users'],
        operation_id='create_user',
        summary='Crear usuario',
        description='Crea un nuevo usuario en el sistema. La contraseña se hashea automáticamente.',
        request=UserSerializer,
        responses={201: UserSerializer, 400: None},
    )
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=['Users'],
        operation_id='update_user',
        summary='Actualizar usuario',
        description='Actualiza parcial o totalmente un usuario existente.',
        request=UserSerializer,
        responses={200: UserSerializer, 400: None, 404: None},
    )
    def put(self, request, pk=None):
        # Solo actualizar usuarios no eliminados
        user = get_object_or_404(User.objects.filter(deleted=False), pk=pk)
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=['Users'],
        operation_id='delete_user',
        summary='Eliminar usuario (soft delete)',
        description='Marca un usuario como eliminado sin eliminarlo físicamente. Solo establece deleted=true y deleted_at.',
        responses={204: None, 404: None},
    )
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
    
    @extend_schema(
        tags=['Users'],
        operation_id='list_groups',
        summary='Listar grupos disponibles',
        description='Obtiene la lista de grupos (roles) disponibles para asignar a usuarios.',
        responses={200: GroupSerializer(many=True)},
    )
    def get(self, request):
        """Listar todos los grupos disponibles"""
        groups = Group.objects.all().order_by('name')
        serializer = GroupSerializer(groups, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ======================
#       ENTITY
# ======================
class EntityAPIView(APIView):
    pagination_class = StandardResultsSetPagination
    
    @extend_schema(
        tags=['Entities'],
        operation_id='list_entities',
        summary='Listar entidades',
        description='Obtiene la lista de entidades no eliminadas. Las entidades son jerárquicas (plantas, áreas, rutas, equipos, items, componentes).',
        parameters=[
            OpenApiParameter(name='page', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description='Número de página'),
            OpenApiParameter(name='page_size', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description='Elementos por página (max: 100)'),
            OpenApiParameter(name='type', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description='Tipo de entidad (1=Planta, 2=Área, 3=Ruta, 4=Equipo, 5=Item, 6=Componente)'),
            OpenApiParameter(name='parent', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description='ID del padre o "null" para entidades raíz'),
            OpenApiParameter(name='search', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description='Buscar en name o tag'),
            OpenApiParameter(name='ordering', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description='Campo para ordenar (ej: name, -created_at)', default='-type, name'),
        ],
        responses={200: EntitySerializer(many=True)},
    )
    @extend_schema(
        tags=['Entities'],
        operation_id='get_entity',
        summary='Obtener entidad',
        description='Obtiene los detalles de una entidad específica por su ID.',
        responses={200: EntitySerializer, 404: None},
    )
    def get(self, request, pk=None):
        if pk:
            # Obtener solo entidades no eliminadas
            entity = get_object_or_404(Entity.objects.filter(deleted=False), pk=pk)
            serializer = EntitySerializer(entity)
            return Response(serializer.data)
        else:
            # Listar solo entidades no eliminadas
            entities = Entity.objects.filter(deleted=False)
            
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
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(entities, request)
            if page is not None:
                serializer = EntitySerializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)
            
            serializer = EntitySerializer(entities, many=True)
            return Response(serializer.data)

    @extend_schema(
        tags=['Entities'],
        operation_id='create_entity',
        summary='Crear entidad',
        description='Crea una nueva entidad (planta, área, ruta, equipo, item o componente). Puede ser jerárquica especificando un parent.',
        request=EntitySerializer,
        responses={201: EntitySerializer, 400: None},
    )
    def post(self, request):
        serializer = EntitySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user if request.user.is_authenticated else None)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=['Entities'],
        operation_id='update_entity',
        summary='Actualizar entidad',
        description='Actualiza parcial o totalmente una entidad existente.',
        request=EntitySerializer,
        responses={200: EntitySerializer, 400: None, 404: None},
    )
    def put(self, request, pk=None):
        # Solo actualizar entidades no eliminadas
        entity = get_object_or_404(Entity.objects.filter(deleted=False), pk=pk)
        serializer = EntitySerializer(entity, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=['Entities'],
        operation_id='delete_entity',
        summary='Eliminar entidad (soft delete)',
        description='Marca una entidad como eliminada sin eliminarla físicamente.',
        responses={204: None, 404: None},
    )
    def delete(self, request, pk=None):
        # Eliminación lógica: solo marcar como eliminado
        entity = get_object_or_404(Entity.objects.filter(deleted=False), pk=pk)
        entity.deleted = True
        entity.save()  # La señal actualizará deleted_at automáticamente
        return Response({"message": "Entidad eliminada correctamente"}, status=status.HTTP_204_NO_CONTENT)


# ======================
#    AREAS & EQUIPMENTS
# ======================
class AreasAPIView(APIView):
    """Vista específica para listar solo áreas (type=2)"""
    pagination_class = StandardResultsSetPagination
    
    @extend_schema(
        tags=['Entities'],
        operation_id='list_areas',
        summary='Listar áreas',
        description='Obtiene la lista de áreas (type=2) no eliminadas.',
        parameters=[
            OpenApiParameter(name='page', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description='Número de página'),
            OpenApiParameter(name='page_size', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description='Elementos por página (max: 100)'),
            OpenApiParameter(name='parent', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description='ID del padre (planta) o "null"'),
            OpenApiParameter(name='search', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description='Buscar en name o tag'),
            OpenApiParameter(name='ordering', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description='Campo para ordenar', default='name'),
        ],
        responses={200: EntitySerializer(many=True)},
    )
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
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(areas, request)
        if page is not None:
            serializer = EntitySerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = EntitySerializer(areas, many=True)
        return Response(serializer.data)


class EquipmentsAPIView(APIView):
    """Vista específica para listar solo equipos (type=4)"""
    pagination_class = StandardResultsSetPagination
    
    @extend_schema(
        tags=['Entities'],
        operation_id='list_equipments',
        summary='Listar equipos',
        description='Obtiene la lista de equipos (type=4) no eliminados.',
        parameters=[
            OpenApiParameter(name='page', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description='Número de página'),
            OpenApiParameter(name='page_size', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description='Elementos por página (max: 100)'),
            OpenApiParameter(name='parent', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description='ID del padre (ruta) o "null"'),
            OpenApiParameter(name='search', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description='Buscar en name o tag'),
            OpenApiParameter(name='ordering', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description='Campo para ordenar (ej: name, -created_at)', default='parent_id, name'),
        ],
        responses={200: EntitySerializer(many=True)},
    )
    def get(self, request):
        # Listar solo equipos no eliminados (con optimización para traer el parent)
        equipments = Entity.objects.filter(deleted=False, type=4).select_related('parent')
        
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
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(equipments, request)
        if page is not None:
            serializer = EntitySerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = EntitySerializer(equipments, many=True)
        return Response(serializer.data)


# ======================
#        REPORT
# ======================
class NoticesByReportApiView(APIView):
    """Obtener avisos de un reporte específico"""
    pagination_class = StandardResultsSetPagination
    
    @extend_schema(
        tags=['Notices'],
        operation_id='list_notices_by_report',
        summary='Listar avisos de un reporte',
        description='Obtiene todos los avisos asociados a un reporte específico.',
        parameters=[
            OpenApiParameter(name='pk', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description='ID del reporte', required=True),
            OpenApiParameter(name='page', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description='Número de página'),
            OpenApiParameter(name='page_size', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description='Elementos por página (max: 100)'),
            OpenApiParameter(name='status', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description='Filtrar por estado'),
            OpenApiParameter(name='ot_status', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description='Filtrar por estado de OT'),
            OpenApiParameter(name='ordering', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description='Campo para ordenar', default='-created_at'),
        ],
        responses={200: NoticeSerializer(many=True)},
    )
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
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(notices, request)
        if page is not None:
            notices_serialized = NoticeSerializer(page, many=True)
            return paginator.get_paginated_response(notices_serialized.data)
        
        notices_serialized = NoticeSerializer(notices, many=True)
        return Response(notices_serialized.data)


class ReportAPIView(APIView):
    pagination_class = StandardResultsSetPagination
    
    @extend_schema(
        tags=['Reports'],
        operation_id='list_reports',
        summary='Listar reportes',
        description='Obtiene la lista de reportes de mantenimiento no eliminados con múltiples filtros disponibles.',
        parameters=[
            OpenApiParameter(name='page', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description='Número de página'),
            OpenApiParameter(name='page_size', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description='Elementos por página (max: 100)'),
            OpenApiParameter(name='entity', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description='ID de la entidad (equipo)'),
            OpenApiParameter(name='work_type', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description='Tipo de trabajo'),
            OpenApiParameter(name='service_type', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description='Tipo de servicio'),
            OpenApiParameter(name='condition', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description='Condición del equipo'),
            OpenApiParameter(name='program', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description='Programa de mantenimiento'),
            OpenApiParameter(name='execution_status', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description='Estado de ejecución'),
            OpenApiParameter(name='is_active', type=OpenApiTypes.BOOL, location=OpenApiParameter.QUERY, description='Si es el reporte activo del equipo'),
            OpenApiParameter(name='search', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description='Buscar en name, observations, diagnostic, recomendations'),
            OpenApiParameter(name='ordering', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description='Campo para ordenar (ej: -execution_date)', default='-created_at'),
        ],
        responses={200: ReportSerializer(many=True)},
    )
    @extend_schema(
        tags=['Reports'],
        operation_id='get_report',
        summary='Obtener reporte',
        description='Obtiene los detalles de un reporte específico con información de la entidad asociada.',
        responses={200: ReportSerializer, 404: None},
    )
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
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(reports, request)
            if page is not None:
                serializer = ReportSerializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)
            
            serializer = ReportSerializer(reports, many=True)
            return Response(serializer.data)

    @extend_schema(
        tags=['Reports'],
        operation_id='create_report',
        summary='Crear reporte',
        description='Crea un nuevo reporte de mantenimiento. Si is_active=true, desactiva otros reportes del mismo equipo automáticamente.',
        request=ReportSerializer,
        responses={201: ReportSerializer, 400: None},
    )
    def post(self, request):
        serializer = ReportSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user if request.user.is_authenticated else None)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=['Reports'],
        operation_id='update_report',
        summary='Actualizar reporte',
        description='Actualiza parcial o totalmente un reporte de mantenimiento existente.',
        request=ReportSerializer,
        responses={200: ReportSerializer, 400: None, 404: None},
    )
    def put(self, request, pk=None):
        # Solo actualizar reportes no eliminados
        report = get_object_or_404(Report.objects.filter(deleted=False), pk=pk)
        serializer = ReportSerializer(report, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=['Reports'],
        operation_id='delete_report',
        summary='Eliminar reporte (soft delete)',
        description='Marca un reporte como eliminado sin eliminarlo físicamente. No elimina el archivo adjunto.',
        responses={204: None, 404: None},
    )
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
    pagination_class = StandardResultsSetPagination
    
    @extend_schema(
        tags=['Notices'],
        operation_id='list_notices',
        summary='Listar avisos',
        description='Obtiene la lista de avisos y órdenes de trabajo no eliminados.',
        parameters=[
            OpenApiParameter(name='page', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description='Número de página'),
            OpenApiParameter(name='page_size', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description='Elementos por página (max: 100)'),
            OpenApiParameter(name='report', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description='ID del reporte'),
            OpenApiParameter(name='status', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description='Estado del aviso'),
            OpenApiParameter(name='ot_status', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description='Estado de la orden de trabajo'),
            OpenApiParameter(name='status_real', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description='Estado real'),
            OpenApiParameter(name='search', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description='Buscar en name, ot_number, comment'),
            OpenApiParameter(name='ordering', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description='Campo para ordenar', default='-created_at'),
        ],
        responses={200: NoticeSerializer(many=True)},
    )
    @extend_schema(
        tags=['Notices'],
        operation_id='get_notice',
        summary='Obtener aviso',
        description='Obtiene los detalles de un aviso específico con sus imágenes asociadas.',
        responses={200: NoticeSerializer, 404: None},
    )
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
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(notices, request)
            if page is not None:
                serializer = NoticeSerializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)
            
            serializer = NoticeSerializer(notices, many=True)
            return Response(serializer.data)

    @extend_schema(
        tags=['Notices'],
        operation_id='create_notice',
        summary='Crear aviso',
        description='Crea un nuevo aviso u orden de trabajo con soporte para múltiples imágenes.',
        request=NoticeSerializer,
        responses={201: NoticeSerializer, 400: None},
    )
    def post(self, request):
        serializer = NoticeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user if request.user.is_authenticated else None)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=['Notices'],
        operation_id='update_notice',
        summary='Actualizar aviso',
        description='Actualiza parcial o totalmente un aviso u orden de trabajo existente.',
        request=NoticeSerializer,
        responses={200: NoticeSerializer, 400: None, 404: None},
    )
    def put(self, request, pk=None):
        # Solo actualizar avisos no eliminados
        notice = get_object_or_404(Notice.objects.filter(deleted=False), pk=pk)
        serializer = NoticeSerializer(notice, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=['Notices'],
        operation_id='delete_notice',
        summary='Eliminar aviso (soft delete)',
        description='Marca un aviso como eliminado sin eliminarlo físicamente.',
        responses={204: None, 404: None},
    )
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
    
    @extend_schema(
        tags=['Analytics'],
        operation_id='equipment_condition_summary',
        summary='Resumen de condiciones de equipos',
        description='Obtiene un resumen del conteo de equipos según su última condición reportada (C1, C2, C3, C4).',
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'c1': {'type': 'integer', 'description': 'Cantidad de equipos en condición 1'},
                    'c2': {'type': 'integer', 'description': 'Cantidad de equipos en condición 2'},
                    'c3': {'type': 'integer', 'description': 'Cantidad de equipos en condición 3'},
                    'c4': {'type': 'integer', 'description': 'Cantidad de equipos en condición 4'},
                }
            }
        },
    )
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
    
    @extend_schema(
        tags=['Analytics'],
        operation_id='equipment_condition_by_month',
        summary='Condiciones de equipos por mes',
        description='Obtiene el conteo de equipos por condición (C1-C4) para cada uno de los últimos 7 meses.',
        responses={
            200: {
                'type': 'object',
                'description': 'Mapa de meses con conteo de condiciones',
                'additionalProperties': {
                    'type': 'object',
                    'properties': {
                        'c1': {'type': 'integer'},
                        'c2': {'type': 'integer'},
                        'c3': {'type': 'integer'},
                        'c4': {'type': 'integer'},
                    }
                }
            }
        },
    )
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
