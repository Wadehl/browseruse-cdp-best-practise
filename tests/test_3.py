"""
测试 3：DOM 可见性检查

验证 is_dom_visible 工具能够检测元素是否在可视范围内
会自动启动和停止 API 服务器
"""

import asyncio
import os
import sys
import subprocess
import time
import socket
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from src import get_or_create_browser, tools, set_browser_manager
from browser_use import Agent
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(Path(__file__).parent.parent / '.env')

# API 服务器配置
API_SERVER_PORT = 8890
api_server_process = None


def get_test_llm():
    """获取测试用的 LLM"""
    if os.getenv("GEMINI_API_KEY"):
        from browser_use import ChatGoogle
        return ChatGoogle(
            model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp"),
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


def is_port_in_use(port):
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def start_api_server():
    """启动 API 服务器"""
    global api_server_process

    # 检查端口是否已被占用
    if is_port_in_use(API_SERVER_PORT):
        print(f"⚠️  端口 {API_SERVER_PORT} 已被占用，假设 API 服务器已在运行")
        return

    print(f"🚀 启动 API 服务器 (端口: {API_SERVER_PORT})...")

    # 启动 API 服务器进程
    api_server_path = Path(__file__).parent / 'api_server.py'
    api_server_process = subprocess.Popen(
        [sys.executable, str(api_server_path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # 等待服务器启动
    max_attempts = 10
    for i in range(max_attempts):
        if is_port_in_use(API_SERVER_PORT):
            print(f"✅ API 服务器已启动")
            time.sleep(0.5)  # 额外等待以确保完全就绪
            return

        time.sleep(0.5)

    print(f"❌ API 服务器启动失败")
    if api_server_process:
        api_server_process.terminate()
        api_server_process = None


def stop_api_server():
    """停止 API 服务器"""
    global api_server_process

    if api_server_process:
        print("🛑 停止 API 服务器...")
        api_server_process.terminate()
        try:
            api_server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            api_server_process.kill()
        print("✅ API 服务器已停止")
        api_server_process = None


async def test_dom_visibility():
    print("🧪 测试 3：DOM 可见性检查\n")

    # 启动 API 服务器
    start_api_server()

    try:
        # 初始化浏览器（强制新实例）
        browser_manager = await get_or_create_browser(headless=False, force_new=True)

        # 设置 browser_manager 到工具中
        set_browser_manager(browser_manager)

        # 定义测试任务
        task = """
        执行以下 DOM 可见性测试：

        1. 访问 http://localhost:8890/test_page.html

        2. 使用 is_dom_visible 工具检查 ID 为 "top-element" 的元素（应该可见）

        3. 使用 is_dom_visible 工具检查 ID 为 "bottom-element" 的元素（可能不可见）

        4. 如果 bottom-element 不可见，滚动到页面底部

        5. 再次使用 is_dom_visible 工具检查 "bottom-element"（现在应该可见）

        请报告每一步的执行结果和可见性状态。
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

        # 清理
        await asyncio.sleep(3)
        await browser_manager.stop()

    finally:
        # 确保停止 API 服务器
        stop_api_server()


if __name__ == "__main__":
    asyncio.run(test_dom_visibility())