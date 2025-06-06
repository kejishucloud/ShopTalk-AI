from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import io
import random
import string
from PIL import Image, ImageDraw, ImageFont
from django.core.cache import cache
from .models import UserProfile
from .serializers import UserSerializer, UserProfileSerializer, UserLoginSerializer

User = get_user_model()

@api_view(['GET'])
@permission_classes([AllowAny])
def generate_captcha(request):
    """生成验证码图片"""
    try:
        # 生成随机验证码
        captcha_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        
        # 将验证码存储到缓存中，设置5分钟过期
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        
        cache.set(f'captcha_{session_key}', captcha_text.upper(), timeout=300)
        
        # 创建图片
        image = Image.new('RGB', (120, 40), color='white')
        draw = ImageDraw.Draw(image)
        
        # 添加背景噪点
        for _ in range(100):
            x = random.randint(0, 120)
            y = random.randint(0, 40)
            draw.point((x, y), fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
        
        # 绘制验证码文字
        try:
            # 尝试使用系统字体
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        except:
            # 使用默认字体
            font = ImageFont.load_default()
        
        # 绘制每个字符
        for i, char in enumerate(captcha_text):
            x = 20 + i * 20 + random.randint(-5, 5)
            y = 10 + random.randint(-5, 5)
            color = (random.randint(50, 150), random.randint(50, 150), random.randint(50, 150))
            draw.text((x, y), char, font=font, fill=color)
        
        # 添加干扰线
        for _ in range(3):
            start = (random.randint(0, 120), random.randint(0, 40))
            end = (random.randint(0, 120), random.randint(0, 40))
            draw.line([start, end], fill=(random.randint(50, 150), random.randint(50, 150), random.randint(50, 150)))
        
        # 将图片转换为bytes
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        
        return HttpResponse(buffer.getvalue(), content_type='image/png')
        
    except Exception as e:
        # 返回一个简单的文本验证码作为备选
        captcha_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cache.set(f'captcha_{session_key}', captcha_text.upper(), timeout=300)
        
        # 创建简单的文本图片
        image = Image.new('RGB', (120, 40), color='lightgray')
        draw = ImageDraw.Draw(image)
        draw.text((30, 15), captcha_text, fill='black')
        
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        
        return HttpResponse(buffer.getvalue(), content_type='image/png')

@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def login_view(request):
    """用户登录"""
    serializer = UserLoginSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'success': False,
            'message': '请求参数无效',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    username = serializer.validated_data['username']
    password = serializer.validated_data['password']
    captcha = serializer.validated_data.get('captcha', '')
    
    # 验证验证码
    session_key = request.session.session_key
    if session_key:
        cached_captcha = cache.get(f'captcha_{session_key}')
        if not cached_captcha or cached_captcha.upper() != captcha.upper():
            return Response({
                'success': False,
                'message': '验证码错误'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 验证码验证成功后删除
        cache.delete(f'captcha_{session_key}')
    else:
        return Response({
            'success': False,
            'message': '验证码已过期，请刷新后重试'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # 验证用户名密码
    user = authenticate(username=username, password=password)
    
    if user is not None:
        if user.is_active:
            # 生成JWT token
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            # 获取用户信息
            user_info = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
            }
            
            # 尝试获取用户profile
            try:
                profile = UserProfile.objects.get(user=user)
                user_info.update({
                    'nickname': profile.nickname,
                    'avatar': profile.avatar.url if profile.avatar else None,
                    'phone': profile.phone,
                })
            except UserProfile.DoesNotExist:
                pass
            
            return Response({
                'success': True,
                'message': '登录成功',
                'data': {
                    'access_token': str(access_token),
                    'refresh_token': str(refresh),
                    'user': user_info,
                    'permissions': list(user.user_permissions.values_list('codename', flat=True)) if user.user_permissions.exists() else []
                }
            })
        else:
            return Response({
                'success': False,
                'message': '账户已被禁用'
            }, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({
            'success': False,
            'message': '用户名或密码错误'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_info(request):
    """获取用户信息"""
    user = request.user
    user_info = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
    }
    
    # 尝试获取用户profile
    try:
        profile = UserProfile.objects.get(user=user)
        user_info.update({
            'nickname': profile.nickname,
            'avatar': profile.avatar.url if profile.avatar else None,
            'phone': profile.phone,
        })
    except UserProfile.DoesNotExist:
        pass
    
    return Response({
        'success': True,
        'data': {
            'user': user_info,
            'permissions': list(user.user_permissions.values_list('codename', flat=True)) if user.user_permissions.exists() else []
        }
    })

class UserViewSet(viewsets.ModelViewSet):
    """用户管理视图集"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def profile(self, request):
        """获取当前用户资料"""
        try:
            profile = UserProfile.objects.get(user=request.user)
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response(
                {'error': '用户资料不存在'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def update_profile(self, request):
        """更新用户资料"""
        try:
            profile = UserProfile.objects.get(user=request.user)
            serializer = UserProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except UserProfile.DoesNotExist:
            return Response(
                {'error': '用户资料不存在'}, 
                status=status.HTTP_404_NOT_FOUND
            ) 