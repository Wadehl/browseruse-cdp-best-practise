"""
浏览器管理器 - 通过 CDP 集成 Playwright 和 BrowserUse

核心特性：
1. 统一浏览器实例 - Playwright 和 BrowserUse 共享同一个 Chrome
2. 网络监控 - 捕获并分析 AJAX/Fetch 请求
3. 数据提取 - 从网络响应中提取 JSON 数据
"""

import asyncio
import json
import subprocess
import time
import os
import pathlib
import tempfile
import aiohttp
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from playwright.async_api import async_playwright, Playwright, Browser, Page
from browser_use import BrowserSession


@dataclass
class NetworkEvent:
    """网络事件数据类"""
    event_type: str  # 'request' or 'response'
    url: str
    method: Optional[str] = None
    status: Optional[int] = None
    headers: Optional[Dict] = None
    body: Optional[Any] = None
    timestamp: float = 0.0


class SimpleBrowserManager:
    """
    简化的浏览器管理器

    通过 CDP 连接 Playwright 和 BrowserUse 到同一个 Chrome 实例
    """

    def __init__(self, cdp_port: int = 9222, headless: bool = False):
        """
        初始化浏览器管理器

        Args:
            cdp_port: CDP 端口号
            headless: 是否无头模式
        """
        self.cdp_port = cdp_port
        self.headless = headless

        # Chrome 进程
        self.chrome_process: Optional[subprocess.Popen] = None

        # Playwright 相关
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.playwright_page: Optional[Page] = None

        # BrowserUse 相关
        self.browser_use_session: Optional[BrowserSession] = None

        # 网络事件存储
        self.network_events: List[NetworkEvent] = []
        self._captured_data: Dict[str, Any] = {}

    async def start(self):
        """启动浏览器并建立连接"""
        # 1. 启动 Chrome
        await self._start_chrome()

        # 2. 连接 Playwright
        await self._connect_playwright()

        # 3. 连接 BrowserUse
        await self._connect_browseruse()

        # 4. 设置网络监听
        await self._setup_network_listeners()

        print("✅ 浏览器管理器启动完成")

    async def _start_chrome(self):
        """启动 Chrome 浏览器"""
        print(f"🚀 启动 Chrome (CDP端口: {self.cdp_port}, Headless: {self.headless})")

        # 创建临时用户数据目录
        user_data_dir = tempfile.mkdtemp(prefix='chrome_cdp_')

        # 查找 Chrome 可执行文件
        # 首先尝试 Playwright 安装的 Chromium
        playwright_chromium_dir = pathlib.Path.home() / '.cache' / 'ms-playwright'
        playwright_chromium = None
        if playwright_chromium_dir.exists():
            # 查找最新的 chromium 版本目录
            chromium_dirs = sorted(playwright_chromium_dir.glob('chromium-*'), reverse=True)
            if chromium_dirs:
                # Linux 路径
                chromium_exe = chromium_dirs[0] / 'chrome-linux' / 'chrome'
                if chromium_exe.exists():
                    playwright_chromium = str(chromium_exe)
                else:
                    # macOS 路径
                    chromium_exe = chromium_dirs[0] / 'chrome-mac' / 'Chromium.app' / 'Contents' / 'MacOS' / 'Chromium'
                    if chromium_exe.exists():
                        playwright_chromium = str(chromium_exe)

        chrome_paths = [
            playwright_chromium,  # Playwright Chromium (优先使用)
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',  # macOS
            '/usr/bin/google-chrome',  # Linux
            '/usr/bin/chromium-browser',  # Linux Chromium
            'chrome',  # Windows/PATH
            'chromium',  # Generic
        ]
        # 过滤掉 None 值
        chrome_paths = [p for p in chrome_paths if p is not None]

        chrome_exe = None
        for path in chrome_paths:
            if os.path.exists(path) or path in ['chrome', 'chromium']:
                try:
                    # 测试可执行文件是否有效
                    test_proc = await asyncio.create_subprocess_exec(
                        path, '--version',
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    await test_proc.wait()
                    chrome_exe = path
                    print(f"✅ 找到 Chrome: {chrome_exe}")
                    break
                except Exception:
                    continue

        if not chrome_exe:
            raise RuntimeError('❌ Chrome 未找到,请安装 Chrome 或 Chromium')

        # Chrome 启动参数
        cmd = [
            chrome_exe,
            f'--remote-debugging-port={self.cdp_port}',
            f'--user-data-dir={user_data_dir}',
            '--no-first-run',
            '--no-default-browser-check',
            '--disable-extensions',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--no-sandbox',
        ]

        if self.headless:
            cmd.append('--headless=new')

        # 启动 Chrome 进程
        self.chrome_process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # 等待 CDP 就绪
        await self._wait_for_cdp()
        print(f"✅ Chrome CDP 已就绪: http://localhost:{self.cdp_port}")

    async def _wait_for_cdp(self, max_attempts: int = 20):
        """等待 CDP 端口就绪"""
        cdp_url = f'http://localhost:{self.cdp_port}'

        for _ in range(max_attempts):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f'{cdp_url}/json/version',
                        timeout=aiohttp.ClientTimeout(total=1)
                    ) as response:
                        if response.status == 200:
                            return
            except Exception:
                pass
            await asyncio.sleep(1)

        # CDP 未就绪，终止进程
        if self.chrome_process:
            try:
                self.chrome_process.terminate()
            except ProcessLookupError:
                pass

        raise RuntimeError(f"CDP 端口 {self.cdp_port} 未就绪")

    async def _connect_playwright(self):
        """连接 Playwright 到 CDP"""
        print("🎭 连接 Playwright 到 CDP...")

        self.playwright = await async_playwright().start()

        # 通过 CDP 连接到已有浏览器
        self.browser = await self.playwright.chromium.connect_over_cdp(
            f'http://localhost:{self.cdp_port}'
        )

        # 获取默认上下文和页面
        contexts = self.browser.contexts
        if contexts:
            pages = contexts[0].pages
            if pages:
                self.playwright_page = pages[0]
            else:
                self.playwright_page = await contexts[0].new_page()
        else:
            context = await self.browser.new_context()
            self.playwright_page = await context.new_page()

        print("✅ Playwright 已连接")

    async def _connect_browseruse(self):
        """连接 BrowserUse 到 CDP"""
        print("🤖 连接 BrowserUse 到 CDP...")

        # 创建 BrowserSession
        cdp_url = f'http://localhost:{self.cdp_port}'
        self.browser_use_session = BrowserSession(cdp_url=cdp_url, keep_alive=True)

        # 启动 BrowserSession
        await self.browser_use_session.start()

        # 获取 Playwright page 的 CDP target_id 并切换到该页面
        if self.playwright_page:
            # 获取 target_id
            target_id = await self._get_target_id()
            if target_id:
                # 切换 BrowserSession 的焦点到 Playwright 页面
                from browser_use.browser.events import SwitchTabEvent
                await self.browser_use_session.event_bus.dispatch(
                    SwitchTabEvent(target_id=target_id)
                )
                print(f"✅ 已将 BrowserSession 焦点切换到 Playwright 页面")
            else:
                print("⚠️  警告: 无法找到 Playwright Page 对应的 target_id")

        print("✅ BrowserUse 已连接")

    async def _get_target_id(self) -> Optional[str]:
        """获取 Playwright Page 对应的 CDP target_id"""
        if not self.playwright_page:
            return None

        try:
            # 使用内部 CDP session 获取 target_id
            cdp_session = await self.playwright_page.context.new_cdp_session(self.playwright_page)
            target_info = await cdp_session.send('Target.getTargetInfo')
            target_id = target_info['targetInfo']['targetId']
            await cdp_session.detach()
            return target_id
        except Exception:
            return None

    async def _setup_network_listeners(self):
        """设置网络事件监听器"""
        if not self.playwright_page:
            return

        # 监听请求
        self.playwright_page.on('request', self._on_request)

        # 监听响应
        self.playwright_page.on('response', self._on_response)

    def _on_request(self, request):
        """处理网络请求事件"""
        event = NetworkEvent(
            event_type='request',
            url=request.url,
            method=request.method,
            headers=request.headers,
            timestamp=time.time()
        )
        self.network_events.append(event)

    def _on_response(self, response):
        """处理网络响应事件"""
        event = NetworkEvent(
            event_type='response',
            url=response.url,
            status=response.status,
            headers=response.headers,
            timestamp=time.time()
        )

        # 异步获取响应体
        asyncio.create_task(self._process_response(response, event))

    async def _process_response(self, response, event: NetworkEvent):
        """处理响应数据"""
        try:
            # 只处理 JSON 响应
            content_type = response.headers.get('content-type', '')
            if 'application/json' in content_type:
                body = await response.text()
                try:
                    event.body = json.loads(body)

                    # 尝试捕获特定的数据
                    for keyword in ['user', 'product', 'api']:
                        if keyword in response.url.lower():
                            self._captured_data[keyword] = {
                                'data': event.body,
                                'url': response.url,
                                'timestamp': event.timestamp,
                                'type': 'json'
                            }
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            print(f"处理响应失败: {e}")
        finally:
            self.network_events.append(event)

    def get_captured_data(self, keyword: str) -> Optional[Dict[str, Any]]:
        """
        获取捕获的数据

        Args:
            keyword: 关键词（在 URL 中搜索）

        Returns:
            捕获的数据字典，如果未找到则返回 None
        """
        # 1. 先从 _captured_data 中查找
        if keyword.lower() in self._captured_data:
            return self._captured_data[keyword.lower()]

        # 2. 从 network_events 中查找
        for event in reversed(self.network_events):
            if event.event_type == 'response' and keyword.lower() in event.url.lower():
                if event.body:
                    return {
                        'data': event.body,
                        'url': event.url,
                        'timestamp': event.timestamp,
                        'type': 'json'
                    }

        return None

    async def stop(self):
        """停止浏览器和所有连接"""
        print("🛑 停止浏览器...")

        # 关闭 BrowserUse
        if self.browser_use_session:
            try:
                await self.browser_use_session.close()
            except Exception:
                pass

        # 关闭 Playwright
        if self.browser:
            try:
                await self.browser.close()
            except Exception:
                pass

        if self.playwright:
            try:
                await self.playwright.stop()
            except Exception:
                pass

        # 终止 Chrome 进程
        if self.chrome_process:
            try:
                self.chrome_process.terminate()
                await asyncio.wait_for(self.chrome_process.wait(), 5)
            except asyncio.TimeoutError:
                try:
                    self.chrome_process.kill()
                    await self.chrome_process.wait()
                except Exception:
                    pass
            except Exception:
                pass

        print("✅ 浏览器已停止")


# 全局浏览器管理器单例
_browser_manager: Optional[SimpleBrowserManager] = None


async def get_or_create_browser(
    headless: bool = None,
    force_new: bool = False
) -> SimpleBrowserManager:
    """
    获取或创建浏览器管理器

    Args:
        headless: 是否无头模式（None 表示使用默认值）
        force_new: 是否强制创建新实例

    Returns:
        SimpleBrowserManager 实例
    """
    global _browser_manager

    # 如果强制创建新实例，先关闭旧的
    if force_new and _browser_manager is not None:
        try:
            await _browser_manager.stop()
        except Exception:
            pass
        _browser_manager = None

    # 如果还没有实例，创建新的
    if _browser_manager is None:
        if headless is None:
            headless = False

        _browser_manager = SimpleBrowserManager(headless=headless)
        await _browser_manager.start()

    return _browser_manager
