"""
小红书平台适配器
实现小红书平台的智能客服功能
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from playwright.async_api import Page, Browser, BrowserContext

from .base import BasePlatformAdapter
from ..utils.playwright_utils import PlaywrightUtils

logger = logging.getLogger(__name__)


class XiaohongshuAdapter(BasePlatformAdapter):
    """小红书平台适配器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.platform_name = "xiaohongshu"
        self.base_url = "https://www.xiaohongshu.com"
        self.creator_url = "https://creator.xiaohongshu.com"
        self.playwright_utils = PlaywrightUtils()
        self.page: Optional[Page] = None
        self.context: Optional[BrowserContext] = None
        
    async def initialize(self) -> bool:
        """初始化小红书适配器"""
        try:
            # 启动浏览器
            self.context = await self.playwright_utils.create_context(
                headless=self.config.get('headless', False),
                user_data_dir=self.config.get('user_data_dir'),
                proxy=self.config.get('proxy')
            )
            
            self.page = await self.context.new_page()
            
            # 设置页面配置
            await self.page.set_viewport_size({"width": 1920, "height": 1080})
            
            # 登录检查
            if not await self._check_login_status():
                logger.warning("小红书未登录，需要手动登录")
                return False
                
            logger.info("小红书适配器初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"小红书适配器初始化失败: {e}")
            return False
    
    async def _check_login_status(self) -> bool:
        """检查登录状态"""
        try:
            await self.page.goto(self.base_url)
            await self.page.wait_for_load_state('networkidle')
            
            # 检查是否存在登录按钮
            login_button = await self.page.query_selector('.login-btn, .sign-in')
            if login_button:
                return False
                
            # 检查是否存在用户头像
            user_avatar = await self.page.query_selector('.user-avatar, .avatar')
            return user_avatar is not None
            
        except Exception as e:
            logger.error(f"检查登录状态失败: {e}")
            return False
    
    async def send_message(self, user_id: str, message: str, message_type: str = "text") -> bool:
        """发送私信"""
        try:
            # 导航到私信页面
            await self.page.goto(f"{self.base_url}/messages")
            await self.page.wait_for_load_state('networkidle')
            
            # 查找或创建对话
            conversation = await self._find_or_create_conversation(user_id)
            if not conversation:
                logger.error(f"无法找到或创建与用户 {user_id} 的对话")
                return False
            
            # 点击对话
            await conversation.click()
            await self.page.wait_for_timeout(1000)
            
            # 发送消息
            if message_type == "text":
                return await self._send_text_message(message)
            elif message_type == "image":
                return await self._send_image_message(message)
            else:
                logger.error(f"不支持的消息类型: {message_type}")
                return False
                
        except Exception as e:
            logger.error(f"发送私信失败: {e}")
            return False
    
    async def _find_or_create_conversation(self, user_id: str):
        """查找或创建对话"""
        try:
            # 查找现有对话
            conversations = await self.page.query_selector_all('.conversation-item')
            for conv in conversations:
                user_info = await conv.query_selector('.user-info')
                if user_info:
                    username = await user_info.get_attribute('data-user-id')
                    if username == user_id:
                        return conv
            
            # 如果没找到，创建新对话
            new_chat_btn = await self.page.query_selector('.new-chat-btn, .start-chat')
            if new_chat_btn:
                await new_chat_btn.click()
                await self.page.wait_for_timeout(1000)
                
                # 搜索用户
                search_input = await self.page.query_selector('.user-search-input')
                if search_input:
                    await search_input.fill(user_id)
                    await self.page.keyboard.press('Enter')
                    await self.page.wait_for_timeout(2000)
                    
                    # 选择用户
                    user_result = await self.page.query_selector('.user-search-result:first-child')
                    if user_result:
                        await user_result.click()
                        return user_result
            
            return None
            
        except Exception as e:
            logger.error(f"查找或创建对话失败: {e}")
            return None
    
    async def _send_text_message(self, message: str) -> bool:
        """发送文本消息"""
        try:
            # 查找消息输入框
            message_input = await self.page.query_selector('.message-input, .chat-input textarea')
            if not message_input:
                logger.error("找不到消息输入框")
                return False
            
            # 输入消息
            await message_input.fill(message)
            await self.page.wait_for_timeout(500)
            
            # 发送消息
            send_btn = await self.page.query_selector('.send-btn, .chat-send-btn')
            if send_btn:
                await send_btn.click()
            else:
                # 使用回车键发送
                await self.page.keyboard.press('Enter')
            
            await self.page.wait_for_timeout(1000)
            logger.info(f"成功发送文本消息: {message[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"发送文本消息失败: {e}")
            return False
    
    async def _send_image_message(self, image_path: str) -> bool:
        """发送图片消息"""
        try:
            # 查找图片上传按钮
            upload_btn = await self.page.query_selector('.upload-btn, .image-upload')
            if not upload_btn:
                logger.error("找不到图片上传按钮")
                return False
            
            # 上传图片
            await upload_btn.set_input_files(image_path)
            await self.page.wait_for_timeout(3000)
            
            # 发送图片
            send_btn = await self.page.query_selector('.send-btn, .confirm-send')
            if send_btn:
                await send_btn.click()
                await self.page.wait_for_timeout(2000)
                logger.info(f"成功发送图片: {image_path}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"发送图片消息失败: {e}")
            return False
    
    async def get_messages(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取私信列表"""
        try:
            await self.page.goto(f"{self.base_url}/messages")
            await self.page.wait_for_load_state('networkidle')
            
            messages = []
            
            # 获取对话列表
            conversations = await self.page.query_selector_all('.conversation-item')
            
            for conv in conversations[:limit]:
                try:
                    # 点击对话
                    await conv.click()
                    await self.page.wait_for_timeout(1000)
                    
                    # 获取对话信息
                    user_info = await conv.query_selector('.user-info')
                    user_name = await user_info.inner_text() if user_info else "未知用户"
                    
                    # 获取最新消息
                    latest_message = await self.page.query_selector('.message-item:last-child')
                    if latest_message:
                        message_text = await latest_message.inner_text()
                        message_time = await self._extract_message_time(latest_message)
                        
                        messages.append({
                            'user_id': user_name,
                            'user_name': user_name,
                            'message': message_text,
                            'timestamp': message_time,
                            'message_type': 'text',
                            'platform': 'xiaohongshu'
                        })
                
                except Exception as e:
                    logger.error(f"获取对话消息失败: {e}")
                    continue
            
            logger.info(f"获取到 {len(messages)} 条私信")
            return messages
            
        except Exception as e:
            logger.error(f"获取私信列表失败: {e}")
            return []
    
    async def _extract_message_time(self, message_element) -> datetime:
        """提取消息时间"""
        try:
            time_element = await message_element.query_selector('.message-time, .time')
            if time_element:
                time_text = await time_element.inner_text()
                # 解析时间文本（需要根据实际格式调整）
                return datetime.now()  # 简化处理
            return datetime.now()
        except:
            return datetime.now()
    
    async def publish_content(self, content: Dict[str, Any]) -> bool:
        """发布内容"""
        try:
            # 导航到创作者中心
            await self.page.goto(f"{self.creator_url}/publish/note")
            await self.page.wait_for_load_state('networkidle')
            
            # 上传图片
            if content.get('images'):
                await self._upload_images(content['images'])
            
            # 填写标题
            if content.get('title'):
                title_input = await self.page.query_selector('.title-input, input[placeholder*="标题"]')
                if title_input:
                    await title_input.fill(content['title'])
            
            # 填写内容
            if content.get('text'):
                content_input = await self.page.query_selector('.content-input, .note-editor')
                if content_input:
                    await content_input.fill(content['text'])
            
            # 添加话题标签
            if content.get('tags'):
                await self._add_tags(content['tags'])
            
            # 发布
            publish_btn = await self.page.query_selector('.publish-btn, .submit-btn')
            if publish_btn:
                await publish_btn.click()
                await self.page.wait_for_timeout(3000)
                
                logger.info("内容发布成功")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"发布内容失败: {e}")
            return False
    
    async def _upload_images(self, image_paths: List[str]) -> bool:
        """上传图片"""
        try:
            upload_area = await self.page.query_selector('.upload-area, .image-upload-area')
            if not upload_area:
                return False
            
            for image_path in image_paths:
                await upload_area.set_input_files(image_path)
                await self.page.wait_for_timeout(2000)
            
            return True
            
        except Exception as e:
            logger.error(f"上传图片失败: {e}")
            return False
    
    async def _add_tags(self, tags: List[str]) -> bool:
        """添加标签"""
        try:
            for tag in tags:
                tag_input = await self.page.query_selector('.tag-input, .hashtag-input')
                if tag_input:
                    await tag_input.fill(f"#{tag}")
                    await self.page.keyboard.press('Enter')
                    await self.page.wait_for_timeout(500)
            
            return True
            
        except Exception as e:
            logger.error(f"添加标签失败: {e}")
            return False
    
    async def get_comments(self, note_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取笔记评论"""
        try:
            await self.page.goto(f"{self.base_url}/explore/{note_id}")
            await self.page.wait_for_load_state('networkidle')
            
            comments = []
            comment_elements = await self.page.query_selector_all('.comment-item')
            
            for element in comment_elements[:limit]:
                try:
                    user_element = await element.query_selector('.comment-user')
                    content_element = await element.query_selector('.comment-content')
                    time_element = await element.query_selector('.comment-time')
                    
                    if user_element and content_element:
                        user_name = await user_element.inner_text()
                        content = await content_element.inner_text()
                        time_text = await time_element.inner_text() if time_element else ""
                        
                        comments.append({
                            'user_name': user_name,
                            'content': content,
                            'time': time_text,
                            'note_id': note_id,
                            'platform': 'xiaohongshu'
                        })
                
                except Exception as e:
                    logger.error(f"解析评论失败: {e}")
                    continue
            
            logger.info(f"获取到 {len(comments)} 条评论")
            return comments
            
        except Exception as e:
            logger.error(f"获取评论失败: {e}")
            return []
    
    async def reply_comment(self, note_id: str, comment_id: str, reply_text: str) -> bool:
        """回复评论"""
        try:
            await self.page.goto(f"{self.base_url}/explore/{note_id}")
            await self.page.wait_for_load_state('networkidle')
            
            # 找到特定评论
            comment_element = await self.page.query_selector(f'[data-comment-id="{comment_id}"]')
            if not comment_element:
                logger.error(f"找不到评论 {comment_id}")
                return False
            
            # 点击回复按钮
            reply_btn = await comment_element.query_selector('.reply-btn')
            if reply_btn:
                await reply_btn.click()
                await self.page.wait_for_timeout(1000)
                
                # 输入回复内容
                reply_input = await self.page.query_selector('.reply-input')
                if reply_input:
                    await reply_input.fill(reply_text)
                    
                    # 发送回复
                    send_btn = await self.page.query_selector('.reply-send-btn')
                    if send_btn:
                        await send_btn.click()
                        await self.page.wait_for_timeout(2000)
                        
                        logger.info(f"成功回复评论: {reply_text}")
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"回复评论失败: {e}")
            return False
    
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """获取用户资料"""
        try:
            await self.page.goto(f"{self.base_url}/user/profile/{user_id}")
            await self.page.wait_for_load_state('networkidle')
            
            profile = {}
            
            # 获取用户名
            username_element = await self.page.query_selector('.username, .user-name')
            if username_element:
                profile['username'] = await username_element.inner_text()
            
            # 获取粉丝数
            fans_element = await self.page.query_selector('.fans-count')
            if fans_element:
                profile['fans_count'] = await fans_element.inner_text()
            
            # 获取关注数
            following_element = await self.page.query_selector('.following-count')
            if following_element:
                profile['following_count'] = await following_element.inner_text()
            
            # 获取获赞数
            likes_element = await self.page.query_selector('.likes-count')
            if likes_element:
                profile['likes_count'] = await likes_element.inner_text()
            
            # 获取简介
            bio_element = await self.page.query_selector('.user-bio, .description')
            if bio_element:
                profile['bio'] = await bio_element.inner_text()
            
            profile['user_id'] = user_id
            profile['platform'] = 'xiaohongshu'
            
            logger.info(f"获取用户资料成功: {user_id}")
            return profile
            
        except Exception as e:
            logger.error(f"获取用户资料失败: {e}")
            return {}
    
    async def search_notes(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """搜索笔记"""
        try:
            # 导航到搜索页面
            await self.page.goto(f"{self.base_url}/search_result?keyword={keyword}")
            await self.page.wait_for_load_state('networkidle')
            
            notes = []
            note_elements = await self.page.query_selector_all('.note-item')
            
            for element in note_elements[:limit]:
                try:
                    title_element = await element.query_selector('.note-title')
                    author_element = await element.query_selector('.note-author')
                    link_element = await element.query_selector('a')
                    
                    if title_element and author_element and link_element:
                        title = await title_element.inner_text()
                        author = await author_element.inner_text()
                        link = await link_element.get_attribute('href')
                        
                        notes.append({
                            'title': title,
                            'author': author,
                            'link': link,
                            'keyword': keyword,
                            'platform': 'xiaohongshu'
                        })
                
                except Exception as e:
                    logger.error(f"解析笔记信息失败: {e}")
                    continue
            
            logger.info(f"搜索到 {len(notes)} 篇笔记")
            return notes
            
        except Exception as e:
            logger.error(f"搜索笔记失败: {e}")
            return []
    
    async def get_analytics(self) -> Dict[str, Any]:
        """获取数据分析"""
        try:
            await self.page.goto(f"{self.creator_url}/analytics")
            await self.page.wait_for_load_state('networkidle')
            
            analytics = {}
            
            # 获取总浏览量
            views_element = await self.page.query_selector('.total-views')
            if views_element:
                analytics['total_views'] = await views_element.inner_text()
            
            # 获取总点赞数
            likes_element = await self.page.query_selector('.total-likes')
            if likes_element:
                analytics['total_likes'] = await likes_element.inner_text()
            
            # 获取总收藏数
            collections_element = await self.page.query_selector('.total-collections')
            if collections_element:
                analytics['total_collections'] = await collections_element.inner_text()
            
            # 获取粉丝增长
            fans_growth_element = await self.page.query_selector('.fans-growth')
            if fans_growth_element:
                analytics['fans_growth'] = await fans_growth_element.inner_text()
            
            analytics['platform'] = 'xiaohongshu'
            analytics['timestamp'] = datetime.now().isoformat()
            
            logger.info("获取数据分析成功")
            return analytics
            
        except Exception as e:
            logger.error(f"获取数据分析失败: {e}")
            return {}
    
    async def cleanup(self):
        """清理资源"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            logger.info("小红书适配器资源清理完成")
        except Exception as e:
            logger.error(f"清理资源失败: {e}")
    
    def get_platform_info(self) -> Dict[str, Any]:
        """获取平台信息"""
        return {
            'name': '小红书',
            'platform_id': 'xiaohongshu',
            'features': [
                '私信管理',
                '内容发布',
                '评论回复',
                '用户资料查询',
                '笔记搜索',
                '数据分析'
            ],
            'supported_message_types': ['text', 'image'],
            'rate_limits': {
                'messages_per_hour': 100,
                'posts_per_day': 10,
                'comments_per_hour': 50
            }
        } 