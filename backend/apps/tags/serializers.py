"""
标签管理模块序列化器
提供标签相关数据的序列化和反序列化
"""

from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import TagCategory, Tag, TagRule, TagAssignment, TagStatistics


class TagCategorySerializer(serializers.ModelSerializer):
    """标签分类序列化器"""
    tag_count = serializers.SerializerMethodField()
    
    class Meta:
        model = TagCategory
        fields = ['id', 'name', 'description', 'color', 'is_active', 
                 'created_at', 'updated_at', 'tag_count']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_tag_count(self, obj):
        """获取分类下的标签数量"""
        return obj.tag_set.filter(is_active=True).count()


class TagSerializer(serializers.ModelSerializer):
    """标签序列化器"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    assignment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Tag
        fields = ['id', 'name', 'category', 'category_name', 'description', 
                 'color', 'is_system', 'is_active', 'created_by', 'created_by_name',
                 'created_at', 'updated_at', 'assignment_count']
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def get_assignment_count(self, obj):
        """获取标签使用次数"""
        return obj.tagassignment_set.count()


class TagRuleSerializer(serializers.ModelSerializer):
    """标签规则序列化器"""
    target_tags_info = TagSerializer(source='target_tags', many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    rule_type_display = serializers.CharField(source='get_rule_type_display', read_only=True)
    
    class Meta:
        model = TagRule
        fields = ['id', 'name', 'rule_type', 'rule_type_display', 'conditions', 
                 'target_tags', 'target_tags_info', 'priority', 'is_active',
                 'created_by', 'created_by_name', 'created_at', 'updated_at']
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def validate_conditions(self, value):
        """验证规则条件格式"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("条件必须是字典格式")
        
        rule_type = self.initial_data.get('rule_type')
        if rule_type == 'keyword' and 'keywords' not in value:
            raise serializers.ValidationError("关键词规则必须包含keywords字段")
        elif rule_type == 'pattern' and 'pattern' not in value:
            raise serializers.ValidationError("正则表达式规则必须包含pattern字段")
        
        return value


class TagAssignmentSerializer(serializers.ModelSerializer):
    """标签分配序列化器"""
    tag_name = serializers.CharField(source='tag.name', read_only=True)
    tag_color = serializers.CharField(source='tag.color', read_only=True)
    content_type_name = serializers.CharField(source='content_type.model', read_only=True)
    assigned_by_name = serializers.CharField(source='assigned_by.username', read_only=True)
    rule_name = serializers.CharField(source='rule.name', read_only=True)
    assignment_type_display = serializers.CharField(source='get_assignment_type_display', read_only=True)
    
    class Meta:
        model = TagAssignment
        fields = ['id', 'tag', 'tag_name', 'tag_color', 'content_type', 'content_type_name',
                 'object_id', 'assignment_type', 'assignment_type_display', 'confidence',
                 'rule', 'rule_name', 'assigned_by', 'assigned_by_name', 'assigned_at']
        read_only_fields = ['assigned_by', 'assigned_at']
    
    def validate_confidence(self, value):
        """验证置信度范围"""
        if not 0 <= value <= 1:
            raise serializers.ValidationError("置信度必须在0-1之间")
        return value


class TagStatisticsSerializer(serializers.ModelSerializer):
    """标签统计序列化器"""
    tag_name = serializers.CharField(source='tag.name', read_only=True)
    tag_category = serializers.CharField(source='tag.category.name', read_only=True)
    tag_color = serializers.CharField(source='tag.color', read_only=True)
    
    class Meta:
        model = TagStatistics
        fields = ['id', 'tag', 'tag_name', 'tag_category', 'tag_color',
                 'total_assignments', 'active_assignments', 'last_assigned_at', 
                 'updated_at']
        read_only_fields = ['updated_at']


# 简化的序列化器，用于下拉选择等场景
class TagSimpleSerializer(serializers.ModelSerializer):
    """简化标签序列化器"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Tag
        fields = ['id', 'name', 'category_name', 'color']


class TagCategorySimpleSerializer(serializers.ModelSerializer):
    """简化标签分类序列化器"""
    
    class Meta:
        model = TagCategory
        fields = ['id', 'name', 'color'] 