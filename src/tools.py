"""
BrowserUse 自定义工具

提供扩展功能：
1. 网络数据捕获
2. DOM 可见性检查
3. Tab 管理
"""

import json
from typing import Optional

from browser_use import Tools, ActionResult

# 创建工具实例
tools = Tools()

# 全局浏览器管理器引用
_current_browser_manager = None


def set_browser_manager(manager):
    """设置全局浏览器管理器"""
    global _current_browser_manager
    _current_browser_manager = manager


@tools.action(
    description="获取包含指定关键词的网络请求数据，从捕获的 AJAX/Fetch 响应中提取 JSON 数据"
)
async def get_network_data(keyword: str) -> ActionResult:
    """
    从捕获的网络事件中查找包含关键词的数据

    Args:
        keyword: 搜索关键词（URL 中包含）

    Returns:
        ActionResult with extracted JSON data
    """
    if not _current_browser_manager:
        return ActionResult(
            error="浏览器管理器未设置",
            extracted_content="请先设置浏览器管理器"
        )

    # 获取捕获的数据
    captured_data = _current_browser_manager.get_captured_data(keyword)

    if captured_data:
        result_text = json.dumps(captured_data['data'], ensure_ascii=False, indent=2)
        return ActionResult(
            extracted_content=result_text,
            metadata={
                'type': captured_data['type'],
                'timestamp': captured_data['timestamp'],
                'keyword': keyword
            }
        )
    else:
        # 返回最近的网络事件供调试
        recent_events = _current_browser_manager.network_events[-10:]
        urls = [e.url for e in recent_events if hasattr(e, 'event_type') and e.event_type == 'response']

        return ActionResult(
            extracted_content=f"未找到包含 '{keyword}' 的数据\n\n最近的请求:\n" + "\n".join(urls),
            metadata={'found': False, 'keyword': keyword}
        )


@tools.action(
    description="检查DOM元素是否在可视范围内"
)
async def is_dom_visible(dom_id: str) -> ActionResult:
    """
    检查指定 DOM 元素是否可见

    Args:
        dom_id: DOM 元素的 ID

    Returns:
        ActionResult with visibility status
    """
    if not _current_browser_manager:
        return ActionResult(
            error="浏览器管理器未设置",
            metadata={'success': False}
        )

    playwright_page = _current_browser_manager.playwright_page
    if not playwright_page:
        return ActionResult(
            error="Playwright 未连接",
            metadata={'success': False}
        )

    try:
        # 检查元素是否存在
        element = await playwright_page.query_selector(f"#{dom_id}")
        if not element:
            return ActionResult(
                extracted_content=f"元素 #{dom_id} 不存在",
                metadata={'exists': False, 'visible': False}
            )

        # 检查元素是否在视口内
        is_visible = await element.is_visible()

        # 获取元素位置信息
        bounding_box = await element.bounding_box()

        return ActionResult(
            extracted_content=f"元素 #{dom_id} {'可见' if is_visible else '不可见'}",
            metadata={
                'exists': True,
                'visible': is_visible,
                'position': bounding_box
            }
        )

    except Exception as e:
        return ActionResult(
            error=f"检查失败: {str(e)}",
            metadata={'success': False}
        )


# Tab 管理相关工具

@tools.action(
    description="标记当前页面为初始Tab，用于后续返回"
)
async def mark_initial_tab() -> ActionResult:
    """
    标记当前页面为初始 Tab

    Returns:
        ActionResult with marked page info
    """
    if not _current_browser_manager:
        return ActionResult(
            error="浏览器管理器未设置",
            metadata={'success': False}
        )

    playwright_page = _current_browser_manager.playwright_page
    if not playwright_page:
        return ActionResult(
            error="Playwright 未连接",
            metadata={'success': False}
        )

    # 保存初始页面 URL 到全局变量
    initial_url = playwright_page.url
    _current_browser_manager._initial_tab_url = initial_url

    return ActionResult(
        extracted_content=f"已标记初始页面: {initial_url}",
        metadata={
            'initial_url': initial_url,
            'success': True
        }
    )


@tools.action(
    description="在新标签页中打开链接"
)
async def open_in_new_tab(url: str) -> ActionResult:
    """
    使用 JavaScript 在新标签页中打开链接

    Args:
        url: 要打开的 URL

    Returns:
        ActionResult with opened tab info
    """
    if not _current_browser_manager:
        return ActionResult(
            error="浏览器管理器未设置",
            metadata={'success': False}
        )

    playwright_page = _current_browser_manager.playwright_page
    if not playwright_page:
        return ActionResult(
            error="Playwright 未连接",
            metadata={'success': False}
        )

    try:
        # 使用 JavaScript 打开新标签页
        await playwright_page.evaluate(f"window.open('{url}', '_blank')")

        # 等待新标签页出现
        await playwright_page.wait_for_timeout(1000)

        # 获取所有页面
        context = playwright_page.context
        pages = context.pages

        return ActionResult(
            extracted_content=f"在新标签页中打开了: {url}",
            metadata={
                'url': url,
                'total_tabs': len(pages),
                'success': True
            }
        )
    except Exception as e:
        return ActionResult(error=f"打开新标签页失败: {str(e)}")


@tools.action(
    description="关闭所有其他标签页并返回初始Tab"
)
async def close_tabs_and_return() -> ActionResult:
    """
    关闭所有其他标签页并返回初始标签页

    Returns:
        ActionResult with operation status
    """
    if not _current_browser_manager:
        return ActionResult(
            error="浏览器管理器未设置",
            metadata={'success': False}
        )

    playwright_page = _current_browser_manager.playwright_page
    if not playwright_page:
        return ActionResult(
            error="Playwright 未连接",
            metadata={'success': False}
        )

    try:
        # 获取初始 URL
        initial_url = getattr(_current_browser_manager, '_initial_tab_url', None)
        if not initial_url:
            return ActionResult(
                error="未找到初始Tab标记，请先调用 mark_initial_tab",
                metadata={'success': False}
            )

        # 获取所有页面
        context = playwright_page.context
        pages = context.pages

        # 找到初始页面
        initial_page = None
        for page in pages:
            if page.url == initial_url:
                initial_page = page
                break

        # 如果找不到初始页面，使用第一个页面
        if not initial_page and pages:
            initial_page = pages[0]

        # 关闭其他页面
        closed_count = 0
        for page in pages:
            if page != initial_page:
                await page.close()
                closed_count += 1

        # 切换到初始页面
        if initial_page:
            await initial_page.bring_to_front()
            # 如果当前 URL 不是初始 URL，导航回去
            if initial_page.url != initial_url:
                await initial_page.goto(initial_url)

        return ActionResult(
            extracted_content=f"已关闭 {closed_count} 个 Tab，返回初始页面",
            metadata={
                'closed_count': closed_count,
                'success': True
            }
        )

    except Exception as e:
        return ActionResult(error=f"关闭Tab失败: {str(e)}")
