"""
AI模型管理序列化器
提供API数据序列化和反序列化
"""

from rest_framework import serializers
from .models import (
    AIModelProvider, AIModel, ModelCallRecord, ModelPerformance,
    ModelLoadBalancer, ModelWeight, ModelQuota
)


class AIModelProviderSerializer(serializers.ModelSerializer):
    """AI模型提供商序列化器"""
    
    class Meta:
        model = AIModelProvider
        fields = [
            'id', 'name', 'provider_type', 'description', 'base_url', 
            'api_version', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class AIModelSerializer(serializers.ModelSerializer):
    """AI模型序列化器"""
    provider_name = serializers.CharField(source='provider.name', read_only=True)
    provider_type = serializers.CharField(source='provider.provider_type', read_only=True)
    capabilities_display = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = AIModel
        fields = [
            'id', 'provider', 'provider_name', 'provider_type', 'name', 'model_id',
            'model_type', 'capabilities', 'capabilities_display', 'max_tokens', 
            'context_window', 'default_temperature', 'default_top_p',
            'input_price_per_1k', 'output_price_per_1k', 'is_active', 'priority',
            'rate_limit_rpm', 'rate_limit_tpm', 'daily_quota', 'additional_config',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
        extra_kwargs = {
            'api_key': {'write_only': True}
        }
    
    def get_capabilities_display(self, obj):
        return obj.get_capabilities_display()
    
    def validate_capabilities(self, value):
        """验证能力列表"""
        if not isinstance(value, list):
            raise serializers.ValidationError("能力必须是列表格式")
        
        valid_capabilities = [choice[0] for choice in AIModel.CAPABILITY_CHOICES]
        for capability in value:
            if capability not in valid_capabilities:
                raise serializers.ValidationError(f"无效的能力: {capability}")
        
        return value


class ModelCallRecordSerializer(serializers.ModelSerializer):
    """模型调用记录序列化器"""
    model_name = serializers.CharField(source='model.name', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = ModelCallRecord
        fields = [
            'id', 'model', 'model_name', 'session_id', 'user', 'user_name',
            'input_text', 'parameters', 'output_text', 'status', 'status_display',
            'error_message', 'input_tokens', 'output_tokens', 'total_tokens',
            'response_time', 'cost', 'request_id', 'ip_address', 'created_at'
        ]
        read_only_fields = ['total_tokens', 'cost', 'created_at']


class ModelPerformanceSerializer(serializers.ModelSerializer):
    """模型性能统计序列化器"""
    model_name = serializers.CharField(source='model.name', read_only=True)
    
    class Meta:
        model = ModelPerformance
        fields = [
            'id', 'model', 'model_name', 'date', 'total_calls', 'successful_calls',
            'failed_calls', 'total_input_tokens', 'total_output_tokens', 'total_tokens',
            'average_response_time', 'success_rate', 'total_cost', 'average_cost_per_call',
            'updated_at'
        ]
        read_only_fields = ['updated_at']


class ModelWeightSerializer(serializers.ModelSerializer):
    """模型权重序列化器"""
    model_name = serializers.CharField(source='model.name', read_only=True)
    
    class Meta:
        model = ModelWeight
        fields = [
            'id', 'load_balancer', 'model', 'model_name', 'weight', 
            'is_healthy', 'last_health_check'
        ]


class ModelLoadBalancerSerializer(serializers.ModelSerializer):
    """模型负载均衡序列化器"""
    model_weights = ModelWeightSerializer(source='modelweight_set', many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    strategy_display = serializers.CharField(source='get_strategy_display', read_only=True)
    
    class Meta:
        model = ModelLoadBalancer
        fields = [
            'id', 'name', 'strategy', 'strategy_display', 'enable_fallback',
            'max_retries', 'retry_delay', 'health_check_enabled', 'health_check_interval',
            'is_active', 'model_weights', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ModelQuotaSerializer(serializers.ModelSerializer):
    """模型配额序列化器"""
    model_name = serializers.CharField(source='model.name', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    quota_type_display = serializers.CharField(source='get_quota_type_display', read_only=True)
    usage_percentage = serializers.SerializerMethodField()
    is_exceeded = serializers.SerializerMethodField()
    
    class Meta:
        model = ModelQuota
        fields = [
            'id', 'model', 'model_name', 'user', 'user_name', 'quota_type',
            'quota_type_display', 'max_calls', 'max_tokens', 'max_cost',
            'used_calls', 'used_tokens', 'used_cost', 'usage_percentage',
            'is_exceeded', 'reset_at', 'last_reset', 'is_active', 'created_at'
        ]
        read_only_fields = ['used_calls', 'used_tokens', 'used_cost', 'last_reset', 'created_at']
    
    def get_usage_percentage(self, obj):
        return obj.get_usage_percentage()
    
    def get_is_exceeded(self, obj):
        return obj.is_exceeded()


class ModelCallRequestSerializer(serializers.Serializer):
    """模型调用请求序列化器"""
    model_id = serializers.IntegerField(help_text="模型ID")
    input_text = serializers.CharField(help_text="输入文本")
    temperature = serializers.FloatField(default=None, required=False, help_text="温度参数")
    max_tokens = serializers.IntegerField(default=None, required=False, help_text="最大Token数")
    top_p = serializers.FloatField(default=None, required=False, help_text="Top-p参数")
    session_id = serializers.CharField(default="", required=False, help_text="会话ID")
    additional_params = serializers.DictField(default=dict, required=False, help_text="额外参数")


class ModelCallResponseSerializer(serializers.Serializer):
    """模型调用响应序列化器"""
    success = serializers.BooleanField()
    output_text = serializers.CharField()
    input_tokens = serializers.IntegerField()
    output_tokens = serializers.IntegerField()
    total_tokens = serializers.IntegerField()
    response_time = serializers.FloatField()
    cost = serializers.DecimalField(max_digits=10, decimal_places=6)
    request_id = serializers.CharField()
    error_message = serializers.CharField(required=False)


class ModelComparisonSerializer(serializers.Serializer):
    """模型对比序列化器"""
    model_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="要对比的模型ID列表"
    )
    input_text = serializers.CharField(help_text="测试文本")
    parameters = serializers.DictField(default=dict, required=False, help_text="调用参数")


class ModelBenchmarkSerializer(serializers.Serializer):
    """模型基准测试序列化器"""
    model_id = serializers.IntegerField(help_text="模型ID")
    test_cases = serializers.ListField(
        child=serializers.CharField(),
        help_text="测试用例列表"
    )
    parameters = serializers.DictField(default=dict, required=False, help_text="调用参数")
    concurrent_requests = serializers.IntegerField(default=1, help_text="并发请求数") 