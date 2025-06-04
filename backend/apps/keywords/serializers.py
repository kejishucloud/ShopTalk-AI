"""
关键词管理模块序列化器
"""

from rest_framework import serializers
from .models import KeywordCategory, Keyword, KeywordRule, KeywordMatch, KeywordStatistics


class KeywordCategorySerializer(serializers.ModelSerializer):
    """关键词分类序列化器"""
    category_type_display = serializers.CharField(source='get_category_type_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    keyword_count = serializers.SerializerMethodField()
    
    class Meta:
        model = KeywordCategory
        fields = [
            'id', 'name', 'description', 'category_type', 'category_type_display',
            'priority', 'is_active', 'keyword_count',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_keyword_count(self, obj):
        """获取该分类下的关键词数量"""
        return obj.keyword_set.filter(is_active=True).count()


class KeywordSerializer(serializers.ModelSerializer):
    """关键词序列化器"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    keyword_type_display = serializers.CharField(source='get_keyword_type_display', read_only=True)
    priority_level_display = serializers.CharField(source='get_priority_level_display', read_only=True)
    match_type_display = serializers.CharField(source='get_match_type_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Keyword
        fields = [
            'id', 'word', 'category', 'category_name', 'keyword_type', 'keyword_type_display',
            'description', 'tags', 'is_active', 'match_type', 'match_type_display',
            'weight', 'priority_level', 'priority_level_display',
            'auto_response', 'trigger_handoff',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_word(self, value):
        """验证关键词"""
        if not value or not value.strip():
            raise serializers.ValidationError("关键词不能为空")
        
        # 检查重复
        category = self.initial_data.get('category')
        if category:
            queryset = Keyword.objects.filter(word=value.strip(), category=category)
            if self.instance:
                queryset = queryset.exclude(id=self.instance.id)
            
            if queryset.exists():
                raise serializers.ValidationError("该分类下关键词已存在")
        
        return value.strip()
    
    def validate_weight(self, value):
        """验证权重"""
        if value < 0 or value > 10:
            raise serializers.ValidationError("权重必须在0-10之间")
        return value


class KeywordRuleSerializer(serializers.ModelSerializer):
    """关键词规则序列化器"""
    rule_type_display = serializers.CharField(source='get_rule_type_display', read_only=True)
    trigger_action_display = serializers.CharField(source='get_trigger_action_display', read_only=True)
    condition_logic_display = serializers.CharField(source='get_condition_logic_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    keyword_count = serializers.SerializerMethodField()
    keywords_detail = KeywordSerializer(source='keywords', many=True, read_only=True)
    
    class Meta:
        model = KeywordRule
        fields = [
            'id', 'name', 'description', 'rule_type', 'rule_type_display',
            'keywords', 'keywords_detail', 'keyword_count',
            'condition_logic', 'condition_logic_display', 'threshold', 'priority',
            'trigger_action', 'trigger_action_display', 'action_config',
            'is_active', 'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_keyword_count(self, obj):
        """获取关键词数量"""
        return obj.keywords.count()
    
    def validate_threshold(self, value):
        """验证阈值"""
        if value < 0 or value > 1:
            raise serializers.ValidationError("阈值必须在0-1之间")
        return value
    
    def validate_keywords(self, value):
        """验证关键词"""
        if not value:
            raise serializers.ValidationError("至少需要选择一个关键词")
        return value


class KeywordMatchSerializer(serializers.ModelSerializer):
    """关键词匹配记录序列化器"""
    match_type_display = serializers.CharField(source='get_match_type_display', read_only=True)
    matched_by_name = serializers.CharField(source='matched_by.username', read_only=True)
    session_id = serializers.CharField(source='session.id', read_only=True)
    message_content = serializers.CharField(source='message.content', read_only=True)
    
    class Meta:
        model = KeywordMatch
        fields = [
            'id', 'keyword', 'matched_text', 'match_type', 'match_type_display',
            'confidence', 'session', 'session_id', 'message', 'message_content',
            'matched_by', 'matched_by_name', 'metadata',
            'created_at', 'matched_at'
        ]
        read_only_fields = ['id', 'created_at', 'matched_at']


class KeywordStatisticsSerializer(serializers.ModelSerializer):
    """关键词统计序列化器"""
    keyword_word = serializers.CharField(source='keyword.word', read_only=True)
    keyword_category = serializers.CharField(source='keyword.category.name', read_only=True)
    
    class Meta:
        model = KeywordStatistics
        fields = [
            'id', 'keyword', 'keyword_word', 'keyword_category', 'date',
            'total_matches', 'unique_users', 'handoff_triggered', 'auto_replies',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        """验证统计数据唯一性"""
        keyword = data.get('keyword')
        date = data.get('date')
        
        if keyword and date:
            queryset = KeywordStatistics.objects.filter(keyword=keyword, date=date)
            if self.instance:
                queryset = queryset.exclude(id=self.instance.id)
            
            if queryset.exists():
                raise serializers.ValidationError({
                    'date': '该关键词在此日期的统计数据已存在'
                })
        
        return data 