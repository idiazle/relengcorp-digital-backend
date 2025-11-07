from rest_framework import serializers
from reldigital.models import User, Entity, Report, Notice, NoticeImage


class UserSerializer(serializers.ModelSerializer):
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
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user


class EntitySerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Entity.objects.all(), allow_null=True, required=False
    )
    children = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Entity
        fields = [
            'id',
            'name',
            'type',
            'attachment',
            'parent',
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
            'extra_info': {'required': False, 'allow_null': True},
            'attachment': {'required': False, 'allow_null': True},
        }


class ReportSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    entity = serializers.PrimaryKeyRelatedField(
        queryset=Entity.objects.all(), allow_null=True, required=False
    )

    class Meta:
        model = Report
        fields = [
            'id',
            'entity',
            'program',
            'task_type',
            'execution_status',
            'observations',
            'condition',
            'diagnostic',
            'recomendations',
            'created_by',
            'deleted',
            'created_at',
            'deleted_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'deleted_at']
        extra_kwargs = {
            'attachment': {'required': False, 'allow_null': True},
            'name': {'required': False, 'allow_null': True, 'allow_blank': True},
            'observations': {'required': False, 'allow_null': True, 'allow_blank': True},
            'execution_date': {'required': False, 'allow_null': True, 'allow_blank': True},
            'diagnostic': {'required': False, 'allow_null': True},
            'recomendations': {'required': False, 'allow_null': True},
        }

class NoticeImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoticeImage
        fields = ['id', 'image']
        
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
