"""
测试 2 简化版：验证 Tab 管理工具

直接测试 Tab 管理工具的基本功能
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from src import get_or_create_browser, tools, set_browser_manager
from browser_use import Agent
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(Path(__file__).parent.parent / '.env')


def get_test_llm():
    """获取测试用的 LLM"""
    if os.getenv("GEMINI_API_KEY"):
        from browser_use import ChatGoogle
        return ChatGoogle(
            model=os.getenv("GEMINI_MODEL", "gemini-3-flash"),
            api_key=os.getenv("GEMINI_API_KEY"),
            http_options={"base_url": os.getenv("GEMINI_BASE_URL")}
        )
    else:
        from browser_use import ChatOpenAI
        return ChatOpenAI(
            model="gpt-4",
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )


async def test_simple_tab_management():
    print("🧪 测试 2 简化版：验证 Tab 管理工具\n")

    # 初始化浏览器（强制新实例）
    browser_manager = await get_or_create_browser(headless=False, force_new=True)

    # 设置 browser_manager 到工具中
    set_browser_manager(browser_manager)

    # 简单的测试任务
    task = """
    请按照以下步骤测试 Tab 管理功能：

    1. 访问 https://example.com

    2. 使用 mark_initial_tab 工具来标记当前页面

    3. 使用 open_in_new_tab 工具打开这些 URL：
       - https://www.python.org
       - https://www.javascript.com
       - https://www.typescriptlang.org

    4. 等待 2 秒

    5. 使用 close_tabs_and_return 工具关闭所有标签页并返回初始页面

    请报告每个步骤的执行结果。
    """

    # 创建 Agent
    agent = Agent(
        task=task,
        browser_session=browser_manager.browser_use_session,
        llm=get_test_llm(),
        tools=tools
    )

    # 执行测试任务
    result = await agent.run()

    print("\n📊 Agent 执行结果：")
    print(result)

    # 验证最终状态
    page = browser_manager.playwright_page
    if page:
        # 获取所有打开的页面
        context = page.context
        pages = context.pages

        print(f"\n✅ 当前打开的标签页数: {len(pages)}")
        for i, p in enumerate(pages):
            try:
                print(f"  Tab {i+1}: {p.url[:50]}...")
            except:
                print(f"  Tab {i+1}: [无法获取URL]")

        final_url = page.url
        print(f"\n✅ 最终页面 URL: {final_url}")
        print(f"是否在 example.com: {'example.com' in final_url}")

    # 清理
    await asyncio.sleep(3)
    await browser_manager.stop()


if __name__ == "__main__":
    asyncio.run(test_simple_tab_management())