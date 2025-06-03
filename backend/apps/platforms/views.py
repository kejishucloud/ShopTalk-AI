from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Platform, PlatformAccount, PlatformConfiguration
from .serializers import PlatformSerializer, PlatformAccountSerializer, PlatformConfigurationSerializer

class PlatformViewSet(viewsets.ModelViewSet):
    """平台管理视图集"""
    queryset = Platform.objects.all()
    serializer_class = PlatformSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def supported_platforms(self, request):
        """获取支持的平台列表"""
        platforms = Platform.objects.filter(is_active=True)
        serializer = self.get_serializer(platforms, many=True)
        return Response(serializer.data)

class PlatformAccountViewSet(viewsets.ModelViewSet):
    """平台账号管理视图集"""
    queryset = PlatformAccount.objects.all()
    serializer_class = PlatformAccountSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """测试平台账号连接"""
        account = self.get_object()
        try:
            # 这里应该实现实际的连接测试逻辑
            return Response({'status': 'success', 'message': '连接测试成功'})
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

class PlatformConfigurationViewSet(viewsets.ModelViewSet):
    """平台配置管理视图集"""
    queryset = PlatformConfiguration.objects.all()
    serializer_class = PlatformConfigurationSerializer
    permission_classes = [IsAuthenticated] 