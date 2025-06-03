"""
京东平台适配器
"""
import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

from .base import EcommercePlatformAdapter, PlatformMessage, MessageType, MessageDirection, PlatformAccount

logger = logging.getLogger(__name__)


class JingdongAdapter(EcommercePlatformAdapter):
    """京东平台适配器"""
    
    def __init__(self, account: PlatformAccount):
        super().__init__(account)
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.is_polling = False
        self.message_polling_interval = 6  # 秒
        
    @property
    def platform_name(self) -> str:
        return "京东"
    
    @property
    def supported_message_types(self) -> List[MessageType]:
        return [
            MessageType.TEXT,
            MessageType.IMAGE,
            MessageType.PRODUCT,
            MessageType.LINK,
            MessageType.FILE
        ]
    
    async def connect(self) -> bool:
        """连接到京东"""
        try:
            logger.info(f"正在连接京东账号: {self.account.account_name}")
            
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
            
            # 登录京东
            await self._login()
            
            # 验证登录状态
            if await self._verify_login():
                self.is_connected = True
                logger.info("京东连接成功")
                
                # 开始消息轮询
                asyncio.create_task(self._start_message_polling())
                return True
            else:
                logger.error("京东登录验证失败")
                return False
                
        except Exception as e:
            logger.error(f"连接京东失败: {str(e)}", exc_info=True)
            return False
    
    async def disconnect(self) -> bool:
        """断开京东连接"""
        try:
            self.is_polling = False
            
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
                
            self.is_connected = False
            logger.info("京东连接已断开")
            return True
        except Exception as e:
            logger.error(f"断开京东连接失败: {str(e)}")
            return False
    
    async def _login(self):
        """登录京东"""
        try:
            # 访问京麦商家后台
            await self.page.goto("https://mai.jd.com/")
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
            
            # 账号密码登录
            username = self.account.credentials.get('username')
            password = self.account.credentials.get('password')
            
            if username and password:
                # 输入用户名
                username_input = await self.page.wait_for_selector('#loginname', timeout=10000)
                await username_input.fill(username)
                
                # 输入密码
                password_input = await self.page.wait_for_selector('#nloginpwd')
                await password_input.fill(password)
                
                # 点击登录
                submit_button = await self.page.wait_for_selector('#loginsubmit')
                await submit_button.click()
                
                # 等待登录完成
                await asyncio.sleep(3)
                
                # 处理可能的验证码
                if await self.page.query_selector('.JDJRV-slide-btn'):
                    logger.warning("检测到滑块验证，需要手动处理")
                    await self.page.wait_for_url("**/index", timeout=60000)
            else:
                logger.warning("未提供登录凭据，需要手动登录")
                await self.page.wait_for_url("**/index", timeout=60000)
            
            # 保存cookies
            cookies = await self.context.cookies()
            # 这里可以保存cookies到数据库
            
        except Exception as e:
            logger.error(f"京东登录失败: {str(e)}")
            raise
    
    async def _verify_login(self) -> bool:
        """验证登录状态"""
        try:
            # 检查是否在京麦首页
            current_url = self.page.url
            if "mai.jd.com" in current_url:
                # 检查用户信息是否存在
                user_info = await self.page.query_selector('.user-info')
                if user_info:
                    logger.info("京东登录验证成功")
                    return True
            
            logger.error("京东登录验证失败")
            return False
                
        except Exception as e:
            logger.error(f"验证京东登录状态失败: {str(e)}")
            return False
    
    async def _start_message_polling(self):
        """开始消息轮询"""
        self.is_polling = True
        logger.info("开始京东消息轮询")
        
        while self.is_polling and self.is_connected:
            try:
                await self._check_new_messages()
                await asyncio.sleep(self.message_polling_interval)
            except Exception as e:
                logger.error(f"消息轮询错误: {str(e)}")
                await asyncio.sleep(self.message_polling_interval)
    
    async def _check_new_messages(self):
        """检查新消息"""
        try:
            # 访问京麦客服页面
            await self.page.goto("https://mai.jd.com/index.action#/customerService/chat")
            await asyncio.sleep(2)
            
            # 查找未读消息
            unread_items = await self.page.query_selector_all('.chat-list-item.unread')
            
            for item in unread_items:
                try:
                    message = await self._parse_message_item(item)
                    if message:
                        await self._handle_message(message)
                except Exception as e:
                    logger.error(f"解析消息失败: {str(e)}")
                    
        except Exception as e:
            logger.error(f"检查新消息失败: {str(e)}")
    
    async def _parse_message_item(self, item) -> Optional[PlatformMessage]:
        """解析消息项"""
        try:
            # 提取消息信息
            customer_name = await item.query_selector('.customer-name')
            customer_name_text = await customer_name.inner_text() if customer_name else ""
            
            content = await item.query_selector('.last-message')
            content_text = await content.inner_text() if content else ""
            
            timestamp = await item.get_attribute('data-time')
            customer_id = await item.get_attribute('data-customer-id')
            
            # 构建消息对象
            message = PlatformMessage(
                message_id=f"jd_{int(time.time())}_{hash(content_text)}",
                conversation_id=f"jd_conv_{customer_id}",
                sender_id=customer_id or customer_name_text,
                sender_name=customer_name_text,
                recipient_id=self.account.account_id,
                recipient_name=self.account.account_name,
                message_type=MessageType.TEXT,
                content=content_text,
                direction=MessageDirection.INBOUND,
                timestamp=float(timestamp) if timestamp else time.time(),
                metadata={
                    'platform': 'jingdong',
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
            logger.info(f"发送京东消息: {message.content[:50]}...")
            
            # 访问客服页面
            await self.page.goto("https://mai.jd.com/index.action#/customerService/chat")
            await asyncio.sleep(2)
            
            # 找到对话
            customer_id = message.conversation_id.replace("jd_conv_", "")
            chat_item = await self.page.query_selector(f'[data-customer-id="{customer_id}"]')
            if chat_item:
                await chat_item.click()
                await asyncio.sleep(1)
            
            # 输入消息
            input_box = await self.page.wait_for_selector('.chat-input')
            await input_box.fill(message.content)
            
            # 发送消息
            send_button = await self.page.query_selector('.send-btn')
            await send_button.click()
            
            await asyncio.sleep(1)
            logger.info("京东消息发送成功")
            return True
            
        except Exception as e:
            logger.error(f"发送京东消息失败: {str(e)}")
            return False
    
    async def get_conversations(self, limit: int = 50) -> List[Dict]:
        """获取对话列表"""
        try:
            await self.page.goto("https://mai.jd.com/index.action#/customerService/chat")
            await asyncio.sleep(2)
            
            conversations = []
            chat_items = await self.page.query_selector_all('.chat-list-item')
            
            for item in chat_items[:limit]:
                try:
                    customer_name = await item.query_selector('.customer-name')
                    customer_name_text = await customer_name.inner_text() if customer_name else ""
                    
                    last_message = await item.query_selector('.last-message')
                    last_message_text = await last_message.inner_text() if last_message else ""
                    
                    timestamp = await item.get_attribute('data-time')
                    customer_id = await item.get_attribute('data-customer-id')
                    
                    conversations.append({
                        'conversation_id': f"jd_conv_{customer_id}",
                        'customer_name': customer_name_text,
                        'customer_id': customer_id,
                        'last_message': last_message_text,
                        'timestamp': timestamp,
                        'platform': 'jingdong'
                    })
                except Exception as e:
                    logger.error(f"解析对话项失败: {str(e)}")
            
            return conversations
            
        except Exception as e:
            logger.error(f"获取京东对话列表失败: {str(e)}")
            return []
    
    async def get_conversation_messages(
        self, 
        conversation_id: str, 
        limit: int = 100
    ) -> List[PlatformMessage]:
        """获取对话消息"""
        try:
            # 打开指定对话
            customer_id = conversation_id.replace("jd_conv_", "")
            await self.page.goto("https://mai.jd.com/index.action#/customerService/chat")
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
                    content = await item.query_selector('.message-content')
                    content_text = await content.inner_text() if content else ""
                    
                    sender = await item.query_selector('.sender')
                    is_self = await sender.get_attribute('data-self') == 'true' if sender else False
                    
                    timestamp = await item.get_attribute('data-time')
                    
                    message = PlatformMessage(
                        message_id=f"jd_{timestamp}_{hash(content_text)}",
                        conversation_id=conversation_id,
                        sender_id=self.account.account_id if is_self else customer_id,
                        sender_name=self.account.account_name if is_self else customer_id,
                        recipient_id=customer_id if is_self else self.account.account_id,
                        recipient_name=customer_id if is_self else self.account.account_name,
                        message_type=MessageType.TEXT,
                        content=content_text,
                        direction=MessageDirection.OUTBOUND if is_self else MessageDirection.INBOUND,
                        timestamp=float(timestamp) if timestamp else time.time(),
                        metadata={'platform': 'jingdong'}
                    )
                    
                    messages.append(message)
                except Exception as e:
                    logger.error(f"解析消息失败: {str(e)}")
            
            return messages
            
        except Exception as e:
            logger.error(f"获取京东对话消息失败: {str(e)}")
            return []
    
    async def mark_message_read(self, message_id: str) -> bool:
        """标记消息为已读"""
        try:
            # 京东通常在查看消息时自动标记为已读
            return True
        except Exception as e:
            logger.error(f"标记京东消息已读失败: {str(e)}")
            return False
    
    async def get_product_info(self, product_id: str) -> Optional[Dict]:
        """获取商品信息"""
        try:
            # 访问商品管理页面
            await self.page.goto(f"https://mai.jd.com/index.action#/goods/edit/{product_id}")
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
                'platform': 'jingdong'
            }
            
        except Exception as e:
            logger.error(f"获取京东商品信息失败: {str(e)}")
            return None
    
    async def get_order_info(self, order_id: str) -> Optional[Dict]:
        """获取订单信息"""
        try:
            # 访问订单详情页
            await self.page.goto(f"https://mai.jd.com/index.action#/order/detail/{order_id}")
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
                'platform': 'jingdong'
            }
            
        except Exception as e:
            logger.error(f"获取京东订单信息失败: {str(e)}")
            return None
    
    async def search_products(self, query: str, limit: int = 20) -> List[Dict]:
        """搜索商品"""
        try:
            # 访问商品管理页面
            await self.page.goto("https://mai.jd.com/index.action#/goods/list")
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
                        'platform': 'jingdong'
                    })
                except Exception as e:
                    logger.error(f"解析商品项失败: {str(e)}")
            
            return products
            
        except Exception as e:
            logger.error(f"搜索京东商品失败: {str(e)}")
            return []
    
    async def get_customer_orders(self, customer_id: str) -> List[Dict]:
        """获取客户订单列表"""
        try:
            # 访问订单管理页面
            await self.page.goto("https://mai.jd.com/index.action#/order/list")
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
                        'platform': 'jingdong'
                    })
                except Exception as e:
                    logger.error(f"解析订单项失败: {str(e)}")
            
            return orders
            
        except Exception as e:
            logger.error(f"获取客户订单失败: {str(e)}")
            return []
    
    async def get_store_info(self) -> Optional[Dict]:
        """获取店铺信息"""
        try:
            await self.page.goto("https://mai.jd.com/index.action#/store/info")
            await asyncio.sleep(2)
            
            # 提取店铺信息
            store_name = await self.page.query_selector('.store-name')
            store_name_text = await store_name.inner_text() if store_name else ""
            
            store_level = await self.page.query_selector('.store-level')
            store_level_text = await store_level.inner_text() if store_level else ""
            
            return {
                'store_name': store_name_text,
                'store_level': store_level_text,
                'platform': 'jingdong'
            }
            
        except Exception as e:
            logger.error(f"获取店铺信息失败: {str(e)}")
            return None
    
    async def get_sales_data(self, start_date: str, end_date: str) -> Optional[Dict]:
        """获取销售数据"""
        try:
            await self.page.goto("https://mai.jd.com/index.action#/data/sales")
            await asyncio.sleep(2)
            
            # 设置日期范围
            start_input = await self.page.query_selector('.start-date')
            if start_input:
                await start_input.fill(start_date)
            
            end_input = await self.page.query_selector('.end-date')
            if end_input:
                await end_input.fill(end_date)
            
            # 查询数据
            query_button = await self.page.query_selector('.query-btn')
            if query_button:
                await query_button.click()
                await asyncio.sleep(3)
            
            # 提取销售数据
            total_sales = await self.page.query_selector('.total-sales')
            total_sales_text = await total_sales.inner_text() if total_sales else "0"
            
            order_count = await self.page.query_selector('.order-count')
            order_count_text = await order_count.inner_text() if order_count else "0"
            
            return {
                'total_sales': total_sales_text,
                'order_count': order_count_text,
                'start_date': start_date,
                'end_date': end_date,
                'platform': 'jingdong'
            }
            
        except Exception as e:
            logger.error(f"获取销售数据失败: {str(e)}")
            return None
    
    async def send_product_message(self, customer_id: str, product_id: str) -> bool:
        """发送商品消息"""
        try:
            # 获取商品信息
            product_info = await self.get_product_info(product_id)
            if not product_info:
                return False
            
            # 构建商品消息
            product_message = PlatformMessage(
                message_id=f"jd_product_{int(time.time())}",
                conversation_id=f"jd_conv_{customer_id}",
                sender_id=self.account.account_id,
                sender_name=self.account.account_name,
                recipient_id=customer_id,
                recipient_name=customer_id,
                message_type=MessageType.PRODUCT,
                content=f"商品推荐：{product_info['title']} - 价格：{product_info['price']}",
                direction=MessageDirection.OUTBOUND,
                timestamp=time.time(),
                metadata={
                    'platform': 'jingdong',
                    'product_info': product_info
                }
            )
            
            return await self.send_message(product_message)
            
        except Exception as e:
            logger.error(f"发送商品消息失败: {str(e)}")
            return False 