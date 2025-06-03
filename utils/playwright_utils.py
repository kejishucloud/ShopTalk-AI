"""
Playwright浏览器工具类
"""
import asyncio
import json
import logging
import random
import time
from typing import Dict, List, Optional, Any, Union
from playwright.async_api import async_playwright, Browser, Page, BrowserContext, Playwright
import requests

logger = logging.getLogger(__name__)


class PlaywrightUtils:
    """
    Playwright浏览器工具类，提供：
    1. 启动 Playwright 异步实例
    2. 支持指纹浏览器（Adspower）集成
    3. 反检测功能
    4. 代理支持
    5. 多浏览器管理
    6. 自动化操作工具
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化Playwright工具
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.ads_id: Optional[str] = self.config.get('ads_id')
        self.is_connected = False
        
        # 反检测配置
        self.stealth_config = self.config.get('stealth', {})
        self.proxy_config = self.config.get('proxy', {})
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
    
    async def start(self) -> bool:
        """启动Playwright"""
        try:
            if not self.playwright:
                self.playwright = await async_playwright().start()
                logger.info("Playwright实例已启动")
            
            return await self.connect_browser()
            
        except Exception as e:
            logger.error(f"启动Playwright失败: {str(e)}", exc_info=True)
            return False
    
    async def connect_browser(self) -> bool:
        """连接到浏览器"""
        try:
            if self.ads_id:
                # 连接指纹浏览器
                return await self._connect_fingerprint_browser()
            else:
                # 启动普通浏览器
                return await self._launch_browser()
                
        except Exception as e:
            logger.error(f"连接浏览器失败: {str(e)}", exc_info=True)
            return False
    
    async def _connect_fingerprint_browser(self) -> bool:
        """连接指纹浏览器（Adspower）"""
        try:
            # 启动Adspower浏览器
            open_url = f"http://local.adspower.net:50325/api/v1/browser/start"
            params = {
                'user_id': self.ads_id,
                'open_tabs': 1
            }
            
            response = requests.get(open_url, params=params, timeout=10)
            if response.status_code != 200:
                logger.error(f"Adspower API调用失败: HTTP {response.status_code}")
                return False
            
            result = response.json()
            if result.get('code') != 0:
                logger.error(f"Adspower启动失败: {result.get('msg', '未知错误')}")
                return False
            
            # 获取WebSocket连接地址
            ws_data = result['data']['ws']
            ws_url = ws_data.get('selenium', ws_data.get('puppeteer'))
            
            if not ws_url.startswith('http'):
                ws_url = f"http://{ws_url}"
            
            # 连接到浏览器
            self.browser = await self.playwright.chromium.connect_over_cdp(ws_url)
            
            # 获取或创建上下文
            contexts = self.browser.contexts
            if contexts:
                self.context = contexts[0]
            else:
                self.context = await self.browser.new_context()
            
            # 获取或创建页面
            pages = self.context.pages
            if pages:
                self.page = pages[0]
            else:
                self.page = await self.context.new_page()
            
            self.is_connected = True
            logger.info(f"已连接到Adspower指纹浏览器: {self.ads_id}")
            return True
            
        except Exception as e:
            logger.error(f"连接指纹浏览器失败: {str(e)}", exc_info=True)
            return False
    
    async def _launch_browser(self) -> bool:
        """启动普通浏览器"""
        try:
            # 浏览器启动参数
            launch_options = {
                'headless': self.config.get('headless', False),
                'args': self._get_browser_args(),
            }
            
            # 代理配置
            if self.proxy_config:
                launch_options['proxy'] = self.proxy_config
            
            # 启动浏览器
            browser_type = self.config.get('browser_type', 'chromium')
            if browser_type == 'firefox':
                self.browser = await self.playwright.firefox.launch(**launch_options)
            elif browser_type == 'webkit':
                self.browser = await self.playwright.webkit.launch(**launch_options)
            else:
                self.browser = await self.playwright.chromium.launch(**launch_options)
            
            # 创建上下文
            context_options = self._get_context_options()
            self.context = await self.browser.new_context(**context_options)
            
            # 应用反检测脚本
            if self.stealth_config.get('enabled', True):
                await self._apply_stealth_scripts()
            
            # 创建页面
            self.page = await self.context.new_page()
            
            self.is_connected = True
            logger.info(f"已启动{browser_type}浏览器")
            return True
            
        except Exception as e:
            logger.error(f"启动浏览器失败: {str(e)}", exc_info=True)
            return False
    
    def _get_browser_args(self) -> List[str]:
        """获取浏览器启动参数"""
        args = [
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-blink-features=AutomationControlled',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--disable-extensions',
            '--no-first-run',
            '--disable-default-apps',
            '--disable-popup-blocking',
            '--disable-translate',
            '--disable-background-timer-throttling',
            '--disable-renderer-backgrounding',
            '--disable-backgrounding-occluded-windows',
            '--disable-ipc-flooding-protection',
        ]
        
        # 添加自定义参数
        custom_args = self.config.get('browser_args', [])
        args.extend(custom_args)
        
        return args
    
    def _get_context_options(self) -> Dict[str, Any]:
        """获取浏览器上下文选项"""
        options = {
            'viewport': self.config.get('viewport', {'width': 1920, 'height': 1080}),
            'user_agent': self._get_random_user_agent(),
            'locale': self.config.get('locale', 'zh-CN'),
            'timezone_id': self.config.get('timezone', 'Asia/Shanghai'),
        }
        
        # 权限设置
        permissions = self.config.get('permissions', [])
        if permissions:
            options['permissions'] = permissions
        
        # 地理位置
        geolocation = self.config.get('geolocation')
        if geolocation:
            options['geolocation'] = geolocation
        
        return options
    
    def _get_random_user_agent(self) -> str:
        """获取随机User-Agent"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        ]
        
        custom_ua = self.config.get('user_agent')
        if custom_ua:
            return custom_ua
        
        return random.choice(user_agents)
    
    async def _apply_stealth_scripts(self):
        """应用反检测脚本"""
        try:
            # 隐藏webdriver属性
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
            
            # 修改plugins
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
            """)
            
            # 修改languages
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh', 'en'],
                });
            """)
            
            # 修改permissions
            await self.context.add_init_script("""
                const originalQuery = window.navigator.permissions.query;
                return window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """)
            
            logger.debug("反检测脚本已应用")
            
        except Exception as e:
            logger.error(f"应用反检测脚本失败: {str(e)}")
    
    async def get_page(self) -> Optional[Page]:
        """获取当前页面"""
        if not self.is_connected:
            await self.start()
        return self.page
    
    async def new_page(self) -> Optional[Page]:
        """创建新页面"""
        if not self.context:
            return None
        
        try:
            page = await self.context.new_page()
            return page
        except Exception as e:
            logger.error(f"创建新页面失败: {str(e)}")
            return None
    
    async def close_extra_pages(self, keep_first: bool = True):
        """关闭多余页面"""
        if not self.context:
            return
        
        try:
            pages = self.context.pages
            if len(pages) <= 1:
                return
            
            start_index = 1 if keep_first else 0
            for page in pages[start_index:]:
                await page.close()
                logger.debug(f"关闭页面: {page.url}")
                
        except Exception as e:
            logger.error(f"关闭多余页面失败: {str(e)}")
    
    async def wait_for_load(self, page: Optional[Page] = None, timeout: int = 30000):
        """等待页面加载完成"""
        target_page = page or self.page
        if not target_page:
            return
        
        try:
            await target_page.wait_for_load_state('networkidle', timeout=timeout)
        except Exception as e:
            logger.warning(f"等待页面加载超时: {str(e)}")
    
    async def random_delay(self, min_ms: int = 1000, max_ms: int = 3000):
        """随机延迟"""
        delay = random.randint(min_ms, max_ms) / 1000
        await asyncio.sleep(delay)
    
    async def human_like_type(self, selector: str, text: str, page: Optional[Page] = None):
        """人性化输入文本"""
        target_page = page or self.page
        if not target_page:
            return False
        
        try:
            element = await target_page.wait_for_selector(selector, timeout=10000)
            await element.click()
            await self.random_delay(100, 300)
            
            # 清空输入框
            await element.fill('')
            await self.random_delay(100, 200)
            
            # 逐字符输入
            for char in text:
                await element.type(char)
                await asyncio.sleep(random.uniform(0.05, 0.15))
            
            return True
            
        except Exception as e:
            logger.error(f"人性化输入失败: {str(e)}")
            return False
    
    async def human_like_click(self, selector: str, page: Optional[Page] = None):
        """人性化点击"""
        target_page = page or self.page
        if not target_page:
            return False
        
        try:
            element = await target_page.wait_for_selector(selector, timeout=10000)
            
            # 移动到元素
            await element.hover()
            await self.random_delay(100, 300)
            
            # 点击
            await element.click()
            await self.random_delay(200, 500)
            
            return True
            
        except Exception as e:
            logger.error(f"人性化点击失败: {str(e)}")
            return False
    
    async def scroll_page(self, direction: str = 'down', distance: int = 500, page: Optional[Page] = None):
        """滚动页面"""
        target_page = page or self.page
        if not target_page:
            return
        
        try:
            if direction == 'down':
                await target_page.mouse.wheel(0, distance)
            elif direction == 'up':
                await target_page.mouse.wheel(0, -distance)
            
            await self.random_delay(500, 1000)
            
        except Exception as e:
            logger.error(f"滚动页面失败: {str(e)}")
    
    async def take_screenshot(self, path: str, page: Optional[Page] = None) -> bool:
        """截图"""
        target_page = page or self.page
        if not target_page:
            return False
        
        try:
            await target_page.screenshot(path=path, full_page=True)
            logger.info(f"截图已保存: {path}")
            return True
            
        except Exception as e:
            logger.error(f"截图失败: {str(e)}")
            return False
    
    async def get_cookies(self) -> List[Dict]:
        """获取cookies"""
        if not self.context:
            return []
        
        try:
            return await self.context.cookies()
        except Exception as e:
            logger.error(f"获取cookies失败: {str(e)}")
            return []
    
    async def set_cookies(self, cookies: List[Dict]):
        """设置cookies"""
        if not self.context:
            return
        
        try:
            await self.context.add_cookies(cookies)
            logger.debug("Cookies已设置")
        except Exception as e:
            logger.error(f"设置cookies失败: {str(e)}")
    
    async def clear_cookies(self):
        """清除cookies"""
        if not self.context:
            return
        
        try:
            await self.context.clear_cookies()
            logger.debug("Cookies已清除")
        except Exception as e:
            logger.error(f"清除cookies失败: {str(e)}")
    
    async def execute_script(self, script: str, page: Optional[Page] = None) -> Any:
        """执行JavaScript脚本"""
        target_page = page or self.page
        if not target_page:
            return None
        
        try:
            return await target_page.evaluate(script)
        except Exception as e:
            logger.error(f"执行脚本失败: {str(e)}")
            return None
    
    async def wait_for_element(self, selector: str, timeout: int = 10000, page: Optional[Page] = None):
        """等待元素出现"""
        target_page = page or self.page
        if not target_page:
            return None
        
        try:
            return await target_page.wait_for_selector(selector, timeout=timeout)
        except Exception as e:
            logger.error(f"等待元素失败: {selector} - {str(e)}")
            return None
    
    async def close(self):
        """关闭浏览器"""
        try:
            if self.ads_id:
                # 关闭指纹浏览器
                await self._close_fingerprint_browser()
            else:
                # 关闭普通浏览器
                if self.context:
                    await self.context.close()
                if self.browser:
                    await self.browser.close()
            
            if self.playwright:
                await self.playwright.stop()
            
            self.is_connected = False
            logger.info("浏览器已关闭")
            
        except Exception as e:
            logger.error(f"关闭浏览器失败: {str(e)}")
    
    async def _close_fingerprint_browser(self):
        """关闭指纹浏览器"""
        try:
            close_url = f"http://local.adspower.net:50325/api/v1/browser/stop"
            params = {'user_id': self.ads_id}
            
            response = requests.get(close_url, params=params, timeout=10)
            if response.status_code == 200:
                logger.info("指纹浏览器已通过API关闭")
            else:
                logger.warning(f"关闭指纹浏览器API调用失败: HTTP {response.status_code}")
                
        except Exception as e:
            logger.error(f"关闭指纹浏览器失败: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            'connected': self.is_connected,
            'has_browser': self.browser is not None,
            'has_context': self.context is not None,
            'has_page': self.page is not None,
            'ads_id': self.ads_id,
            'page_url': self.page.url if self.page else None,
        }


