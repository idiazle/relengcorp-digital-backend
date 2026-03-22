from rest_framework import serializers
from django.contrib.auth.models import Group
from .models import User, Entity, Report, Notice, NoticeImage


class GroupSerializer(serializers.ModelSerializer):
    """Serializer para listar grupos disponibles"""
    class Meta:
        model = Group
        fields = ['id', 'name']


class UserSerializer(serializers.ModelSerializer):
    groups = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Group.objects.all(),
        required=False
    )
    
    class Meta:
        model = User
        fields = [
            'id',
            'code',
            'name',
            'last_name',
            'username',
            'dui',
            'short_name',
            'position',
            'email',
            'password',
            'phone',
            'extra_emails',
            'groups',  # Array de IDs de grupos
            'deleted',
            'created_at',
            'updated_at',
            'deleted_at',
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
            'deleted_at': {'read_only': True},
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        groups = validated_data.pop('groups', [])
        
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        
        # Asignar grupos usando los IDs
        if groups:
            user.groups.set(groups)
        
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        groups = validated_data.pop('groups', None)
        
        # Actualizar campos básicos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Actualizar contraseña si se proporciona
        if password:
            instance.set_password(password)
        
        instance.save()
        
        # Actualizar grupos si se proporcionan (usando IDs)
        if groups is not None:
            instance.groups.set(groups)
        
        return instance



class EntityParentSerializer(serializers.ModelSerializer):
    """Serializer simplificado para mostrar información del parent"""
    class Meta:
        model = Entity
        fields = ['id', 'name', 'tag']


class EntityChildrenSerializer(serializers.ModelSerializer):
    """Serializer simplificado para mostrar información de los children"""
    class Meta:
        model = Entity
        fields = ['id', 'name']


class EntitySerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    parent = EntityParentSerializer(read_only=True)
    parent_id = serializers.PrimaryKeyRelatedField(
        queryset=Entity.objects.all(), 
        allow_null=True, 
        required=False,
        source='parent',
        write_only=True
    )
    children = EntityChildrenSerializer(many=True, read_only=True)

    class Meta:
        model = Entity
        fields = [
            'id',
            'name',
            'type',
            'tag',
            'attachment',
            'parent',
            'parent_id',
            'children',
            'created_by',
            'extra_info',
            'deleted',
            'created_at',
            'deleted_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'deleted_at']
        extra_kwargs = {
            'name': {'required': True},
            'type': {'required': True},
            'tag': {'required': True},
            'attachment': {'required': False, 'allow_null': True, 'use_url': True},
            'extra_info': {'required': False, 'allow_null': True},
        }


class ReportSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    entity = serializers.PrimaryKeyRelatedField(
        queryset=Entity.objects.all(), allow_null=True, required=False
    )
    parents = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = [
            'id',
            'entity',
            'parents',
            'name',
            'execution_date',
            'program',
            'service_type',
            'work_type',
            'execution_status',
            'observations',
            'condition',
            'attachment',
            'diagnostic',
            'recomendations',
            'created_by',
            'is_active',
            'deleted',
            'created_at',
            'deleted_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'deleted_at', 'parents']
        extra_kwargs = {
            'attachment': {'required': False, 'allow_null': True, 'use_url': True},
            'name': {'required': False, 'allow_null': True, 'allow_blank': True},
            'service_type': {'required': False, 'allow_null': True},
            'work_type': {'required': False, 'allow_null': True},
            'observations': {'required': False, 'allow_null': True, 'allow_blank': True},
            'execution_date': {'required': False, 'allow_null': True},
            'diagnostic': {'required': False, 'allow_null': True},
            'recomendations': {'required': False, 'allow_null': True},
            'is_active': {'required': False, 'default': True},
        }
    
    def get_parents(self, obj):
        """Obtiene la lista de padres de la entidad asociada al reporte"""
        if obj.entity:
            hierarchy = obj.entity.get_hierarchy()
            return hierarchy.get('parents', [])
        return []


class NoticeImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoticeImage
        fields = ['id', 'image']
        extra_kwargs = {
            'image': {'use_url': True},
        }


class NoticeSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    images = NoticeImageSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = Notice
        exclude = ['created_at', 'updated_at', 'deleted_at', 'deleted']
        read_only_fields = ['created_at', 'updated_at', 'deleted_at']
        extra_kwargs = {
            'ot_number': {'required': False, 'allow_null': True},
            'ot_date': {'required': False, 'allow_null': True},
            'comment': {'required': False, 'allow_null': True}
        }

    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        notice = Notice.objects.create(**validated_data)

        for image_data in images_data:
            NoticeImage.objects.create(notice=notice, **image_data)

        return notice
