"""
智能体管理模块序列化器
提供智能体相关数据的序列化和反序列化
"""

from rest_framework import serializers
from django.utils import timezone
from .models import Agent, AgentConfig, AgentExecution, AgentLog, AgentMetrics


class AgentConfigSerializer(serializers.ModelSerializer):
    """智能体配置序列化器"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = AgentConfig
        fields = ['id', 'name', 'config_data', 'description', 'is_active',
                 'created_by', 'created_by_name', 'created_at', 'updated_at']
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def validate_config_data(self, value):
        """验证配置数据格式"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("配置数据必须是字典格式")
        return value


class AgentSerializer(serializers.ModelSerializer):
    """智能体序列化器"""
    config_name = serializers.CharField(source='config.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    agent_type_display = serializers.CharField(source='get_agent_type_display', read_only=True)
    uptime_seconds = serializers.SerializerMethodField()
    success_rate = serializers.ReadOnlyField()
    
    class Meta:
        model = Agent
        fields = ['id', 'name', 'agent_type', 'agent_type_display', 'description',
                 'config', 'config_name', 'status', 'status_display', 'is_active',
                 'pid', 'started_at', 'last_execution_at', 'uptime_seconds',
                 'total_executions', 'successful_executions', 'failed_executions',
                 'success_rate', 'created_by', 'created_by_name', 'created_at', 'updated_at']
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'pid', 
                           'started_at', 'last_execution_at', 'total_executions',
                           'successful_executions', 'failed_executions']
    
    def get_uptime_seconds(self, obj):
        """获取运行时间（秒）"""
        uptime = obj.uptime
        return uptime.total_seconds() if uptime else None


class AgentExecutionSerializer(serializers.ModelSerializer):
    """智能体执行记录序列化器"""
    agent_name = serializers.CharField(source='agent.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    duration_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = AgentExecution
        fields = ['id', 'agent', 'agent_name', 'execution_id', 'input_data',
                 'output_data', 'status', 'status_display', 'error_message',
                 'started_at', 'completed_at', 'duration', 'duration_formatted']
        read_only_fields = ['execution_id', 'started_at', 'completed_at', 'duration']
    
    def get_duration_formatted(self, obj):
        """格式化执行时长"""
        if obj.duration:
            if obj.duration < 1:
                return f"{obj.duration * 1000:.0f}ms"
            elif obj.duration < 60:
                return f"{obj.duration:.2f}s"
            else:
                minutes = int(obj.duration // 60)
                seconds = obj.duration % 60
                return f"{minutes}m {seconds:.2f}s"
        return None


class AgentLogSerializer(serializers.ModelSerializer):
    """智能体日志序列化器"""
    agent_name = serializers.CharField(source='agent.name', read_only=True)
    execution_id = serializers.CharField(source='execution.execution_id', read_only=True)
    level_display = serializers.CharField(source='get_level_display', read_only=True)
    
    class Meta:
        model = AgentLog
        fields = ['id', 'agent', 'agent_name', 'execution', 'execution_id',
                 'level', 'level_display', 'message', 'extra_data', 'created_at']
        read_only_fields = ['created_at']


class AgentMetricsSerializer(serializers.ModelSerializer):
    """智能体指标序列化器"""
    agent_name = serializers.CharField(source='agent.name', read_only=True)
    
    class Meta:
        model = AgentMetrics
        fields = ['id', 'agent', 'agent_name', 'metrics_data', 'cpu_usage',
                 'memory_usage', 'requests_per_minute', 'average_response_time',
                 'error_rate', 'recorded_at']
        read_only_fields = ['recorded_at']


# 简化的序列化器
class AgentSimpleSerializer(serializers.ModelSerializer):
    """简化智能体序列化器"""
    agent_type_display = serializers.CharField(source='get_agent_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Agent
        fields = ['id', 'name', 'agent_type', 'agent_type_display', 
                 'status', 'status_display', 'is_active']


class AgentConfigSimpleSerializer(serializers.ModelSerializer):
    """简化配置序列化器"""
    
    class Meta:
        model = AgentConfig
        fields = ['id', 'name', 'description', 'is_active']


# 统计相关序列化器
class AgentStatisticsSerializer(serializers.Serializer):
    """智能体统计信息序列化器"""
    total_agents = serializers.IntegerField()
    running_agents = serializers.IntegerField()
    idle_agents = serializers.IntegerField()
    error_agents = serializers.IntegerField()
    total_executions_today = serializers.IntegerField()
    successful_executions_today = serializers.IntegerField()
    failed_executions_today = serializers.IntegerField()
    average_response_time = serializers.FloatField()
    success_rate = serializers.FloatField()


class AgentPerformanceSerializer(serializers.Serializer):
    """智能体性能统计序列化器"""
    agent_id = serializers.IntegerField()
    agent_name = serializers.CharField()
    executions_count = serializers.IntegerField()
    success_count = serializers.IntegerField()
    failure_count = serializers.IntegerField()
    success_rate = serializers.FloatField()
    average_duration = serializers.FloatField()
    last_execution = serializers.DateTimeField() 