class PlaywrightManager:
    """Playwright管理器"""
    
    def __init__(self):
        self.instances: Dict[str, PlaywrightUtils] = {}
    
    async def create_instance(self, instance_id: str, config: Optional[Dict] = None) -> PlaywrightUtils:
        """创建Playwright实例"""
        if instance_id in self.instances:
            await self.instances[instance_id].close()
        
        instance = PlaywrightUtils(config)
        self.instances[instance_id] = instance
        
        return instance
    
    def get_instance(self, instance_id: str) -> Optional[PlaywrightUtils]:
        """获取Playwright实例"""
        return self.instances.get(instance_id)
    
    async def close_instance(self, instance_id: str):
        """关闭Playwright实例"""
        if instance_id in self.instances:
            await self.instances[instance_id].close()
            del self.instances[instance_id]
    
    async def close_all(self):
        """关闭所有实例"""
        for instance_id in list(self.instances.keys()):
            await self.close_instance(instance_id)
    
    def list_instances(self) -> List[str]:
        """列出所有实例ID"""
        return list(self.instances.keys())
    
    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """检查所有实例的健康状态"""
        status = {}
        for instance_id, instance in self.instances.items():
            status[instance_id] = await instance.health_check()
        return status


# 全局Playwright管理器实例
playwright_manager = PlaywrightManager() 