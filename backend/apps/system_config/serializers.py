from rest_framework import serializers
from .models import ConfigCategory, SystemConfig, ConfigGroup


class ConfigCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfigCategory
        fields = ['id', 'name', 'display_name', 'description', 'order', 'is_active']


class ConfigGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfigGroup
        fields = ['id', 'name', 'display_name', 'description', 'order', 'is_collapsible', 'is_expanded']


class SystemConfigSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.display_name', read_only=True)
    group_name = serializers.CharField(source='group.display_name', read_only=True, allow_null=True)
    parsed_value = serializers.SerializerMethodField()
    
    class Meta:
        model = SystemConfig
        fields = [
            'id', 'key', 'display_name', 'description', 'config_type', 
            'value', 'parsed_value', 'default_value', 'choices', 
            'is_required', 'is_encrypted', 'order', 'is_active',
            'category', 'category_name', 'group', 'group_name',
            'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'value': {'write_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True}
        }

    def get_parsed_value(self, obj):
        """获取解析后的配置值"""
        if obj.is_encrypted and obj.value:
            # 对于加密字段，返回掩码
            return '***' * (len(obj.value) // 3 + 1)
        return obj.get_value()

    def validate_value(self, value):
        """验证配置值"""
        config_type = self.initial_data.get('config_type', 'string')
        
        if config_type == 'integer':
            try:
                int(value)
            except ValueError:
                raise serializers.ValidationError("必须是整数")
        elif config_type == 'float':
            try:
                float(value)
            except ValueError:
                raise serializers.ValidationError("必须是浮点数")
        elif config_type == 'boolean':
            if str(value).lower() not in ('true', 'false', '1', '0', 'yes', 'no', 'on', 'off'):
                raise serializers.ValidationError("必须是布尔值")
        elif config_type == 'json':
            try:
                import json
                json.loads(value)
            except json.JSONDecodeError:
                raise serializers.ValidationError("必须是有效的JSON格式")
        elif config_type == 'email':
            from django.core.validators import validate_email
            from django.core.exceptions import ValidationError
            try:
                validate_email(value)
            except ValidationError:
                raise serializers.ValidationError("必须是有效的邮箱地址")
        elif config_type == 'url':
            from django.core.validators import URLValidator
            from django.core.exceptions import ValidationError
            try:
                URLValidator()(value)
            except ValidationError:
                raise serializers.ValidationError("必须是有效的URL")
        
        return value


class ConfigCategoryDetailSerializer(serializers.ModelSerializer):
    """配置分类详情序列化器，包含分组和配置项"""
    groups = serializers.SerializerMethodField()
    ungrouped_configs = serializers.SerializerMethodField()
    
    class Meta:
        model = ConfigCategory
        fields = ['id', 'name', 'display_name', 'description', 'order', 'is_active', 'groups', 'ungrouped_configs']
    
    def get_groups(self, obj):
        """获取该分类下的所有配置组"""
        groups = ConfigGroup.objects.filter(category=obj).prefetch_related('systemconfig_set')
        result = []
        
        for group in groups:
            configs = SystemConfig.objects.filter(group=group, is_active=True)
            group_data = ConfigGroupSerializer(group).data
            group_data['configs'] = SystemConfigSerializer(configs, many=True).data
            result.append(group_data)
        
        return result
    
    def get_ungrouped_configs(self, obj):
        """获取该分类下未分组的配置项"""
        configs = SystemConfig.objects.filter(category=obj, group__isnull=True, is_active=True)
        return SystemConfigSerializer(configs, many=True).data


class ConfigUpdateSerializer(serializers.Serializer):
    """批量更新配置的序列化器"""
    configs = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        )
    )
    
    def validate_configs(self, value):
        """验证配置更新数据"""
        for config_data in value:
            if 'key' not in config_data or 'value' not in config_data:
                raise serializers.ValidationError("每个配置项必须包含key和value")
        return value 