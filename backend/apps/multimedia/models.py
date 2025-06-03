from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
import uuid
import os

User = get_user_model()


def upload_to_images(instance, filename):
    """图片上传路径"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('images', filename)


def upload_to_videos(instance, filename):
    """视频上传路径"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('videos', filename)


def upload_to_audios(instance, filename):
    """音频上传路径"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('audios', filename)


class MediaFile(models.Model):
    """多媒体文件基础模型"""
    
    MEDIA_TYPES = [
        ('image', '图片'),
        ('video', '视频'),
        ('audio', '音频'),
    ]
    
    PROCESSING_STATUS = [
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('failed', '处理失败'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPES, verbose_name='媒体类型')
    original_filename = models.CharField(max_length=255, verbose_name='原始文件名')
    file_size = models.BigIntegerField(verbose_name='文件大小(字节)')
    mime_type = models.CharField(max_length=100, verbose_name='MIME类型')
    
    # 处理状态
    processing_status = models.CharField(
        max_length=20,
        choices=PROCESSING_STATUS,
        default='pending',
        verbose_name='处理状态'
    )
    processing_progress = models.IntegerField(default=0, verbose_name='处理进度(%)')
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    
    # 关联信息
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='上传用户'
    )
    platform = models.CharField(max_length=50, blank=True, verbose_name='来源平台')
    conversation_id = models.CharField(max_length=100, blank=True, verbose_name='对话ID')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '多媒体文件'
        verbose_name_plural = '多媒体文件'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['media_type', 'created_at']),
            models.Index(fields=['processing_status']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f'{self.original_filename} - {self.get_media_type_display()}'


class ImageFile(models.Model):
    """图片文件模型"""
    
    media_file = models.OneToOneField(
        MediaFile,
        on_delete=models.CASCADE,
        primary_key=True,
        verbose_name='媒体文件'
    )
    
    file = models.ImageField(
        upload_to=upload_to_images,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif', 'webp'])],
        verbose_name='图片文件'
    )
    
    # 图片属性
    width = models.IntegerField(default=0, verbose_name='宽度')
    height = models.IntegerField(default=0, verbose_name='高度')
    
    # 缩略图
    thumbnail = models.ImageField(
        upload_to=upload_to_images,
        blank=True,
        null=True,
        verbose_name='缩略图'
    )
    
    # AI分析结果
    ocr_text = models.TextField(blank=True, verbose_name='OCR识别文本')
    objects_detected = models.JSONField(default=list, verbose_name='检测到的物体')
    scene_description = models.TextField(blank=True, verbose_name='场景描述')
    ai_analysis = models.JSONField(default=dict, verbose_name='AI分析结果')
    
    class Meta:
        verbose_name = '图片文件'
        verbose_name_plural = '图片文件'
    
    def __str__(self):
        return f'图片: {self.media_file.original_filename}'


class VideoFile(models.Model):
    """视频文件模型"""
    
    media_file = models.OneToOneField(
        MediaFile,
        on_delete=models.CASCADE,
        primary_key=True,
        verbose_name='媒体文件'
    )
    
    file = models.FileField(
        upload_to=upload_to_videos,
        validators=[FileExtensionValidator(['mp4', 'avi', 'mov', 'webm'])],
        verbose_name='视频文件'
    )
    
    # 视频属性
    duration = models.FloatField(default=0.0, verbose_name='时长(秒)')
    width = models.IntegerField(default=0, verbose_name='宽度')
    height = models.IntegerField(default=0, verbose_name='高度')
    fps = models.FloatField(default=0.0, verbose_name='帧率')
    bitrate = models.IntegerField(default=0, verbose_name='比特率')
    
    # 缩略图和预览
    thumbnail = models.ImageField(
        upload_to=upload_to_images,
        blank=True,
        null=True,
        verbose_name='视频缩略图'
    )
    
    # AI分析结果
    transcript = models.TextField(blank=True, verbose_name='语音转文字')
    scene_analysis = models.JSONField(default=list, verbose_name='场景分析')
    objects_timeline = models.JSONField(default=list, verbose_name='物体时间线')
    ai_summary = models.TextField(blank=True, verbose_name='AI总结')
    
    class Meta:
        verbose_name = '视频文件'
        verbose_name_plural = '视频文件'
    
    def __str__(self):
        return f'视频: {self.media_file.original_filename}'


class AudioFile(models.Model):
    """音频文件模型"""
    
    media_file = models.OneToOneField(
        MediaFile,
        on_delete=models.CASCADE,
        primary_key=True,
        verbose_name='媒体文件'
    )
    
    file = models.FileField(
        upload_to=upload_to_audios,
        validators=[FileExtensionValidator(['mp3', 'wav', 'aac', 'm4a'])],
        verbose_name='音频文件'
    )
    
    # 音频属性
    duration = models.FloatField(default=0.0, verbose_name='时长(秒)')
    sample_rate = models.IntegerField(default=0, verbose_name='采样率')
    channels = models.IntegerField(default=0, verbose_name='声道数')
    bitrate = models.IntegerField(default=0, verbose_name='比特率')
    
    # AI分析结果
    transcript = models.TextField(blank=True, verbose_name='语音转文字')
    language_detected = models.CharField(max_length=10, blank=True, verbose_name='检测语言')
    speaker_count = models.IntegerField(default=0, verbose_name='说话人数量')
    emotion_analysis = models.JSONField(default=dict, verbose_name='情感分析')
    ai_summary = models.TextField(blank=True, verbose_name='AI总结')
    
    class Meta:
        verbose_name = '音频文件'
        verbose_name_plural = '音频文件'
    
    def __str__(self):
        return f'音频: {self.media_file.original_filename}'


class ProcessingTask(models.Model):
    """处理任务模型"""
    
    TASK_TYPES = [
        ('ocr', 'OCR文字识别'),
        ('object_detection', '物体检测'),
        ('scene_analysis', '场景分析'),
        ('speech_to_text', '语音转文字'),
        ('video_analysis', '视频分析'),
        ('thumbnail_generation', '缩略图生成'),
        ('ai_description', 'AI描述生成'),
    ]
    
    TASK_STATUS = [
        ('pending', '待处理'),
        ('running', '运行中'),
        ('completed', '已完成'),
        ('failed', '失败'),
        ('cancelled', '已取消'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    media_file = models.ForeignKey(
        MediaFile,
        on_delete=models.CASCADE,
        verbose_name='媒体文件'
    )
    
    task_type = models.CharField(max_length=50, choices=TASK_TYPES, verbose_name='任务类型')
    status = models.CharField(max_length=20, choices=TASK_STATUS, default='pending', verbose_name='状态')
    progress = models.IntegerField(default=0, verbose_name='进度(%)')
    
    # 任务配置
    config = models.JSONField(default=dict, verbose_name='任务配置')
    
    # 结果
    result = models.JSONField(default=dict, verbose_name='处理结果')
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    
    # 时间信息
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '处理任务'
        verbose_name_plural = '处理任务'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['task_type', 'status']),
        ]
    
    def __str__(self):
        return f'{self.get_task_type_display()} - {self.get_status_display()}'


class AIAnalysisResult(models.Model):
    """AI分析结果模型"""
    
    ANALYSIS_TYPES = [
        ('image_description', '图片描述'),
        ('video_summary', '视频总结'),
        ('audio_transcript', '音频转录'),
        ('content_moderation', '内容审核'),
        ('emotion_detection', '情感检测'),
        ('object_recognition', '物体识别'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    media_file = models.ForeignKey(
        MediaFile,
        on_delete=models.CASCADE,
        verbose_name='媒体文件'
    )
    
    analysis_type = models.CharField(max_length=50, choices=ANALYSIS_TYPES, verbose_name='分析类型')
    model_name = models.CharField(max_length=100, verbose_name='使用模型')
    confidence = models.FloatField(verbose_name='置信度')
    
    # 分析结果
    result_data = models.JSONField(verbose_name='结果数据')
    text_result = models.TextField(blank=True, verbose_name='文本结果')
    
    # 元数据
    processing_time = models.FloatField(verbose_name='处理时间(秒)')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        verbose_name = 'AI分析结果'
        verbose_name_plural = 'AI分析结果'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['analysis_type', 'created_at']),
            models.Index(fields=['media_file', 'analysis_type']),
        ]
    
    def __str__(self):
        return f'{self.get_analysis_type_display()} - {self.media_file.original_filename}' 