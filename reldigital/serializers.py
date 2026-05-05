from rest_framework import serializers
from django.contrib.auth.models import Group
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, Entity, Report, Notice, NoticeImage


class LoginSerializer(TokenObtainPairSerializer):
    """Serializador personalizado para login con información del usuario en el token"""
    
    @classmethod
    def get_token(cls, user):
        """Sobrescribir para agregar claims customizados al token"""
        token = super().get_token(user)
        
        # Agregar información del usuario al token
        token['id'] = user.id
        token['username'] = user.username
        token['email'] = user.email
        token['name'] = user.name
        token['last_name'] = user.last_name
        token['code'] = user.code
        token['position'] = user.position
        token['short_name'] = user.short_name
        token['phone'] = user.phone or ""
        token['groups'] = list(user.groups.values_list('id', flat=True))
        token['is_staff'] = user.is_staff
        token['is_superuser'] = user.is_superuser
        token['is_active'] = user.is_active
        
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user

        data['code'] = 200
        data['user'] = {
            'id': user.id,
            'code': user.code,
            'name': user.name,
            'last_name': user.last_name,
            'username': user.username,
            'dui': user.dui,
            'short_name': user.short_name,
            'position': user.position,
            'email': user.email,
            'phone': user.phone,
            'extra_emails': user.extra_emails,
            'groups': list(user.groups.values_list('id', flat=True)),
            'deleted': user.deleted,
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
        }
        return data


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

    def to_internal_value(self, data):
        """
        Acepta `parent` (id u objeto con id) además de `parent_id` para mantener compatibilidad.
        """
        mutable_data = data.copy()

        if 'parent' in mutable_data and 'parent_id' not in mutable_data:
            parent_value = mutable_data.get('parent')

            if isinstance(parent_value, dict):
                parent_value = parent_value.get('id', None)

            if parent_value in ('', 'null', 'None'):
                parent_value = None

            mutable_data['parent_id'] = parent_value

        return super().to_internal_value(mutable_data)


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
