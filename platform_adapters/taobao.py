"""
淘宝平台适配器
"""
import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

from .base import EcommercePlatformAdapter, PlatformMessage, MessageType, MessageDirection, PlatformAccount

logger = logging.getLogger(__name__)


class TaobaoAdapter(EcommercePlatformAdapter):
    """淘宝平台适配器"""
    
    def __init__(self, account: PlatformAccount):
        super().__init__(account)
        self.driver = None
        self.session_cookies = None
        self.last_message_check = 0
        self.message_polling_interval = 5  # 秒
        self.is_polling = False
        
    @property
    def platform_name(self) -> str:
        return "淘宝"
    
    @property
    def supported_message_types(self) -> List[MessageType]:
        return [
            MessageType.TEXT,
            MessageType.IMAGE,
            MessageType.LINK,
            MessageType.PRODUCT
        ]
    
    async def connect(self) -> bool:
        """连接到淘宝"""
        try:
            logger.info(f"正在连接淘宝账号: {self.account.account_name}")
            
            # 初始化Chrome浏览器
            chrome_options = Options()
            if self.account.settings.get('headless', False):
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # 登录淘宝
            await self._login()
            
            # 验证登录状态
            if await self._verify_login():
                self.is_connected = True
                logger.info("淘宝连接成功")
                
                # 开始消息轮询
                asyncio.create_task(self._start_message_polling())
                return True
            else:
                logger.error("淘宝登录验证失败")
                return False
                
        except Exception as e:
            logger.error(f"连接淘宝失败: {str(e)}", exc_info=True)
            return False
    
    async def disconnect(self) -> bool:
        """断开淘宝连接"""
        try:
            self.is_polling = False
            if self.driver:
                self.driver.quit()
                self.driver = None
            self.is_connected = False
            logger.info("淘宝连接已断开")
            return True
        except Exception as e:
            logger.error(f"断开淘宝连接失败: {str(e)}")
            return False
    
    async def _login(self):
        """登录淘宝"""
        try:
            # 访问淘宝登录页面
            self.driver.get("https://login.taobao.com/")
            
            # 检查是否有保存的cookies
            saved_cookies = self.account.credentials.get('cookies')
            if saved_cookies:
                for cookie in saved_cookies:
                    self.driver.add_cookie(cookie)
                self.driver.refresh()
                return
            
            # 手动登录流程
            username = self.account.credentials.get('username')
            password = self.account.credentials.get('password')
            
            if username and password:
                # 输入用户名密码
                username_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "fm-login-id"))
                )
                password_input = self.driver.find_element(By.ID, "fm-login-password")
                
                username_input.send_keys(username)
                password_input.send_keys(password)
                
                # 点击登录按钮
                login_button = self.driver.find_element(By.CSS_SELECTOR, ".fm-button.fm-submit.password-login")
                login_button.click()
                
                # 等待登录完成或需要验证码
                await asyncio.sleep(3)
                
                # 检查是否需要滑块验证
                if self._check_slider_verification():
                    logger.warning("检测到滑块验证，需要手动处理")
                    # 这里可以集成自动滑块验证逻辑
                    
            else:
                logger.warning("未提供用户名密码，需要手动登录")
                # 等待手动登录
                input("请手动完成登录后按回车继续...")
            
            # 保存cookies
            cookies = self.driver.get_cookies()
            self.session_cookies = cookies
            
        except Exception as e:
            logger.error(f"淘宝登录失败: {str(e)}")
            raise
    
    async def _verify_login(self) -> bool:
        """验证登录状态"""
        try:
            # 访问卖家中心
            self.driver.get("https://myseller.taobao.com/")
            await asyncio.sleep(2)
            
            # 检查是否成功进入卖家中心
            current_url = self.driver.current_url
            if "myseller.taobao.com" in current_url:
                logger.info("淘宝登录验证成功")
                return True
            else:
                logger.error("淘宝登录验证失败")
                return False
                
        except Exception as e:
            logger.error(f"验证淘宝登录状态失败: {str(e)}")
            return False
    
    def _check_slider_verification(self) -> bool:
        """检查是否有滑块验证"""
        try:
            slider_elements = self.driver.find_elements(By.CSS_SELECTOR, ".nc_wrapper")
            return len(slider_elements) > 0
        except:
            return False
    
    async def _start_message_polling(self):
        """开始消息轮询"""
        self.is_polling = True
        logger.info("开始淘宝消息轮询")
        
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
            # 访问千牛消息页面
            self.driver.get("https://qianniu.taobao.com/")
            await asyncio.sleep(2)
            
            # 查找未读消息
            message_elements = self.driver.find_elements(
                By.CSS_SELECTOR, 
                ".message-item.unread"
            )
            
            for element in message_elements:
                try:
                    message = await self._parse_message_element(element)
                    if message:
                        await self._handle_message(message)
                except Exception as e:
                    logger.error(f"解析消息失败: {str(e)}")
                    
        except Exception as e:
            logger.error(f"检查新消息失败: {str(e)}")
    
    async def _parse_message_element(self, element) -> Optional[PlatformMessage]:
        """解析消息元素"""
        try:
            # 提取消息信息
            message_id = element.get_attribute("data-message-id")
            sender_name = element.find_element(By.CSS_SELECTOR, ".sender-name").text
            content = element.find_element(By.CSS_SELECTOR, ".message-content").text
            timestamp = element.get_attribute("data-timestamp")
            
            # 构建消息对象
            message = PlatformMessage(
                message_id=message_id or f"tb_{int(time.time())}",
                conversation_id=f"tb_conv_{sender_name}",
                sender_id=sender_name,
                sender_name=sender_name,
                recipient_id=self.account.account_id,
                recipient_name=self.account.account_name,
                message_type=MessageType.TEXT,
                content=content,
                direction=MessageDirection.INBOUND,
                timestamp=float(timestamp) if timestamp else time.time(),
                metadata={
                    'platform': 'taobao',
                    'raw_element': str(element.get_attribute('outerHTML'))
                }
            )
            
            return message
            
        except Exception as e:
            logger.error(f"解析消息元素失败: {str(e)}")
            return None
    
    async def send_message(self, message: PlatformMessage) -> bool:
        """发送消息"""
        try:
            logger.info(f"发送淘宝消息: {message.content[:50]}...")
            
            # 找到对话窗口
            conversation_selector = f"[data-conversation-id='{message.conversation_id}']"
            conversation_element = self.driver.find_element(By.CSS_SELECTOR, conversation_selector)
            conversation_element.click()
            
            await asyncio.sleep(1)
            
            # 找到输入框
            input_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".message-input"))
            )
            
            # 输入消息内容
            input_box.clear()
            input_box.send_keys(message.content)
            
            # 发送消息
            send_button = self.driver.find_element(By.CSS_SELECTOR, ".send-button")
            send_button.click()
            
            await asyncio.sleep(1)
            logger.info("淘宝消息发送成功")
            return True
            
        except Exception as e:
            logger.error(f"发送淘宝消息失败: {str(e)}")
            return False
    
    async def get_conversations(self, limit: int = 50) -> List[Dict]:
        """获取对话列表"""
        try:
            # 访问对话列表页面
            self.driver.get("https://qianniu.taobao.com/conversations")
            await asyncio.sleep(2)
            
            conversations = []
            conversation_elements = self.driver.find_elements(
                By.CSS_SELECTOR, 
                ".conversation-item"
            )[:limit]
            
            for element in conversation_elements:
                try:
                    conversation_id = element.get_attribute("data-conversation-id")
                    customer_name = element.find_element(By.CSS_SELECTOR, ".customer-name").text
                    last_message = element.find_element(By.CSS_SELECTOR, ".last-message").text
                    timestamp = element.get_attribute("data-timestamp")
                    
                    conversations.append({
                        'conversation_id': conversation_id,
                        'customer_name': customer_name,
                        'last_message': last_message,
                        'timestamp': timestamp,
                        'platform': 'taobao'
                    })
                except Exception as e:
                    logger.error(f"解析对话元素失败: {str(e)}")
            
            return conversations
            
        except Exception as e:
            logger.error(f"获取淘宝对话列表失败: {str(e)}")
            return []
    
    async def get_conversation_messages(
        self, 
        conversation_id: str, 
        limit: int = 100
    ) -> List[PlatformMessage]:
        """获取对话消息"""
        try:
            # 打开指定对话
            conversation_url = f"https://qianniu.taobao.com/conversation/{conversation_id}"
            self.driver.get(conversation_url)
            await asyncio.sleep(2)
            
            messages = []
            message_elements = self.driver.find_elements(
                By.CSS_SELECTOR, 
                ".message-item"
            )[-limit:]  # 获取最新的消息
            
            for element in message_elements:
                message = await self._parse_message_element(element)
                if message:
                    messages.append(message)
            
            return messages
            
        except Exception as e:
            logger.error(f"获取淘宝对话消息失败: {str(e)}")
            return []
    
    async def mark_message_read(self, message_id: str) -> bool:
        """标记消息为已读"""
        try:
            # 找到消息元素并标记为已读
            message_element = self.driver.find_element(
                By.CSS_SELECTOR, 
                f"[data-message-id='{message_id}']"
            )
            
            # 点击消息或执行标记已读的操作
            message_element.click()
            await asyncio.sleep(0.5)
            
            return True
            
        except Exception as e:
            logger.error(f"标记淘宝消息已读失败: {str(e)}")
            return False
    
    async def get_product_info(self, product_id: str) -> Optional[Dict]:
        """获取商品信息"""
        try:
            # 访问商品详情页
            product_url = f"https://item.taobao.com/item.htm?id={product_id}"
            self.driver.get(product_url)
            await asyncio.sleep(2)
            
            # 提取商品信息
            title = self.driver.find_element(By.CSS_SELECTOR, ".tb-main-title").text
            price = self.driver.find_element(By.CSS_SELECTOR, ".tb-price").text
            
            # 提取商品图片
            images = []
            img_elements = self.driver.find_elements(By.CSS_SELECTOR, ".tb-thumb img")
            for img in img_elements:
                src = img.get_attribute("src")
                if src:
                    images.append(src)
            
            return {
                'product_id': product_id,
                'title': title,
                'price': price,
                'images': images,
                'platform': 'taobao',
                'url': product_url
            }
            
        except Exception as e:
            logger.error(f"获取淘宝商品信息失败: {str(e)}")
            return None
    
    async def get_order_info(self, order_id: str) -> Optional[Dict]:
        """获取订单信息"""
        try:
            # 访问订单详情页
            order_url = f"https://trade.taobao.com/trade/detail/trade_order_detail.htm?trade_id={order_id}"
            self.driver.get(order_url)
            await asyncio.sleep(2)
            
            # 提取订单信息
            order_status = self.driver.find_element(By.CSS_SELECTOR, ".order-status").text
            total_amount = self.driver.find_element(By.CSS_SELECTOR, ".total-amount").text
            
            return {
                'order_id': order_id,
                'status': order_status,
                'total_amount': total_amount,
                'platform': 'taobao'
            }
            
        except Exception as e:
            logger.error(f"获取淘宝订单信息失败: {str(e)}")
            return None
    
    async def search_products(self, query: str, limit: int = 20) -> List[Dict]:
        """搜索商品"""
        try:
            # 访问搜索页面
            search_url = f"https://s.taobao.com/search?q={query}"
            self.driver.get(search_url)
            await asyncio.sleep(2)
            
            products = []
            product_elements = self.driver.find_elements(
                By.CSS_SELECTOR, 
                ".item"
            )[:limit]
            
            for element in product_elements:
                try:
                    title = element.find_element(By.CSS_SELECTOR, ".title").text
                    price = element.find_element(By.CSS_SELECTOR, ".price").text
                    link = element.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                    
                    products.append({
                        'title': title,
                        'price': price,
                        'link': link,
                        'platform': 'taobao'
                    })
                except Exception as e:
                    logger.error(f"解析商品元素失败: {str(e)}")
            
            return products
            
        except Exception as e:
            logger.error(f"搜索淘宝商品失败: {str(e)}")
            return []
    
    async def get_customer_orders(self, customer_id: str) -> List[Dict]:
        """获取客户订单列表"""
        try:
            # 访问客户订单页面
            orders_url = f"https://trade.taobao.com/trade/itemlist/list_sold_items.htm?buyer_nick={customer_id}"
            self.driver.get(orders_url)
            await asyncio.sleep(2)
            
            orders = []
            order_elements = self.driver.find_elements(By.CSS_SELECTOR, ".order-item")
            
            for element in order_elements:
                try:
                    order_id = element.get_attribute("data-order-id")
                    status = element.find_element(By.CSS_SELECTOR, ".order-status").text
                    amount = element.find_element(By.CSS_SELECTOR, ".order-amount").text
                    
                    orders.append({
                        'order_id': order_id,
                        'status': status,
                        'amount': amount,
                        'customer_id': customer_id,
                        'platform': 'taobao'
                    })
                except Exception as e:
                    logger.error(f"解析订单元素失败: {str(e)}")
            
            return orders
            
        except Exception as e:
            logger.error(f"获取客户订单失败: {str(e)}")
            return [] 