# BrowserUse Agent Helper

让自动化测试 Agent 更好地代理你的浏览器 - CDP + Playwright + BrowserUse 集成示例

## 项目简介

本项目展示了如何通过 Chrome DevTools Protocol (CDP) 连接 Playwright 和 BrowserUse，实现高级浏览器自动化功能：

- **统一浏览器实例**：Playwright 和 BrowserUse 共享同一个 Chrome 实例
- **网络监控**：捕获并分析 AJAX/Fetch 请求和响应数据
- **Tab 管理**：智能标签页管理，支持多标签页操作
- **自定义工具**：为 BrowserUse Agent 提供扩展功能

## 核心特性

### 1. CDP 共享机制

通过 CDP 端口，让 Playwright 和 BrowserUse 连接到同一个 Chrome 实例：

```python
from browser_manager import get_or_create_browser

# 创建浏览器管理器
browser_manager = await get_or_create_browser(headless=False)

# Playwright 和 BrowserUse 自动连接到同一个浏览器
playwright_page = browser_manager.playwright_page
browseruse_session = browser_manager.browser_use_session
```

### 2. 网络数据捕获

自动捕获和解析网络请求：

```python
# 捕获包含特定关键词的 API 响应数据
@tools.action(description="获取网络请求数据")
async def get_network_data(keyword: str) -> ActionResult:
    captured_data = browser_manager.get_captured_data(keyword)
    return ActionResult(extracted_content=json.dumps(captured_data))
```

### 3. Tab 管理工具

提供智能标签页管理：

```python
# 标记初始标签页
@tools.action(description="标记当前页面为初始页")
async def mark_initial_tab() -> ActionResult:
    ...

# 在新标签页打开链接
@tools.action(description="在新标签页中打开链接")
async def open_in_new_tab(url: str) -> ActionResult:
    ...

# 关闭其他标签页并返回初始页
@tools.action(description="关闭所有其他标签页并返回初始页")
async def close_tabs_and_return() -> ActionResult:
    ...
```

## 快速开始

### 安装依赖

```bash
uv sync
```

### 配置环境变量

复制 `.env.example` 到 `.env` 并配置：

```bash
cp .env.example .env
```

编辑 `.env`：

```env
# Gemini API 配置（默认）
GEMINI_API_KEY=your_gemini_api_key
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta
GEMINI_MODEL=gemini-2.0-flash-exp
```

### 运行测试

**测试 1：网络数据捕获**

```bash
# 终端 1：启动 API 服务器
uv run python tests/api_server.py

# 终端 2：运行测试
uv run python tests/test_1_improved.py
```

**测试 2：Tab 管理**

```bash
uv run python tests/test_2_simple.py
```

**测试 3：DOM 可见性检查**

```bash
uv run python tests/test_3.py
```

## 项目结构

```
browseruse-agent-helper/
├── src/
│   ├── __init__.py              # 包入口
│   ├── browser_manager.py       # 浏览器管理器（CDP集成）
│   └── tools.py                 # BrowserUse 自定义工具
├── tests/
│   ├── test_1_improved.py       # 网络数据捕获测试
│   ├── test_2_simple.py         # Tab 管理测试
│   ├── test_3.py                # DOM 可见性测试
│   ├── test_page.html           # 测试页面
│   └── api_server.py            # 测试 API 服务器
├── .env.example                 # 环境变量示例
├── pyproject.toml               # 项目配置
└── README.md                    # 本文件
```

## 技术架构

### 浏览器管理器 (`SimpleBrowserManager`)

核心组件，管理 Chrome 实例并提供 CDP 集成：

```python
class SimpleBrowserManager:
    def __init__(self, cdp_port: int = 9222, headless: bool = False):
        # Chrome 进程
        self.chrome_process = None

        # Playwright 连接
        self.playwright: Playwright = None
        self.browser: Browser = None
        self.playwright_page: Page = None

        # BrowserUse 连接
        self.browser_use_session: BrowserUseSession = None

        # 网络事件捕获
        self.network_events = []
```

主要功能：

1. **启动 Chrome**：使用指定 CDP 端口启动 Chrome
2. **连接 Playwright**：通过 CDP 连接 Playwright
3. **连接 BrowserUse**：通过 CDP 连接 BrowserUse
4. **网络监控**：监听并捕获网络请求/响应
5. **数据提取**：从捕获的网络数据中提取特定内容

### 自定义工具 (`tools.py`)

为 BrowserUse Agent 提供扩展功能：

- `get_network_data(keyword)`: 获取包含关键词的网络数据
- `is_dom_visible(dom_id)`: 检查 DOM 元素可见性
- `mark_initial_tab()`: 标记初始标签页
- `open_in_new_tab(url)`: 在新标签页打开链接
- `close_tabs_and_return()`: 关闭其他标签页并返回

## 测试说明

### 测试 1：网络数据捕获

演示如何捕获 AJAX 请求并提取 JSON 数据：

1. 启动本地 API 服务器（`api_server.py`）
2. Agent 访问测试页面并触发 API 调用
3. 使用 `get_network_data` 工具捕获响应数据
4. 验证捕获的 JSON 数据

### 测试 2：Tab 管理

演示智能标签页管理：

1. 访问初始页面并标记
2. 在新标签页打开多个链接
3. 关闭所有新标签页
4. 返回初始标签页

### 测试 3：DOM 可见性

演示检查 DOM 元素是否在视口内：

1. 访问测试页面
2. 检查页面顶部元素（可见）
3. 检查页面底部元素（不可见）
4. 滚动到底部后再次检查（可见）

## 最佳实践

### 1. 工具定义

使用清晰的描述和类型注解：

```python
@tools.action(
    description="获取包含指定关键词的网络请求数据"
)
async def get_network_data(keyword: str) -> ActionResult:
    """
    从捕获的网络事件中查找包含关键词的数据

    Args:
        keyword: 搜索关键词（URL 中包含）

    Returns:
        ActionResult with extracted JSON data
    """
    ...
```

### 2. 错误处理

始终处理可能的错误情况：

```python
if not _current_browser_manager:
    return ActionResult(
        error="浏览器管理器未设置",
        metadata={'success': False}
    )
```

### 3. 状态管理

使用全局变量管理共享状态：

```python
# 全局浏览器管理器单例
_browser_manager: Optional[SimpleBrowserManager] = None

def set_browser_manager(manager: SimpleBrowserManager):
    """设置全局浏览器管理器"""
    global _current_browser_manager
    _current_browser_manager = manager
```

### 4. 异步操作

所有工具函数都应该是异步的：

```python
async def custom_tool() -> ActionResult:
    # 异步操作
    await some_async_operation()
    return ActionResult(...)
```

## 常见问题

### Q: 为什么需要 CDP？

A: CDP 允许多个客户端（Playwright 和 BrowserUse）连接到同一个浏览器实例，共享浏览器状态（cookies、session 等）。

### Q: 如何捕获更复杂的网络数据？

A: 可以在 `SimpleBrowserManager` 中扩展网络事件监听器，添加更多的过滤和处理逻辑。

### Q: 工具调用失败怎么办？

A: 检查：
1. 浏览器管理器是否正确设置（`set_browser_manager`）
2. 工具描述是否清晰
3. Agent 任务指令是否明确

### Q: 如何添加新工具？

A: 使用 `@tools.action` 装饰器：

```python
@tools.action(description="工具描述")
async def my_custom_tool(param: str) -> ActionResult:
    # 实现逻辑
    return ActionResult(extracted_content="结果")
```

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License
