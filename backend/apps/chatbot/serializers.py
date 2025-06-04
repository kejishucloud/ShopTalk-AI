"""
智能客服聊天机器人序列化器
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import ChatbotConfig, ChatSession, HumanHandoff, ChatStatistics, AgentPerformance


class UserSerializer(serializers.ModelSerializer):
    """用户序列化器"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class ChatbotConfigSerializer(serializers.ModelSerializer):
    """聊天机器人配置序列化器"""
    
    platform_display = serializers.CharField(source='get_platform_display', read_only=True)
    primary_agent_name = serializers.CharField(source='primary_agent.name', read_only=True)
    fallback_agent_name = serializers.CharField(source='fallback_agent.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = ChatbotConfig
        fields = [
            'id', 'name', 'description', 'platform', 'platform_display',
            'welcome_message', 'default_response', 'max_session_duration',
            'primary_agent', 'primary_agent_name', 'fallback_agent', 'fallback_agent_name',
            'auto_handoff_enabled', 'handoff_keywords', 'handoff_threshold',
            'is_active', 'created_at', 'updated_at', 'created_by', 'created_by_username'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_handoff_threshold(self, value):
        """验证转人工阈值"""
        if not 0 <= value <= 1:
            raise serializers.ValidationError("转人工阈值必须在0-1之间")
        return value
    
    def validate_max_session_duration(self, value):
        """验证最大会话时长"""
        if value < 60:
            raise serializers.ValidationError("最大会话时长不能少于60秒")
        if value > 86400:  # 24小时
            raise serializers.ValidationError("最大会话时长不能超过24小时")
        return value


class ChatSessionSerializer(serializers.ModelSerializer):
    """聊天会话序列化器"""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    user_info_display = serializers.SerializerMethodField()
    config_name = serializers.CharField(source='config.name', read_only=True)
    assigned_agent_name = serializers.CharField(source='assigned_agent.name', read_only=True)
    is_active_session = serializers.BooleanField(source='is_active', read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = [
            'id', 'platform', 'app_name', 'platform_user_id',
            'user', 'config', 'config_name', 'assigned_agent', 'assigned_agent_name',
            'status', 'status_display', 'message_count', 'last_message_at',
            'session_data', 'user_info', 'user_info_display',
            'created_at', 'updated_at', 'ended_at', 'is_active_session', 'duration'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'message_count']
    
    def get_user_info_display(self, obj):
        """获取用户信息显示"""
        if obj.user:
            return {
                'username': obj.user.username,
                'name': f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
            }
        return obj.user_info
    
    def get_duration(self, obj):
        """获取会话持续时间（秒）"""
        if obj.ended_at:
            return (obj.ended_at - obj.created_at).total_seconds()
        elif obj.last_message_at:
            return (obj.last_message_at - obj.created_at).total_seconds()
        return 0


class HumanHandoffSerializer(serializers.ModelSerializer):
    """人工接入序列化器"""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    trigger_reason_display = serializers.CharField(source='get_trigger_reason_display', read_only=True)
    
    session_info = serializers.SerializerMethodField()
    triggered_by_info = serializers.SerializerMethodField()
    assigned_agent_info = serializers.SerializerMethodField()
    
    waiting_time_seconds = serializers.ReadOnlyField(source='waiting_time')
    handling_time_seconds = serializers.ReadOnlyField(source='handling_time')
    
    class Meta:
        model = HumanHandoff
        fields = [
            'id', 'session', 'session_info',
            'trigger_reason', 'trigger_reason_display', 'trigger_message', 'trigger_context',
            'status', 'status_display', 'priority', 'priority_display',
            'triggered_by', 'triggered_by_info', 'assigned_agent', 'assigned_agent_info',
            'resolution_notes', 'customer_satisfaction',
            'created_at', 'assigned_at', 'started_at', 'completed_at',
            'waiting_time_seconds', 'handling_time_seconds'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_session_info(self, obj):
        """获取会话信息"""
        return {
            'id': str(obj.session.id),
            'platform': obj.session.platform,
            'platform_user_id': obj.session.platform_user_id,
            'status': obj.session.status
        }
    
    def get_triggered_by_info(self, obj):
        """获取触发者信息"""
        if obj.triggered_by:
            return {
                'id': obj.triggered_by.id,
                'username': obj.triggered_by.username,
                'name': f"{obj.triggered_by.first_name} {obj.triggered_by.last_name}".strip()
            }
        return None
    
    def get_assigned_agent_info(self, obj):
        """获取分配客服信息"""
        if obj.assigned_agent:
            return {
                'id': obj.assigned_agent.id,
                'username': obj.assigned_agent.username,
                'name': f"{obj.assigned_agent.first_name} {obj.assigned_agent.last_name}".strip()
            }
        return None
    
    def validate_customer_satisfaction(self, value):
        """验证客户满意度"""
        if value is not None and not 1 <= value <= 5:
            raise serializers.ValidationError("客户满意度必须在1-5之间")
        return value


class ChatStatisticsSerializer(serializers.ModelSerializer):
    """聊天统计序列化器"""
    
    # 计算字段
    bot_success_rate_percent = serializers.SerializerMethodField()
    handoff_rate = serializers.SerializerMethodField()
    avg_messages_per_session = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatStatistics
        fields = [
            'id', 'date', 'platform',
            'total_sessions', 'active_sessions', 'completed_sessions',
            'total_messages', 'bot_messages', 'user_messages', 'human_messages',
            'handoff_requests', 'handoff_completed', 'avg_handoff_wait_time', 'avg_handoff_handle_time',
            'satisfaction_ratings', 'avg_satisfaction',
            'bot_success_rate', 'bot_success_rate_percent', 'avg_response_time',
            'handoff_rate', 'avg_messages_per_session',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_bot_success_rate_percent(self, obj):
        """获取机器人成功率百分比"""
        return round(obj.bot_success_rate * 100, 2)
    
    def get_handoff_rate(self, obj):
        """获取人工接入率"""
        if obj.total_sessions > 0:
            return round((obj.handoff_requests / obj.total_sessions) * 100, 2)
        return 0
    
    def get_avg_messages_per_session(self, obj):
        """获取平均每会话消息数"""
        if obj.total_sessions > 0:
            return round(obj.total_messages / obj.total_sessions, 2)
        return 0


class AgentPerformanceSerializer(serializers.ModelSerializer):
    """智能体性能序列化器"""
    
    agent_name = serializers.CharField(source='agent.name', read_only=True)
    agent_type = serializers.CharField(source='agent.agent_type', read_only=True)
    
    success_rate_percent = serializers.ReadOnlyField(source='success_rate')
    error_rate_percent = serializers.ReadOnlyField(source='error_rate')
    
    # 性能等级
    performance_grade = serializers.SerializerMethodField()
    
    class Meta:
        model = AgentPerformance
        fields = [
            'id', 'agent', 'agent_name', 'agent_type', 'date',
            'total_requests', 'successful_requests', 'failed_requests',
            'avg_response_time', 'max_response_time', 'min_response_time',
            'accuracy_score', 'confidence_avg',
            'cpu_usage_avg', 'memory_usage_avg',
            'timeout_count', 'error_count',
            'success_rate_percent', 'error_rate_percent', 'performance_grade',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_performance_grade(self, obj):
        """获取性能等级"""
        success_rate = obj.success_rate
        avg_response_time = obj.avg_response_time
        
        if success_rate >= 95 and avg_response_time <= 500:
            return 'A'
        elif success_rate >= 90 and avg_response_time <= 1000:
            return 'B'
        elif success_rate >= 80 and avg_response_time <= 2000:
            return 'C'
        elif success_rate >= 70:
            return 'D'
        else:
            return 'F'


class ChatbotConfigCreateSerializer(serializers.ModelSerializer):
    """聊天机器人配置创建序列化器"""
    
    class Meta:
        model = ChatbotConfig
        fields = [
            'name', 'description', 'platform',
            'welcome_message', 'default_response', 'max_session_duration',
            'primary_agent', 'fallback_agent',
            'auto_handoff_enabled', 'handoff_keywords', 'handoff_threshold',
            'is_active'
        ]
    
    def create(self, validated_data):
        """创建配置时设置创建者"""
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class HumanHandoffCreateSerializer(serializers.ModelSerializer):
    """人工接入创建序列化器"""
    
    class Meta:
        model = HumanHandoff
        fields = [
            'session', 'trigger_reason', 'trigger_message', 'trigger_context',
            'priority'
        ]
    
    def create(self, validated_data):
        """创建人工接入时设置触发者"""
        request = self.context.get('request')
        if request and request.user:
            validated_data['triggered_by'] = request.user
        return super().create(validated_data) 