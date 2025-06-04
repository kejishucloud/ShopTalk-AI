"""
应用管理模块序列化器
"""

from rest_framework import serializers
from .models import Application, AppConfig, AppCallback, AppAuth, AppStatistics


class ApplicationSerializer(serializers.ModelSerializer):
    """应用配置序列化器"""
    platform_display = serializers.CharField(source='get_platform_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Application
        fields = [
            'id', 'name', 'description', 'platform', 'platform_display',
            'app_id', 'app_secret', 'status', 'status_display', 'is_active',
            'created_at', 'updated_at', 'activated_at', 'last_callback_at',
            'created_by', 'created_by_name'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'activated_at', 'last_callback_at']
        extra_kwargs = {
            'app_secret': {'write_only': True}
        }
    
    def validate_app_id(self, value):
        """验证应用ID唯一性"""
        if self.instance and self.instance.app_id == value:
            return value
        
        if Application.objects.filter(app_id=value).exists():
            raise serializers.ValidationError("应用ID已存在")
        return value


class AppConfigSerializer(serializers.ModelSerializer):
    """应用配置详情序列化器"""
    app_name = serializers.CharField(source='app.name', read_only=True)
    config_type_display = serializers.CharField(source='get_config_type_display', read_only=True)
    
    class Meta:
        model = AppConfig
        fields = [
            'id', 'app', 'app_name', 'config_type', 'config_type_display',
            'config_key', 'config_value', 'is_encrypted', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        """验证配置键唯一性"""
        app = data.get('app')
        config_key = data.get('config_key')
        
        if app and config_key:
            queryset = AppConfig.objects.filter(app=app, config_key=config_key)
            if self.instance:
                queryset = queryset.exclude(id=self.instance.id)
            
            if queryset.exists():
                raise serializers.ValidationError({
                    'config_key': '该应用下配置键已存在'
                })
        
        return data


class AppCallbackSerializer(serializers.ModelSerializer):
    """应用回调记录序列化器"""
    app_name = serializers.CharField(source='app.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = AppCallback
        fields = [
            'id', 'app', 'app_name', 'method', 'headers', 'body', 'ip_address',
            'status', 'status_display', 'response_data', 'error_message',
            'created_at', 'processed_at'
        ]
        read_only_fields = ['id', 'created_at', 'processed_at']


class AppAuthSerializer(serializers.ModelSerializer):
    """应用认证配置序列化器"""
    app_name = serializers.CharField(source='app.name', read_only=True)
    auth_type_display = serializers.CharField(source='get_auth_type_display', read_only=True)
    
    class Meta:
        model = AppAuth
        fields = [
            'id', 'app', 'app_name', 'auth_type', 'auth_type_display',
            'auth_key', 'auth_value', 'is_active', 'extra_config',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'auth_value': {'write_only': True}
        }
    
    def validate(self, data):
        """验证认证类型唯一性"""
        app = data.get('app')
        auth_type = data.get('auth_type')
        
        if app and auth_type:
            queryset = AppAuth.objects.filter(app=app, auth_type=auth_type)
            if self.instance:
                queryset = queryset.exclude(id=self.instance.id)
            
            if queryset.exists():
                raise serializers.ValidationError({
                    'auth_type': '该应用下认证类型已存在'
                })
        
        return data


class AppStatisticsSerializer(serializers.ModelSerializer):
    """应用统计数据序列化器"""
    app_name = serializers.CharField(source='app.name', read_only=True)
    
    class Meta:
        model = AppStatistics
        fields = [
            'id', 'app', 'app_name', 'date',
            'message_count', 'session_count', 'user_count', 'error_count',
            'avg_response_time', 'max_response_time',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        """验证统计日期唯一性"""
        app = data.get('app')
        date = data.get('date')
        
        if app and date:
            queryset = AppStatistics.objects.filter(app=app, date=date)
            if self.instance:
                queryset = queryset.exclude(id=self.instance.id)
            
            if queryset.exists():
                raise serializers.ValidationError({
                    'date': '该应用在此日期的统计数据已存在'
                })
        
        return data 