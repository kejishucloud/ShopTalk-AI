"""
抖音平台适配器
"""
import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

from .base import EcommercePlatformAdapter, PlatformMessage, MessageType, MessageDirection, PlatformAccount

logger = logging.getLogger(__name__)


class DouyinAdapter(EcommercePlatformAdapter):
    """抖音平台适配器"""
    
    def __init__(self, account: PlatformAccount):
        super().__init__(account)
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.is_polling = False
        self.message_polling_interval = 5  # 秒
        
    @property
    def platform_name(self) -> str:
        return "抖音"
    
    @property
    def supported_message_types(self) -> List[MessageType]:
        return [
            MessageType.TEXT,
            MessageType.IMAGE,
            MessageType.VIDEO,
            MessageType.PRODUCT,
            MessageType.LINK
        ]
    
    async def connect(self) -> bool:
        """连接到抖音"""
        try:
            logger.info(f"正在连接抖音账号: {self.account.account_name}")
            
            # 启动Playwright
            self.playwright = await async_playwright().start()
            
            # 启动浏览器
            self.browser = await self.playwright.chromium.launch(
                headless=self.account.settings.get('headless', False),
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                ]
            )
            
            # 创建浏览器上下文
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # 创建页面
            self.page = await self.context.new_page()
            
            # 登录抖音
            await self._login()
            
            # 验证登录状态
            if await self._verify_login():
                self.is_connected = True
                logger.info("抖音连接成功")
                
                # 开始消息轮询
                asyncio.create_task(self._start_message_polling())
                return True
            else:
                logger.error("抖音登录验证失败")
                return False
                
        except Exception as e:
            logger.error(f"连接抖音失败: {str(e)}", exc_info=True)
            return False
    
    async def disconnect(self) -> bool:
        """断开抖音连接"""
        try:
            self.is_polling = False
            
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
                
            self.is_connected = False
            logger.info("抖音连接已断开")
            return True
        except Exception as e:
            logger.error(f"断开抖音连接失败: {str(e)}")
            return False
    
    async def _login(self):
        """登录抖音"""
        try:
            # 访问抖店商家后台
            await self.page.goto("https://fxg.jinritemai.com/")
            await asyncio.sleep(3)
            
            # 检查是否有保存的cookies
            saved_cookies = self.account.credentials.get('cookies')
            if saved_cookies:
                await self.context.add_cookies(saved_cookies)
                await self.page.reload()
                await asyncio.sleep(2)
                return
            
            # 点击登录
            login_button = await self.page.query_selector('.login-btn')
            if login_button:
                await login_button.click()
                await asyncio.sleep(2)
            
            # 手机号登录
            phone = self.account.credentials.get('phone')
            if phone:
                # 输入手机号
                phone_input = await self.page.wait_for_selector('input[placeholder*="手机号"]', timeout=10000)
                await phone_input.fill(phone)
                
                # 点击获取验证码
                code_button = await self.page.wait_for_selector('.get-code-btn')
                await code_button.click()
                
                # 等待用户输入验证码
                logger.warning("请手动输入验证码并完成登录")
                await self.page.wait_for_url("**/compass", timeout=60000)
            else:
                logger.warning("未提供手机号，需要手动登录")
                await self.page.wait_for_url("**/compass", timeout=60000)
            
            # 保存cookies
            cookies = await self.context.cookies()
            # 这里可以保存cookies到数据库
            
        except Exception as e:
            logger.error(f"抖音登录失败: {str(e)}")
            raise
    
    async def _verify_login(self) -> bool:
        """验证登录状态"""
        try:
            # 检查是否在抖店后台
            current_url = self.page.url
            if "jinritemai.com" in current_url:
                # 检查用户信息是否存在
                user_info = await self.page.query_selector('.user-info')
                if user_info:
                    logger.info("抖音登录验证成功")
                    return True
            
            logger.error("抖音登录验证失败")
            return False
                
        except Exception as e:
            logger.error(f"验证抖音登录状态失败: {str(e)}")
            return False
    
    async def _start_message_polling(self):
        """开始消息轮询"""
        self.is_polling = True
        logger.info("开始抖音消息轮询")
        
        while self.is_polling and self.is_connected:
            try:
                await self._check_new_messages()
                await self._check_live_comments()  # 检查直播评论
                await asyncio.sleep(self.message_polling_interval)
            except Exception as e:
                logger.error(f"消息轮询错误: {str(e)}")
                await asyncio.sleep(self.message_polling_interval)
    
    async def _check_new_messages(self):
        """检查新消息"""
        try:
            # 访问客服消息页面
            await self.page.goto("https://fxg.jinritemai.com/ffa/mshop/shop_center/customer_service")
            await asyncio.sleep(2)
            
            # 查找未读消息
            unread_items = await self.page.query_selector_all('.chat-item.unread')
            
            for item in unread_items:
                try:
                    message = await self._parse_message_item(item)
                    if message:
                        await self._handle_message(message)
                except Exception as e:
                    logger.error(f"解析消息失败: {str(e)}")
                    
        except Exception as e:
            logger.error(f"检查新消息失败: {str(e)}")
    
    async def _check_live_comments(self):
        """检查直播评论"""
        try:
            # 访问直播管理页面
            await self.page.goto("https://fxg.jinritemai.com/ffa/mshop/live/live_list")
            await asyncio.sleep(2)
            
            # 查找正在直播的房间
            live_rooms = await self.page.query_selector_all('.live-room.active')
            
            for room in live_rooms:
                try:
                    room_id = await room.get_attribute('data-room-id')
                    if room_id:
                        await self._check_room_comments(room_id)
                except Exception as e:
                    logger.error(f"检查直播间评论失败: {str(e)}")
                    
        except Exception as e:
            logger.error(f"检查直播评论失败: {str(e)}")
    
    async def _check_room_comments(self, room_id: str):
        """检查直播间评论"""
        try:
            # 访问直播间管理页面
            await self.page.goto(f"https://fxg.jinritemai.com/ffa/mshop/live/live_room/{room_id}")
            await asyncio.sleep(2)
            
            # 查找新评论
            comments = await self.page.query_selector_all('.comment-item.new')
            
            for comment in comments:
                try:
                    user_name = await comment.query_selector('.user-name')
                    user_name_text = await user_name.inner_text() if user_name else ""
                    
                    content = await comment.query_selector('.comment-content')
                    content_text = await content.inner_text() if content else ""
                    
                    # 构建评论消息
                    message = PlatformMessage(
                        message_id=f"dy_live_{int(time.time())}_{hash(content_text)}",
                        conversation_id=f"dy_live_{room_id}",
                        sender_id=user_name_text,
                        sender_name=user_name_text,
                        recipient_id=self.account.account_id,
                        recipient_name=self.account.account_name,
                        message_type=MessageType.TEXT,
                        content=content_text,
                        direction=MessageDirection.INBOUND,
                        timestamp=time.time(),
                        metadata={
                            'platform': 'douyin',
                            'source': 'live_comment',
                            'room_id': room_id
                        }
                    )
                    
                    await self._handle_message(message)
                except Exception as e:
                    logger.error(f"解析直播评论失败: {str(e)}")
                    
        except Exception as e:
            logger.error(f"检查直播间评论失败: {str(e)}")
    
    async def _parse_message_item(self, item) -> Optional[PlatformMessage]:
        """解析消息项"""
        try:
            # 提取消息信息
            customer_name = await item.query_selector('.customer-name')
            customer_name_text = await customer_name.inner_text() if customer_name else ""
            
            content = await item.query_selector('.message-content')
            content_text = await content.inner_text() if content else ""
            
            timestamp = await item.get_attribute('data-timestamp')
            customer_id = await item.get_attribute('data-customer-id')
            
            # 构建消息对象
            message = PlatformMessage(
                message_id=f"dy_{int(time.time())}_{hash(content_text)}",
                conversation_id=f"dy_conv_{customer_id}",
                sender_id=customer_id or customer_name_text,
                sender_name=customer_name_text,
                recipient_id=self.account.account_id,
                recipient_name=self.account.account_name,
                message_type=MessageType.TEXT,
                content=content_text,
                direction=MessageDirection.INBOUND,
                timestamp=float(timestamp) if timestamp else time.time(),
                metadata={
                    'platform': 'douyin',
                    'customer_id': customer_id
                }
            )
            
            return message
            
        except Exception as e:
            logger.error(f"解析消息项失败: {str(e)}")
            return None
    
    async def send_message(self, message: PlatformMessage) -> bool:
        """发送消息"""
        try:
            logger.info(f"发送抖音消息: {message.content[:50]}...")
            
            # 判断是否为直播评论回复
            if 'live' in message.conversation_id:
                return await self._send_live_comment(message)
            
            # 普通客服消息
            await self.page.goto("https://fxg.jinritemai.com/ffa/mshop/shop_center/customer_service")
            await asyncio.sleep(2)
            
            # 找到对话
            customer_id = message.conversation_id.replace("dy_conv_", "")
            chat_item = await self.page.query_selector(f'[data-customer-id="{customer_id}"]')
            if chat_item:
                await chat_item.click()
                await asyncio.sleep(1)
            
            # 输入消息
            input_box = await self.page.wait_for_selector('.message-input')
            await input_box.fill(message.content)
            
            # 发送消息
            send_button = await self.page.query_selector('.send-btn')
            await send_button.click()
            
            await asyncio.sleep(1)
            logger.info("抖音消息发送成功")
            return True
            
        except Exception as e:
            logger.error(f"发送抖音消息失败: {str(e)}")
            return False
    
    async def _send_live_comment(self, message: PlatformMessage) -> bool:
        """发送直播评论"""
        try:
            room_id = message.conversation_id.replace("dy_live_", "")
            
            # 访问直播间管理页面
            await self.page.goto(f"https://fxg.jinritemai.com/ffa/mshop/live/live_room/{room_id}")
            await asyncio.sleep(2)
            
            # 输入评论
            comment_input = await self.page.wait_for_selector('.comment-input')
            await comment_input.fill(message.content)
            
            # 发送评论
            send_button = await self.page.query_selector('.send-comment-btn')
            await send_button.click()
            
            await asyncio.sleep(1)
            logger.info("抖音直播评论发送成功")
            return True
            
        except Exception as e:
            logger.error(f"发送抖音直播评论失败: {str(e)}")
            return False
    
    async def get_conversations(self, limit: int = 50) -> List[Dict]:
        """获取对话列表"""
        try:
            await self.page.goto("https://fxg.jinritemai.com/ffa/mshop/shop_center/customer_service")
            await asyncio.sleep(2)
            
            conversations = []
            chat_items = await self.page.query_selector_all('.chat-item')
            
            for item in chat_items[:limit]:
                try:
                    customer_name = await item.query_selector('.customer-name')
                    customer_name_text = await customer_name.inner_text() if customer_name else ""
                    
                    last_message = await item.query_selector('.last-message')
                    last_message_text = await last_message.inner_text() if last_message else ""
                    
                    timestamp = await item.get_attribute('data-timestamp')
                    customer_id = await item.get_attribute('data-customer-id')
                    
                    conversations.append({
                        'conversation_id': f"dy_conv_{customer_id}",
                        'customer_name': customer_name_text,
                        'customer_id': customer_id,
                        'last_message': last_message_text,
                        'timestamp': timestamp,
                        'platform': 'douyin'
                    })
                except Exception as e:
                    logger.error(f"解析对话项失败: {str(e)}")
            
            return conversations
            
        except Exception as e:
            logger.error(f"获取抖音对话列表失败: {str(e)}")
            return []
    
    async def get_conversation_messages(
        self, 
        conversation_id: str, 
        limit: int = 100
    ) -> List[PlatformMessage]:
        """获取对话消息"""
        try:
            # 打开指定对话
            customer_id = conversation_id.replace("dy_conv_", "")
            await self.page.goto("https://fxg.jinritemai.com/ffa/mshop/shop_center/customer_service")
            await asyncio.sleep(2)
            
            # 选择对话
            chat_item = await self.page.query_selector(f'[data-customer-id="{customer_id}"]')
            if chat_item:
                await chat_item.click()
                await asyncio.sleep(2)
            
            messages = []
            message_items = await self.page.query_selector_all('.message-item')
            
            for item in message_items[-limit:]:
                try:
                    content = await item.query_selector('.content')
                    content_text = await content.inner_text() if content else ""
                    
                    sender = await item.query_selector('.sender')
                    is_self = await sender.get_attribute('data-self') == 'true' if sender else False
                    
                    timestamp = await item.get_attribute('data-timestamp')
                    
                    message = PlatformMessage(
                        message_id=f"dy_{timestamp}_{hash(content_text)}",
                        conversation_id=conversation_id,
                        sender_id=self.account.account_id if is_self else customer_id,
                        sender_name=self.account.account_name if is_self else customer_id,
                        recipient_id=customer_id if is_self else self.account.account_id,
                        recipient_name=customer_id if is_self else self.account.account_name,
                        message_type=MessageType.TEXT,
                        content=content_text,
                        direction=MessageDirection.OUTBOUND if is_self else MessageDirection.INBOUND,
                        timestamp=float(timestamp) if timestamp else time.time(),
                        metadata={'platform': 'douyin'}
                    )
                    
                    messages.append(message)
                except Exception as e:
                    logger.error(f"解析消息失败: {str(e)}")
            
            return messages
            
        except Exception as e:
            logger.error(f"获取抖音对话消息失败: {str(e)}")
            return []
    
    async def mark_message_read(self, message_id: str) -> bool:
        """标记消息为已读"""
        try:
            # 抖音通常在查看消息时自动标记为已读
            return True
        except Exception as e:
            logger.error(f"标记抖音消息已读失败: {str(e)}")
            return False
    
    async def get_product_info(self, product_id: str) -> Optional[Dict]:
        """获取商品信息"""
        try:
            # 访问商品管理页面
            await self.page.goto(f"https://fxg.jinritemai.com/ffa/mshop/goods/edit/{product_id}")
            await asyncio.sleep(3)
            
            # 提取商品信息
            title = await self.page.query_selector('.goods-title input')
            title_text = await title.input_value() if title else ""
            
            price = await self.page.query_selector('.price-input')
            price_text = await price.input_value() if price else ""
            
            stock = await self.page.query_selector('.stock-input')
            stock_text = await stock.input_value() if stock else ""
            
            # 提取商品图片
            images = []
            img_elements = await self.page.query_selector_all('.goods-image img')
            for img in img_elements:
                src = await img.get_attribute('src')
                if src:
                    images.append(src)
            
            return {
                'product_id': product_id,
                'title': title_text,
                'price': price_text,
                'stock': stock_text,
                'images': images,
                'platform': 'douyin'
            }
            
        except Exception as e:
            logger.error(f"获取抖音商品信息失败: {str(e)}")
            return None
    
    async def get_order_info(self, order_id: str) -> Optional[Dict]:
        """获取订单信息"""
        try:
            # 访问订单详情页
            await self.page.goto(f"https://fxg.jinritemai.com/ffa/mshop/order/detail/{order_id}")
            await asyncio.sleep(2)
            
            # 提取订单信息
            status = await self.page.query_selector('.order-status')
            status_text = await status.inner_text() if status else ""
            
            amount = await self.page.query_selector('.order-amount')
            amount_text = await amount.inner_text() if amount else ""
            
            customer = await self.page.query_selector('.customer-info')
            customer_text = await customer.inner_text() if customer else ""
            
            return {
                'order_id': order_id,
                'status': status_text,
                'amount': amount_text,
                'customer': customer_text,
                'platform': 'douyin'
            }
            
        except Exception as e:
            logger.error(f"获取抖音订单信息失败: {str(e)}")
            return None
    
    async def search_products(self, query: str, limit: int = 20) -> List[Dict]:
        """搜索商品"""
        try:
            # 访问商品管理页面
            await self.page.goto("https://fxg.jinritemai.com/ffa/mshop/goods/list")
            await asyncio.sleep(2)
            
            # 搜索商品
            search_input = await self.page.query_selector('.search-input')
            if search_input:
                await search_input.fill(query)
                
                search_button = await self.page.query_selector('.search-btn')
                if search_button:
                    await search_button.click()
                    await asyncio.sleep(2)
            
            products = []
            product_items = await self.page.query_selector_all('.goods-item')
            
            for item in product_items[:limit]:
                try:
                    title = await item.query_selector('.goods-title')
                    title_text = await title.inner_text() if title else ""
                    
                    price = await item.query_selector('.goods-price')
                    price_text = await price.inner_text() if price else ""
                    
                    stock = await item.query_selector('.goods-stock')
                    stock_text = await stock.inner_text() if stock else ""
                    
                    product_id = await item.get_attribute('data-goods-id')
                    
                    products.append({
                        'product_id': product_id,
                        'title': title_text,
                        'price': price_text,
                        'stock': stock_text,
                        'platform': 'douyin'
                    })
                except Exception as e:
                    logger.error(f"解析商品项失败: {str(e)}")
            
            return products
            
        except Exception as e:
            logger.error(f"搜索抖音商品失败: {str(e)}")
            return []
    
    async def get_customer_orders(self, customer_id: str) -> List[Dict]:
        """获取客户订单列表"""
        try:
            # 访问订单管理页面
            await self.page.goto("https://fxg.jinritemai.com/ffa/mshop/order/list")
            await asyncio.sleep(2)
            
            # 搜索客户订单
            search_input = await self.page.query_selector('.customer-search')
            if search_input:
                await search_input.fill(customer_id)
                
                search_button = await self.page.query_selector('.search-btn')
                if search_button:
                    await search_button.click()
                    await asyncio.sleep(2)
            
            orders = []
            order_items = await self.page.query_selector_all('.order-item')
            
            for item in order_items:
                try:
                    order_id = await item.get_attribute('data-order-id')
                    status = await item.query_selector('.order-status')
                    status_text = await status.inner_text() if status else ""
                    
                    amount = await item.query_selector('.order-amount')
                    amount_text = await amount.inner_text() if amount else ""
                    
                    orders.append({
                        'order_id': order_id,
                        'status': status_text,
                        'amount': amount_text,
                        'customer_id': customer_id,
                        'platform': 'douyin'
                    })
                except Exception as e:
                    logger.error(f"解析订单项失败: {str(e)}")
            
            return orders
            
        except Exception as e:
            logger.error(f"获取客户订单失败: {str(e)}")
            return []
    
    async def get_live_rooms(self) -> List[Dict]:
        """获取直播间列表"""
        try:
            await self.page.goto("https://fxg.jinritemai.com/ffa/mshop/live/live_list")
            await asyncio.sleep(2)
            
            rooms = []
            room_items = await self.page.query_selector_all('.live-room')
            
            for item in room_items:
                try:
                    room_id = await item.get_attribute('data-room-id')
                    title = await item.query_selector('.room-title')
                    title_text = await title.inner_text() if title else ""
                    
                    status = await item.query_selector('.room-status')
                    status_text = await status.inner_text() if status else ""
                    
                    viewer_count = await item.query_selector('.viewer-count')
                    viewer_count_text = await viewer_count.inner_text() if viewer_count else "0"
                    
                    rooms.append({
                        'room_id': room_id,
                        'title': title_text,
                        'status': status_text,
                        'viewer_count': viewer_count_text,
                        'platform': 'douyin'
                    })
                except Exception as e:
                    logger.error(f"解析直播间项失败: {str(e)}")
            
            return rooms
            
        except Exception as e:
            logger.error(f"获取直播间列表失败: {str(e)}")
            return []
    
    async def start_live(self, title: str, cover_image: str = None) -> bool:
        """开始直播"""
        try:
            await self.page.goto("https://fxg.jinritemai.com/ffa/mshop/live/create")
            await asyncio.sleep(2)
            
            # 输入直播标题
            title_input = await self.page.query_selector('.live-title-input')
            if title_input:
                await title_input.fill(title)
            
            # 上传封面图片
            if cover_image:
                file_input = await self.page.query_selector('input[type="file"]')
                if file_input:
                    await file_input.set_input_files(cover_image)
            
            # 开始直播
            start_button = await self.page.query_selector('.start-live-btn')
            if start_button:
                await start_button.click()
                await asyncio.sleep(3)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"开始直播失败: {str(e)}")
            return False
    
    async def end_live(self, room_id: str) -> bool:
        """结束直播"""
        try:
            await self.page.goto(f"https://fxg.jinritemai.com/ffa/mshop/live/live_room/{room_id}")
            await asyncio.sleep(2)
            
            # 结束直播
            end_button = await self.page.query_selector('.end-live-btn')
            if end_button:
                await end_button.click()
                
                # 确认结束
                confirm_button = await self.page.query_selector('.confirm-end-btn')
                if confirm_button:
                    await confirm_button.click()
                    await asyncio.sleep(2)
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"结束直播失败: {str(e)}")
            return False 