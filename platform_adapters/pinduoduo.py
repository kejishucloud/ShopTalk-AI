"""
拼多多平台适配器
"""
import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

from .base import EcommercePlatformAdapter, PlatformMessage, MessageType, MessageDirection, PlatformAccount

logger = logging.getLogger(__name__)


class PinduoduoAdapter(EcommercePlatformAdapter):
    """拼多多平台适配器"""
    
    def __init__(self, account: PlatformAccount):
        super().__init__(account)
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.is_polling = False
        self.message_polling_interval = 8  # 秒
        
    @property
    def platform_name(self) -> str:
        return "拼多多"
    
    @property
    def supported_message_types(self) -> List[MessageType]:
        return [
            MessageType.TEXT,
            MessageType.IMAGE,
            MessageType.PRODUCT,
            MessageType.LINK
        ]
    
    async def connect(self) -> bool:
        """连接到拼多多"""
        try:
            logger.info(f"正在连接拼多多账号: {self.account.account_name}")
            
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
            
            # 登录拼多多
            await self._login()
            
            # 验证登录状态
            if await self._verify_login():
                self.is_connected = True
                logger.info("拼多多连接成功")
                
                # 开始消息轮询
                asyncio.create_task(self._start_message_polling())
                return True
            else:
                logger.error("拼多多登录验证失败")
                return False
                
        except Exception as e:
            logger.error(f"连接拼多多失败: {str(e)}", exc_info=True)
            return False
    
    async def disconnect(self) -> bool:
        """断开拼多多连接"""
        try:
            self.is_polling = False
            
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
                
            self.is_connected = False
            logger.info("拼多多连接已断开")
            return True
        except Exception as e:
            logger.error(f"断开拼多多连接失败: {str(e)}")
            return False
    
    async def _login(self):
        """登录拼多多"""
        try:
            # 访问拼多多商家后台
            await self.page.goto("https://mms.pinduoduo.com/")
            await asyncio.sleep(3)
            
            # 检查是否有保存的cookies
            saved_cookies = self.account.credentials.get('cookies')
            if saved_cookies:
                await self.context.add_cookies(saved_cookies)
                await self.page.reload()
                await asyncio.sleep(2)
                return
            
            # 手机号登录
            phone = self.account.credentials.get('phone')
            password = self.account.credentials.get('password')
            
            if phone and password:
                # 输入手机号
                phone_input = await self.page.wait_for_selector('input[placeholder*="手机号"]', timeout=10000)
                await phone_input.fill(phone)
                
                # 输入密码
                password_input = await self.page.wait_for_selector('input[type="password"]')
                await password_input.fill(password)
                
                # 点击登录
                login_button = await self.page.wait_for_selector('.login-btn')
                await login_button.click()
                
                # 等待登录完成
                await asyncio.sleep(3)
                
                # 处理可能的验证码
                if await self.page.query_selector('.captcha'):
                    logger.warning("检测到验证码，需要手动处理")
                    await self.page.wait_for_url("**/home", timeout=60000)
            else:
                logger.warning("未提供登录凭据，需要手动登录")
                await self.page.wait_for_url("**/home", timeout=60000)
            
            # 保存cookies
            cookies = await self.context.cookies()
            # 这里可以保存cookies到数据库
            
        except Exception as e:
            logger.error(f"拼多多登录失败: {str(e)}")
            raise
    
    async def _verify_login(self) -> bool:
        """验证登录状态"""
        try:
            # 检查是否在商家后台首页
            current_url = self.page.url
            if "mms.pinduoduo.com" in current_url:
                # 检查用户信息是否存在
                user_info = await self.page.query_selector('.user-info')
                if user_info:
                    logger.info("拼多多登录验证成功")
                    return True
            
            logger.error("拼多多登录验证失败")
            return False
                
        except Exception as e:
            logger.error(f"验证拼多多登录状态失败: {str(e)}")
            return False
    
    async def _start_message_polling(self):
        """开始消息轮询"""
        self.is_polling = True
        logger.info("开始拼多多消息轮询")
        
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
            # 访问客服消息页面
            await self.page.goto("https://mms.pinduoduo.com/message/chat")
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
                message_id=f"pdd_{int(time.time())}_{hash(content_text)}",
                conversation_id=f"pdd_conv_{customer_id}",
                sender_id=customer_id or customer_name_text,
                sender_name=customer_name_text,
                recipient_id=self.account.account_id,
                recipient_name=self.account.account_name,
                message_type=MessageType.TEXT,
                content=content_text,
                direction=MessageDirection.INBOUND,
                timestamp=float(timestamp) if timestamp else time.time(),
                metadata={
                    'platform': 'pinduoduo',
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
            logger.info(f"发送拼多多消息: {message.content[:50]}...")
            
            # 访问客服页面
            await self.page.goto("https://mms.pinduoduo.com/message/chat")
            await asyncio.sleep(2)
            
            # 找到对话
            customer_id = message.conversation_id.replace("pdd_conv_", "")
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
            logger.info("拼多多消息发送成功")
            return True
            
        except Exception as e:
            logger.error(f"发送拼多多消息失败: {str(e)}")
            return False
    
    async def get_conversations(self, limit: int = 50) -> List[Dict]:
        """获取对话列表"""
        try:
            await self.page.goto("https://mms.pinduoduo.com/message/chat")
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
                        'conversation_id': f"pdd_conv_{customer_id}",
                        'customer_name': customer_name_text,
                        'customer_id': customer_id,
                        'last_message': last_message_text,
                        'timestamp': timestamp,
                        'platform': 'pinduoduo'
                    })
                except Exception as e:
                    logger.error(f"解析对话项失败: {str(e)}")
            
            return conversations
            
        except Exception as e:
            logger.error(f"获取拼多多对话列表失败: {str(e)}")
            return []
    
    async def get_conversation_messages(
        self, 
        conversation_id: str, 
        limit: int = 100
    ) -> List[PlatformMessage]:
        """获取对话消息"""
        try:
            # 打开指定对话
            customer_id = conversation_id.replace("pdd_conv_", "")
            await self.page.goto("https://mms.pinduoduo.com/message/chat")
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
                        message_id=f"pdd_{timestamp}_{hash(content_text)}",
                        conversation_id=conversation_id,
                        sender_id=self.account.account_id if is_self else customer_id,
                        sender_name=self.account.account_name if is_self else customer_id,
                        recipient_id=customer_id if is_self else self.account.account_id,
                        recipient_name=customer_id if is_self else self.account.account_name,
                        message_type=MessageType.TEXT,
                        content=content_text,
                        direction=MessageDirection.OUTBOUND if is_self else MessageDirection.INBOUND,
                        timestamp=float(timestamp) if timestamp else time.time(),
                        metadata={'platform': 'pinduoduo'}
                    )
                    
                    messages.append(message)
                except Exception as e:
                    logger.error(f"解析消息失败: {str(e)}")
            
            return messages
            
        except Exception as e:
            logger.error(f"获取拼多多对话消息失败: {str(e)}")
            return []
    
    async def mark_message_read(self, message_id: str) -> bool:
        """标记消息为已读"""
        try:
            # 拼多多通常在查看消息时自动标记为已读
            return True
        except Exception as e:
            logger.error(f"标记拼多多消息已读失败: {str(e)}")
            return False
    
    async def get_product_info(self, product_id: str) -> Optional[Dict]:
        """获取商品信息"""
        try:
            # 访问商品管理页面
            await self.page.goto(f"https://mms.pinduoduo.com/goods/goods-edit?goods_id={product_id}")
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
                'platform': 'pinduoduo'
            }
            
        except Exception as e:
            logger.error(f"获取拼多多商品信息失败: {str(e)}")
            return None
    
    async def get_order_info(self, order_id: str) -> Optional[Dict]:
        """获取订单信息"""
        try:
            # 访问订单详情页
            await self.page.goto(f"https://mms.pinduoduo.com/order/order-detail?order_sn={order_id}")
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
                'platform': 'pinduoduo'
            }
            
        except Exception as e:
            logger.error(f"获取拼多多订单信息失败: {str(e)}")
            return None
    
    async def search_products(self, query: str, limit: int = 20) -> List[Dict]:
        """搜索商品"""
        try:
            # 访问商品管理页面
            await self.page.goto("https://mms.pinduoduo.com/goods/goods-list")
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
                        'platform': 'pinduoduo'
                    })
                except Exception as e:
                    logger.error(f"解析商品项失败: {str(e)}")
            
            return products
            
        except Exception as e:
            logger.error(f"搜索拼多多商品失败: {str(e)}")
            return []
    
    async def get_customer_orders(self, customer_id: str) -> List[Dict]:
        """获取客户订单列表"""
        try:
            # 访问订单管理页面
            await self.page.goto("https://mms.pinduoduo.com/order/order-list")
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
                        'platform': 'pinduoduo'
                    })
                except Exception as e:
                    logger.error(f"解析订单项失败: {str(e)}")
            
            return orders
            
        except Exception as e:
            logger.error(f"获取客户订单失败: {str(e)}")
            return []
    
    async def update_product_price(self, product_id: str, new_price: float) -> bool:
        """更新商品价格"""
        try:
            await self.page.goto(f"https://mms.pinduoduo.com/goods/goods-edit?goods_id={product_id}")
            await asyncio.sleep(2)
            
            # 修改价格
            price_input = await self.page.query_selector('.price-input')
            if price_input:
                await price_input.fill(str(new_price))
                
                # 保存修改
                save_button = await self.page.query_selector('.save-btn')
                if save_button:
                    await save_button.click()
                    await asyncio.sleep(2)
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"更新商品价格失败: {str(e)}")
            return False
    
    async def update_product_stock(self, product_id: str, new_stock: int) -> bool:
        """更新商品库存"""
        try:
            await self.page.goto(f"https://mms.pinduoduo.com/goods/goods-edit?goods_id={product_id}")
            await asyncio.sleep(2)
            
            # 修改库存
            stock_input = await self.page.query_selector('.stock-input')
            if stock_input:
                await stock_input.fill(str(new_stock))
                
                # 保存修改
                save_button = await self.page.query_selector('.save-btn')
                if save_button:
                    await save_button.click()
                    await asyncio.sleep(2)
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"更新商品库存失败: {str(e)}")
            return False 